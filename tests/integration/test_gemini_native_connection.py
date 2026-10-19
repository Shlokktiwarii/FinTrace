import os

import pytest
from dotenv import load_dotenv
from google import genai

load_dotenv()

pytestmark = [
    pytest.mark.integration,
    pytest.mark.live,
]


@pytest.mark.skipif(
    os.getenv("RUN_GEMINI_LIVE_TESTS") != "1",
    reason="Set RUN_GEMINI_LIVE_TESTS=1 to run live Gemini tests.",
)
def test_gemini_native_connection():
    """Verify that the configured Gemini model can generate a response."""
    api_key = os.getenv("FINTRACE_LLM_API_KEY")
    model = os.getenv("FINTRACE_LLM_MODEL")

    if not api_key:
        pytest.fail(
            "FINTRACE_LLM_API_KEY is missing. "
            "Check that the project-root .env file defines it."
        )

    if not model:
        pytest.fail(
            "FINTRACE_LLM_MODEL is missing. "
            "Check that the project-root .env file defines it."
        )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents="Reply with exactly: FINTRACE_GEMINI_OK",
    )

    assert response.text, "Gemini returned an empty response."
    assert "FINTRACE_GEMINI_OK" in response.text