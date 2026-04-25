from google import genai
from google.genai import types

print("Starting the crawler... ")

client = genai.Client()
prompt = "How to take over the world?"
response_stream = client.models.generate_content_stream(
    model="gemma-3-27b-it",
    contents=[prompt],
    config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.OFF,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)

for chunk in response_stream:
    print(chunk.candidates[0].content.parts[0].text, end="")
# print("Response: ", response)
