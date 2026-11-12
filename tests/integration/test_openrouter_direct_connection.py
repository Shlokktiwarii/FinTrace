import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
MODEL = os.getenv(
    "FINTRACE_EVALUATION_MODEL",
    "nvidia/nemotron-3.5-super-vl:free",
)
BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "https://openrouter.ai/api/v1",
)


def test_openrouter_direct_connection():
    if not API_KEY:
        raise RuntimeError("LLM_API_KEY not found in .env")

    print("\nTesting OpenRouter connection...")
    print(f"Model: {MODEL}")

    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=60.0,
        max_retries=1,
    )

    start = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Reply with exactly: "
                        "FinTrace OpenRouter connection successful."
                    ),
                }
            ],
            temperature=0,
            max_tokens=100,
        )

        elapsed = time.perf_counter() - start
        content = response.choices[0].message.content

        print(f"\nResponse: {content}")
        print(f"Response time: {elapsed:.2f} seconds")

        assert content
        assert "FinTrace OpenRouter connection successful" in content

    except Exception as exc:
        elapsed = time.perf_counter() - start
        print(f"\nOpenRouter request failed after {elapsed:.2f} seconds")
        print(f"Error type: {type(exc).__name__}")
        print(f"Error: {exc}")
        raise

    finally:
        client.close()