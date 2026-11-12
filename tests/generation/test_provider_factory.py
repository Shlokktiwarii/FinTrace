from unittest.mock import patch

import pytest

from fintrace.core.config import Settings
from fintrace.generation.provider_factory import create_llm_provider


def test_factory_creates_openrouter_provider():

    settings = Settings(
        llm_provider="openrouter",
        llm_api_key="test-key",
        llm_model="openrouter/free",
    )

    provider = create_llm_provider(settings)

    assert provider.__class__.__name__ == "OpenRouterProvider"


def test_factory_rejects_missing_api_key():

    settings = Settings(
        llm_provider="openrouter",
        llm_api_key=None,
    )

    with pytest.raises(ValueError):
        create_llm_provider(settings)


def test_factory_rejects_unknown_provider():

    settings = Settings(
        llm_provider="unknown",
    )

    with pytest.raises(ValueError):
        create_llm_provider(settings)


@patch("fintrace.generation.provider_factory.GeminiProvider")
def test_factory_supports_gemini(mock_gemini):

    settings = Settings(
        llm_provider="gemini",
        llm_api_key="test-key",
        llm_model="gemini-model",
    )

    create_llm_provider(settings)

    mock_gemini.assert_called_once()