import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)

api_key = os.getenv("FINTRACE_LLM_API_KEY")
model = os.getenv("FINTRACE_LLM_MODEL")

if not api_key:
    raise RuntimeError("FINTRACE_LLM_API_KEY was not loaded.")

if not model:
    raise RuntimeError("FINTRACE_LLM_MODEL was not loaded.")

client = genai.Client(api_key=api_key)

try:
    print(f"Testing native Gemini generation with: {model}")

    response = client.models.generate_content(
        model=model,
        contents="Reply with exactly: FINTRACE_GEMINI_OK",
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=128,
        ),
    )

    print("\n--- Response diagnostics ---")
    print("Response text:", repr(response.text))
    print("Prompt feedback:", response.prompt_feedback)

    if response.candidates:
        for index, candidate in enumerate(response.candidates):
            print(f"\nCandidate {index}:")
            print("Finish reason:", candidate.finish_reason)
            print("Content:", candidate.content)
    else:
        print("No candidates returned.")

    if response.usage_metadata:
        print("Usage metadata:", response.usage_metadata)

finally:
    client.close()