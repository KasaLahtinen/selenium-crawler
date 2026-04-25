# AI-Powered URL Resolver Integration

This plan outlines the architecture and steps to build the `selenium-crawler` microservice and integrate it seamlessly with your existing `Gemini-IRC-bot` using asynchronous design patterns.

## Goal

Enhance the IRC bot to resolve difficult URLs (JavaScript heavy, cookie banners) by offloading the heavy lifting to a standalone, asynchronous Python microservice that uses a Podman-based Selenium Grid and the Google Gemini AI. The IRC bot will be updated to handle this concurrently so that it never blocks the chat channels.

## Design Decisions (from User Feedback)

1. **Infrastructure**: We will use **Podman and Pods** instead of Docker to host the Selenium Grid and FastAPI backend.
2. **AI Cookie Bypass Strategy**: We will rely purely on DOM analysis. Gemini will analyze the raw HTML to locate an "Accept" clickable element. No screenshots will be taken (especially for image/multimedia URLs).
3. **AI Summarization Prompt**: The summary format will be strictly text: the original title, followed by a 1-3 bulleted facts list on a single line. Nothing fancy.
4. **Fallback Logic**: The trigger for falling back to the Selenium service will be embedded in `bot.py`'s `_get_url_info` function. If the fast crawler fails to find a title/description or detects a cookie wall, it triggers the heavy crawler.

## Proposed Changes

### Component 1: `selenium-crawler` Microservice

#### [NEW] `podman-compose.yml` (or Bash script for Podman Pod)
- Defines a Podman Pod containing the Selenium standalone image (or hub+nodes if scaling is needed) and the FastAPI service.

#### [NEW] `requirements.txt`
- `fastapi`, `uvicorn`, `selenium`, `google-genai`, `python-dotenv`.

#### [NEW] `main.py` (FastAPI App)
- Creates an endpoint `POST /resolve`.
- **Logic**: 
  1. Requests a browser session from the Selenium instance in the pod.
  2. Navigates to the given URL.
  3. Extracts the DOM, sends it to Gemini to locate the CSS selector for any "Accept Cookies" button, and clicks it if found.
  4. Extracts the rendered page text.
  5. Uses Gemini to generate a summary matching the exact prompt constraints (Title + 1-3 facts).
  6. Clears cookies/cache, closes the browser session, and returns the summary.

### Component 2: `Gemini-IRC-bot` 

#### [MODIFY] `bot.py`
- Import `concurrent.futures.ThreadPoolExecutor`.
- Initialize `self.url_pool = ThreadPoolExecutor(max_workers=5)` in `__init__`.
- Update `_handle_url` to submit the URL processing task to `self.url_pool` instead of running it synchronously.
- Update `_get_url_info`:
  - Run the `requests` + `bs4` logic.
  - If `title` is missing, or matches known cookie-wall patterns (e.g., "Just a moment...", "Accept Cookies"), the worker thread makes an HTTP POST request to the local FastAPI service (`http://localhost:8000/resolve`).
  - Return the AI summary.
- The worker thread then uses `self.send_message()` to post the result to the IRC channel.

## Verification Plan

### Automated/Local Testing
1. Spin up the Podman Pod in the `selenium-crawler` directory.
2. Start the FastAPI server.
3. Use `curl` to test the `/resolve` endpoint with known difficult URLs.

### Manual Verification
1. Run `python bot.py` and join a test IRC channel.
2. Post a direct image link or basic HTML site -> Verify instantaneous response using the fast crawler.
3. Post a complex URL -> Verify the bot remains responsive to other messages while waiting.
4. Verify that 5-15 seconds later, the bot outputs the strictly formatted AI-generated summary.
