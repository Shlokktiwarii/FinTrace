import os

import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("FINTRACE_LLM_API_KEY")

if not api_key:
    raise RuntimeError("FINTRACE_LLM_API_KEY is not configured.")

response = httpx.get(
    "https://generativelanguage.googleapis.com/v1beta/models",
    headers={"x-goog-api-key": api_key},
    timeout=30.0,
)

print("HTTP status:", response.status_code)
response.raise_for_status()

for model in response.json().get("models", []):
    methods = model.get("supportedGenerationMethods", [])

    if "generateContent" in methods:
        print(model["name"])