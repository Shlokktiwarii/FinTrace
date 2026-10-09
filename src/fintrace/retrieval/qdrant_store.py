from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.models import IndexedChunk, SearchResult


class QdrantVectorStore:
    """Store and retrieve document embeddings using Qdrant."""

    def __init__(
        self,
        url: str,
        collection_name: str,
        vector_size: int,
        api_key: str | None = None,
        client: QdrantClient | None = None,
    ) -> None:
        if vector_size < 1:
            raise ValueError("Vector size must be at least 1")

        self.collection_name = collection_name
        self.vector_size = vector_size

        self.client = client or QdrantClient(
            url=url,
            api_key=api_key or None,
        )

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the collection if necessary and validate its dimension."""
        collections = self.client.get_collections().collections
        existing_names = {collection.name for collection in collections}

        if self.collection_name not in existing_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )
            return

        collection_info = self.client.get_collection(
            self.collection_name
        )
        vectors_config = collection_info.config.params.vectors

        if not isinstance(vectors_config, VectorParams):
            raise ValueError(
                f"Collection {self.collection_name!r} must use "
                "a single unnamed dense vector configuration."
            )

        if vectors_config.size != self.vector_size:
            raise ValueError(
                f"Collection {self.collection_name!r} has vector size "
                f"{vectors_config.size}; expected {self.vector_size}."
            )

    def upsert(self, chunks: list[IndexedChunk]) -> None:
        """Insert or update indexed chunks in Qdrant."""
        if not chunks:
            return

        points: list[PointStruct] = []

        for indexed_chunk in chunks:
            chunk = indexed_chunk.chunk
            embedding = indexed_chunk.embedding

            if len(embedding) != self.vector_size:
                raise ValueError(
                    f"Chunk {chunk.chunk_id!r} has embedding dimension "
                    f"{len(embedding)}; expected {self.vector_size}."
                )

            point_id = str(
                uuid5(NAMESPACE_URL, chunk.chunk_id)
            )

            points.append(
                PointStruct(
                    id=point_id,
                    vector=list(embedding),
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "company": chunk.company,
                        "source_url": chunk.source_url,
                        "page_number": chunk.page_number,
                        "section": chunk.section,
                        "text": chunk.text,
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

    def search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[SearchResult]:
        """Retrieve the most similar chunks for a query embedding."""
        if limit < 1:
            raise ValueError("Limit must be at least 1")

        if len(query_embedding) != self.vector_size:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} "
                f"does not match collection dimension {self.vector_size}."
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
            with_payload=True,
        )

        return [
            self._to_search_result(point)
            for point in response.points
        ]

    @staticmethod
    def _to_search_result(point: ScoredPoint) -> SearchResult:
        """Convert a Qdrant result into the application's search model."""
        payload = point.payload

        if payload is None:
            raise ValueError(
                f"Qdrant point {point.id!r} has no payload."
            )

        required_fields = (
            "chunk_id",
            "document_id",
            "company",
            "source_url",
            "page_number",
            "text",
        )

        missing_fields = [
            field for field in required_fields
            if field not in payload
        ]

        if missing_fields:
            raise ValueError(
                f"Qdrant payload is missing fields: {missing_fields}"
            )

        chunk = DocumentChunk(
            chunk_id=str(payload["chunk_id"]),
            document_id=str(payload["document_id"]),
            company=str(payload["company"]),
            source_url=str(payload["source_url"]),
            page_number=int(payload["page_number"]),
            section=payload.get("section"),
            text=str(payload["text"]),
        )

        return SearchResult(
            chunk=chunk,
            score=float(point.score),
        )