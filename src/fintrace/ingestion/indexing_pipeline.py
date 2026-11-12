from fintrace.ingestion.parsers.pdf import PdfParser
from fintrace.ingestion.normalizer import DocumentNormalizer
from fintrace.ingestion.structure import DocumentStructureExtractor
from fintrace.ingestion.chunker import DocumentChunker

from fintrace.retrieval.indexer import ChunkIndexer
from fintrace.retrieval.vector_store import VectorStore


class DocumentIndexingPipeline:
    """Process raw financial documents and index their chunks."""

    def __init__(
        self,
        parser: PdfParser,
        normalizer: DocumentNormalizer,
        structure_extractor: DocumentStructureExtractor,
        chunker: DocumentChunker,
        indexer: ChunkIndexer,
        vector_store: VectorStore,
    ) -> None:
        self.parser = parser
        self.normalizer = normalizer
        self.structure_extractor = structure_extractor
        self.chunker = chunker
        self.indexer = indexer
        self.vector_store = vector_store

    def index_document(self, document) -> int:
        """Parse, chunk, embed and index one financial document."""

        # 1. Extract PDF text
        parsed_document = self.parser.parse(document)

        # 2. Normalize extracted text
        normalized_document = self.normalizer.normalize(
            parsed_document
        )

        # 3. Identify document sections
        structured_pages = self.structure_extractor.extract(
            normalized_document
        )

        # 4. Create chunks
        chunks = self.chunker.chunk(
            document_id=document.document_id,
            company=document.company,
            source_url=document.source_url,
            structured_pages=structured_pages,
        )

        if not chunks:
            return 0

        # 5. Generate embeddings
        indexed_chunks = self.indexer.index(chunks)

        # 6. Store in Qdrant
        self.vector_store.upsert(indexed_chunks)

        return len(indexed_chunks)