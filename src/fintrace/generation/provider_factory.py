from fintrace.core.config import Settings
from fintrace.generation.gemini_provider import GeminiProvider
from fintrace.generation.openrouter_provider import OpenRouterProvider
from fintrace.generation.provider import LLMProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Create an LLM provider from application settings."""

    provider = settings.llm_provider.lower()

    if provider == "openrouter":
        if not settings.llm_api_key:
            raise ValueError(
                "LLM_API_KEY is required for OpenRouter."
            )

        return OpenRouterProvider(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    if provider == "gemini":
        if not settings.llm_api_key:
            raise ValueError(
                "LLM_API_KEY is required for Gemini."
            )

        return GeminiProvider(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout=settings.llm_timeout,
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )