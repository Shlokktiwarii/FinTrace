from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.prompt_values import StringPromptValue

from fintrace.evaluation.ragas_openrouter import OpenRouterRagasLLM


def make_llm() -> OpenRouterRagasLLM:
    return OpenRouterRagasLLM(
        api_key="test-key",
        model="nvidia/nemotron-3.5-super-vl:free",
    )


def test_prompt_conversion() -> None:
    prompt = StringPromptValue(text="Evaluate this answer.")

    assert OpenRouterRagasLLM._prompt_text(prompt) == (
        "Evaluate this answer."
    )


def test_empty_api_key_rejected() -> None:
    with pytest.raises(ValueError, match="API key"):
        OpenRouterRagasLLM(api_key="")


@pytest.mark.asyncio
async def test_async_generation() -> None:
    llm = make_llm()

    message = MagicMock()
    message.content = "The answer is supported."
    choice = MagicMock()
    choice.message = message
    choice.finish_reason = "stop"

    response = MagicMock()
    response.choices = [choice]

    llm._async_client.chat.completions.create = AsyncMock(
        return_value=response
    )

    result = await llm.agenerate_text(
        StringPromptValue(text="Evaluate this answer."),
    )

    assert result.generations[0][0].text == (
        "The answer is supported."
    )
    assert llm.is_finished(result)

    await llm.aclose()


@pytest.mark.asyncio
async def test_empty_response_rejected() -> None:
    llm = make_llm()

    message = MagicMock()
    message.content = None
    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.choices = [choice]

    llm._async_client.chat.completions.create = AsyncMock(
        return_value=response
    )

    with pytest.raises(RuntimeError, match="empty response"):
        await llm.agenerate_text(
            StringPromptValue(text="Evaluate this answer."),
        )

    await llm.aclose()