import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)

api_key = os.getenv("FINTRACE_LLM_API_KEY")

if not api_key:
    raise RuntimeError("FINTRACE_LLM_API_KEY was not loaded.")

url = "https://generativelanguage.googleapis.com/v1beta/models"

print("Testing native Gemini API...")
print("API key loaded:", bool(api_key))

try:
    response = httpx.get(
        url,
        headers={"x-goog-api-key": api_key},
        timeout=20.0,
    )

    print("HTTP status:", response.status_code)

    if response.is_success:
        data = response.json()
        models = [
            item["name"]
            for item in data.get("models", [])
            if "generateContent"
            in item.get("supportedGenerationMethods", [])
        ]

        print("Models available for text generation:")
        for model in models:
            print(f"  {model}")

    else:
        # Print Google's error response, never the API key.
        print("Response:", response.text[:2000])

except httpx.HTTPError as exc:
    print("Connection error:", type(exc).__name__)
    print(str(exc))