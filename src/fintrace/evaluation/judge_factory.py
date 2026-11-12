from __future__ import annotations

import os

from dotenv import load_dotenv

from fintrace.evaluation.ragas_embeddings import FinTraceRagasEmbeddings
from fintrace.evaluation.ragas_openrouter import OpenRouterRagasLLM


def create_ragas_judge() -> tuple[
    OpenRouterRagasLLM,
    FinTraceRagasEmbeddings,
]:
    load_dotenv()

    api_key = os.getenv("LLM_API_KEY") or os.getenv(
        "FINTRACE_LLM_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "Set LLM_API_KEY in your .env file."
        )

    model = (
        os.getenv("FINTRACE_EVALUATION_MODEL")
        or os.getenv("LLM_MODEL")
        or "openrouter/free"
    )

    base_url = os.getenv(
        "LLM_BASE_URL",
        "https://openrouter.ai/api/v1",
    )

    llm = OpenRouterRagasLLM(
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout=float(os.getenv("LLM_TIMEOUT", "90")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        temperature=0.0,
    )

    embeddings = FinTraceRagasEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
    )

    return llm, embeddings