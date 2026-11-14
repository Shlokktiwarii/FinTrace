from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4 , UUID

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from fintrace.api.dependencies import load_all_chunks
from fintrace.ingestion.models import (
    DocumentSource,
    DocumentType,
    RawDocument,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path("data/uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    company: str = Form(...),
    ticker: str | None = Form(None),
    exchange: str | None = Form(None),
    document_type: str = Form("annual_report"),
):
    services = request.app.state.services

    # 1. Validate filename.
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    # 2. Read and validate PDF.
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Empty PDF.")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="PDF exceeds the 50 MB upload limit.",
        )

    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file.",
        )

    # 3. Validate document type.
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document type.",
        ) from None

    # 4. Generate unique document ID.
    document_id = str(uuid4())

    # 5. Save original PDF.
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / f"{document_id}.pdf"
    file_path.write_bytes(content)

    # 6. Construct RawDocument.
    source_url = (
        f"{str(request.base_url).rstrip('/')}"
        f"/api/v1/documents/{document_id}/file"
    )

    raw_document = RawDocument(
        document_id=document_id,
        company=company,
        ticker=ticker,
        exchange=exchange,
        document_type=doc_type,
        source=DocumentSource.COMPANY,
        source_url=source_url,
        content=content,
        fetched_at=datetime.now(UTC),
    )

    try:
        # 7. Parse, chunk, embed and index.
        chunks_indexed = await run_in_threadpool(
            services["indexing_pipeline"].index_document,
            raw_document,
        )

        if chunks_indexed == 0:
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in the PDF.",
            )

        # 8. Refresh BM25 with all indexed documents.
        updated_chunks = await run_in_threadpool(
            load_all_chunks,
            services["vector_store"],
        )

        services["sparse_retriever"].index(updated_chunks)
        services["chunks"] = updated_chunks

    except Exception:
        file_path.unlink(missing_ok=True)
        raise

    return {
        "document_id": document_id,
        "filename": file.filename,
        "company": company,
        "status": "completed",
        "chunks_indexed": chunks_indexed,
        "source_url": source_url,
    }


@router.get("/{document_id}/file")
async def get_document_file(document_id: str):
    try:
      document_id = str(UUID(document_id))
    except ValueError:
      raise HTTPException(
        status_code=400,
        detail="Invalid document ID.",
    ) from None
    file_path = UPLOAD_DIR / f"{document_id}.pdf"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{document_id}.pdf",
    )