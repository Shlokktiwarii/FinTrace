from unittest.mock import MagicMock, patch

import pytest

from fintrace.generation.openrouter_provider import OpenRouterProvider


def test_provider_rejects_empty_api_key():
    with pytest.raises(ValueError):
        OpenRouterProvider(api_key="")


def test_provider_rejects_empty_prompt():
    provider = OpenRouterProvider(
        api_key="test-key",
    )

    with pytest.raises(ValueError):
        provider.generate("")


@patch("fintrace.generation.openrouter_provider.OpenAI")
def test_generate_returns_response(mock_openai):

    mock_client = MagicMock()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        '{"answer": "Test answer [E1]", '
        '"citation_ids": ["E1"], "abstained": false}'
    )

    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    provider = OpenRouterProvider(
        api_key="test-key",
        model="openrouter/free",
    )

    result = provider.generate("Test prompt")

    assert "Test answer" in result

    mock_client.chat.completions.create.assert_called_once()


@patch("fintrace.generation.openrouter_provider.OpenAI")
def test_generate_rejects_empty_response(mock_openai):

    mock_client = MagicMock()

    mock_response = MagicMock()
    mock_response.choices[0].message.content = None

    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client

    provider = OpenRouterProvider(
        api_key="test-key",
    )

    with pytest.raises(RuntimeError):
        provider.generate("Test prompt")