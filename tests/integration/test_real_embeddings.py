import math
import os

import pytest

from fintrace.retrieval.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)


@pytest.mark.skipif(
    os.getenv("RUN_REAL_MODEL_TESTS") != "1",
    reason="Set RUN_REAL_MODEL_TESTS=1 to run model integration tests",
)
def test_real_embedding_model_produces_valid_vectors() -> None:
    provider = SentenceTransformerEmbeddingProvider(
        model_name="BAAI/bge-small-en-v1.5",
        device="cpu",
    )

    texts = [
        "Revenue from operations for the financial year.",
        "The company reported its annual financial performance.",
    ]

    vectors = provider.embed_many(texts)

    assert len(vectors) == 2
    assert all(len(vector) == 384 for vector in vectors)

    for vector in vectors:
        magnitude = math.sqrt(sum(value * value for value in vector))
        assert magnitude == pytest.approx(1.0, abs=1e-4)

    similarity = sum(
        left * right
        for left, right in zip(vectors[0], vectors[1], strict=True)
    )

    assert math.isfinite(similarity)
    assert -1.0 <= similarity <= 1.0