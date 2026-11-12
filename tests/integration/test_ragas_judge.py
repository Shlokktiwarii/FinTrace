import os

import pytest
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


@pytest.mark.integration
@pytest.mark.live
@pytest.mark.asyncio
async def test_openrouter_judge_connection():

    api_key = os.getenv("LLM_API_KEY") or os.getenv("FINTRACE_LLM_API_KEY")

    if not api_key:
        pytest.skip("OpenRouter API key not configured")

    model = (
        os.getenv("FINTRACE_EVALUATION_MODEL")
        or os.getenv("LLM_MODEL", "openrouter/free")
    )

    async with AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv(
            "LLM_BASE_URL",
            "https://openrouter.ai/api/v1",
        ),
        timeout=60.0,
        max_retries=1,
    ) as client:

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with exactly: FinTrace judge operational.",
                }
            ],
            temperature=0,
            max_tokens=100,
        )

    print("\nMODEL:", model)
    print("\nFINISH REASON:", response.choices[0].finish_reason)
    print("\nMESSAGE:", response.choices[0].message)
    print("\nFULL RESPONSE:")
    print(response.model_dump_json(indent=2))

    message = response.choices[0].message

    content = message.content

    if isinstance(content, list):
        content = " ".join(
            item.text
            for item in content
            if getattr(item, "text", None)
        )

    assert content, (
        f"Model returned no text. "
        f"Finish reason: {response.choices[0].finish_reason}"
    )