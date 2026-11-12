import json
import os
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

client = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"],
)

collection = os.getenv("QDRANT_COLLECTION", "fintrace_chunks")

output_path = Path("data/reliance_chunks.jsonl")
output_path.parent.mkdir(parents=True, exist_ok=True)

offset = None
total = 0

with output_path.open("w", encoding="utf-8") as file:
    while True:
        points, next_offset = client.scroll(
            collection_name=collection,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = point.payload or {}

            record = {
                "chunk_id": payload.get("chunk_id", str(point.id)),
                "document_id": payload.get("document_id"),
                "company": payload.get("company"),
                "source_url": payload.get("source_url"),
                "page_number": payload.get("page_number"),
                "section": payload.get("section"),
                "text": payload.get("text", ""),
            }

            file.write(json.dumps(record, ensure_ascii=False) + "\n")
            total += 1

        if next_offset is None:
            break

        offset = next_offset

print(f"Exported {total} chunks to {output_path}")