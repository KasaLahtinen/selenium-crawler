import os
import time

from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import types
from loguru import logger
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

app = FastAPI(title="Selenium AI Crawler")
client = genai.Client()


class ResolveRequest(BaseModel):
    url: str


def get_safety_settings():
    return [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.OFF,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.OFF,
        ),
    ]


@app.post("/resolve")
def resolve_url(req: ResolveRequest):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # Spoof a real, modern browser to avoid "deprecated browser" walls
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = None
    try:
        driver = webdriver.Remote(
            command_executor=os.environ.get("SELENIUM_URL", "http://localhost:4444/wd/hub"), options=options
        )
        driver.get(req.url)
        time.sleep(3)  # Give initial JS time to load

        # 1. AI Cookie Bypass Strategy
        # Extract only interactive elements to prevent the prompt from truncating before the button appears
        clickable_html = driver.execute_script("""
            let elements = document.querySelectorAll('button, a, input[type="submit"], input[type="button"]');
            let result = [];
            elements.forEach(el => {
                let text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim();
                if (text.length > 0) {
                    let clone = el.cloneNode(false);
                    clone.innerText = text;
                    result.push(clone.outerHTML);
                }
            });
            return result.join('\\n');
        """)

        prompt_btn = (
            "Analyze these clickable HTML elements and find the CSS selector for the primary 'Accept All', "
            "'Agree', or 'Accept Cookies' button (it may be in a local language, e.g., 'Hyväksy kaikki'). "
            "Return ONLY the raw CSS selector string (e.g., 'button.some-class' or 'button[aria-label=\"Accept\"]'). "
            f"If none exists, return 'NONE'.\n\n{clickable_html[:30000]}"
        )

        btn_response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=[prompt_btn],
            config=types.GenerateContentConfig(safety_settings=get_safety_settings()),
        )

        selector = btn_response.text.strip().replace("`", "")
        logger.debug(f"AI suggested cookie button selector: {selector}")
        if selector and selector != "NONE":
            try:
                element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                # Use JavaScript click to bypass transparent overlays or animations
                driver.execute_script("arguments[0].click();", element)
                logger.debug(f"Clicked {selector} via JS. Waiting for redirect and SPA load...")
                time.sleep(5)  # Wait for cookie wall to redirect and heavy SPAs to load
            except Exception as e:
                logger.error(f"Failed to click cookie button using selector {selector}: {e}")

        # 2. Extract final rendered content and summarize
        title = driver.title
        page_text = driver.execute_script("return document.body.innerText;")

        prompt_summary = (
            "Analyze this webpage content. Provide a strictly formatted summary with the original title followed by 1-3 bulleted facts.\n"
            "If the content appears to be a cookie consent warning, captcha, or 'Before you continue' page that we failed to bypass, "
            "do NOT summarize it. Instead, reply EXACTLY with: 'Error: Could not bypass consent wall.'\n\n"
            f"Title: {title}\nContent:\n{page_text[:15000]}"
        )
        summary_response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=[prompt_summary],
            config=types.GenerateContentConfig(safety_settings=get_safety_settings()),
        )

        return {"summary": summary_response.text.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if driver:
            driver.quit()
