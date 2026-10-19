import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("FINTRACE_LLM_API_KEY")
model = os.getenv("FINTRACE_LLM_MODEL", "gemini-flash-latest")

if not api_key:
    raise RuntimeError("FINTRACE_LLM_API_KEY is not configured.")

print(f"Testing model: {model}")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model=model,
        contents="Reply with exactly: FINTRACE_GEMINI_OK",
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=128,
        ),
    )

    print("Response:", repr(response.text))
    print("Finish reason:", response.candidates[0].finish_reason)

except Exception as exc:
    print("Error type:", type(exc).__name__)
    print("Error:", str(exc))