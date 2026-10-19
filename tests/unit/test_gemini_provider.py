from unittest.mock import MagicMock, patch

import pytest

from fintrace.generation.gemini_provider import GeminiProvider


@patch("fintrace.generation.gemini_provider.genai.Client")
def test_generate_returns_gemini_text(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_response = MagicMock()
    mock_response.text = '{"answer": "Revenue increased.", "citation_ids": ["E1"], "abstained": false}'

    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiProvider(
        api_key="test-key",
        model="gemini-3.8-flash",
    )

    result = provider.generate("Answer using the supplied evidence.")

    assert result == (
        '{"answer": "Revenue increased.", '
        '"citation_ids": ["E1"], "abstained": false}'
    )

    mock_client.models.generate_content.assert_called_once()


@patch("fintrace.generation.gemini_provider.genai.Client")
def test_generate_rejects_empty_prompt(mock_client_class):
    provider = GeminiProvider(
        api_key="test-key",
        model="gemini-3.8-flash",
    )

    with pytest.raises(ValueError, match="Prompt must not be empty"):
        provider.generate("   ")


@patch("fintrace.generation.gemini_provider.genai.Client")
def test_generate_rejects_empty_response(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_response = MagicMock()
    mock_response.text = None

    mock_client.models.generate_content.return_value = mock_response

    provider = GeminiProvider(
        api_key="test-key",
        model="gemini-3.8-flash",
    )

    with pytest.raises(RuntimeError, match="no usable text"):
        provider.generate("Answer using the supplied evidence.")


def test_rejects_empty_api_key():
    with pytest.raises(ValueError, match="API key must not be empty"):
        GeminiProvider(api_key="  ", model="gemini-3.8-flash")


def test_rejects_empty_model():
    with pytest.raises(ValueError, match="Model name must not be empty"):
        GeminiProvider(api_key="test-key", model="  ")