import re

from rank_bm25 import BM25Okapi

from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.models import SearchResult


_TOKEN_PATTERN = re.compile(
    r"[a-z]+(?:'[a-z]+)?|\d+(?:[.,]\d+)*|₹|%"
)


def tokenize(text: str) -> list[str]:
    """Normalize financial text into searchable tokens."""
    return _TOKEN_PATTERN.findall(text.casefold())


class BM25SparseRetriever:
    """Retrieve document chunks using BM25 lexical relevance."""

    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []
        self._bm25: BM25Okapi | None = None

    def index(self, chunks: list[DocumentChunk]) -> int:
        """Build or replace the sparse index for the supplied chunks."""
        chunk_ids = [chunk.chunk_id for chunk in chunks]

        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("Chunk IDs must be unique within an index")

        if any(not chunk.text.strip() for chunk in chunks):
            raise ValueError("Chunks must not contain empty text")

        tokenized_chunks = [
            tokenize(chunk.text)
            for chunk in chunks
        ]

        # BM25 cannot meaningfully index documents with no searchable tokens.
        searchable = [
            (chunk, tokens)
            for chunk, tokens in zip(
                chunks,
                tokenized_chunks,
                strict=True,
            )
            if tokens
        ]

        self._chunks = [chunk for chunk, _ in searchable]

        if not searchable:
            self._bm25 = None
            return 0

        corpus = [tokens for _, tokens in searchable]
        self._bm25 = BM25Okapi(corpus)

        return len(self._chunks)

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Return the highest-scoring chunks for a lexical query."""
        if not query.strip():
            raise ValueError("Query must not be empty")

        if limit < 1:
            raise ValueError("Limit must be at least 1")

        if self._bm25 is None:
            return []

        query_tokens = tokenize(query)

        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(self._chunks)),
            key=lambda index: float(scores[index]),
            reverse=True,
        )

        results: list[SearchResult] = []

        for index in ranked_indices:
            score = float(scores[index])

            # Do not return documents with no lexical overlap.
            if score <= 0:
                continue

            results.append(
                SearchResult(
                    chunk=self._chunks[index],
                    score=score,
                )
            )

            if len(results) == limit:
                break

        return results