from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from uuid import NAMESPACE_URL, uuid5
from fintrace.ingestion.models import DocumentChunk
from fintrace.retrieval.models import IndexedChunk, SearchResult


class QdrantVectorStore:
    """Qdrant-backed vector store."""

    def __init__(
    self,
    url: str,
    collection_name: str,
    vector_size: int,
    api_key: str | None = None,
    client: QdrantClient | None = None,
    ) -> None:
      self.collection_name = collection_name

      self.client = client or QdrantClient(
        url=url,
        api_key=api_key or None,
      )

      self._ensure_collection(vector_size)

    def _ensure_collection(
        self,
        vector_size: int,
    ) -> None:
        collections = self.client.get_collections()

        names = {
            collection.name
            for collection in collections.collections
        }

        if self.collection_name in names:
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    def upsert(
        self,
        chunks: list[IndexedChunk],
    ) -> None:
        """Insert or update indexed chunks."""

        points = [
            PointStruct(
                id=str(
                  uuid5(
                  NAMESPACE_URL,
                  chunk.chunk.chunk_id,
                   )
        ),
                vector=list(chunk.embedding),
                payload={
                    "chunk_id": chunk.chunk.chunk_id,
                    "document_id": chunk.chunk.document_id,
                    "company": chunk.chunk.company,
                    "source_url": chunk.chunk.source_url,
                    "page_number": chunk.chunk.page_number,
                    "section": chunk.chunk.section,
                    "text": chunk.chunk.text,
                },
            )
            for chunk in chunks
        ]

        if not points:
            return

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[SearchResult]:
        """Search for the most similar chunks."""

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
        ).points

        return [
            SearchResult(
                chunk=DocumentChunk(
                    chunk_id=result.payload["chunk_id"],
                    document_id=result.payload["document_id"],
                    company=result.payload["company"],
                    source_url=result.payload["source_url"],
                    page_number=result.payload["page_number"],
                    section=result.payload["section"],
                    text=result.payload["text"],
                ),
                score=result.score,
            )
            for result in results
        ]