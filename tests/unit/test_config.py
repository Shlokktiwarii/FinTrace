from fintrace.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"

    assert settings.source_request_timeout == 30
    assert settings.source_max_retries == 3

    assert settings.qdrant_url == "http://localhost:6333"
    assert settings.qdrant_collection == "fintrace_chunks"
    assert settings.qdrant_api_key == ""