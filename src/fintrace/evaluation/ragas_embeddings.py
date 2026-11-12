from __future__ import annotations

import asyncio
from typing import Any

from ragas.embeddings.base import BaseRagasEmbeddings
from sentence_transformers import SentenceTransformer


class FinTraceRagasEmbeddings(BaseRagasEmbeddings):
    """RAGAS embedding adapter using FinTrace's BGE model."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ) -> None:
        super().__init__()

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_query(self, text: str) -> list[float]:
        vector = self.model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vector.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=32,
        )
        return vectors.tolist()

    async def aembed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self.embed_query, text)

    async def aembed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return await asyncio.to_thread(self.embed_documents, texts)