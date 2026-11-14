from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4, UUID

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    Depends,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from fintrace.api.dependencies import load_all_chunks
from fintrace.database.session import get_db
from fintrace.database.models import Document
from fintrace.ingestion.models import (
    DocumentSource,
    DocumentType,
    RawDocument,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path("data/uploads")
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("/upload")
async def upload_document(
    request: Request,
    db: Session = Depends(get_db),
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

    # 4. Generate document ID.
    document_id = uuid4()

    # 5. Save original PDF locally.
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    file_path = UPLOAD_DIR / f"{document_id}.pdf"
    file_path.write_bytes(content)

    source_url = (
        f"{str(request.base_url).rstrip('/')}"
        f"/api/v1/documents/{document_id}/file"
    )

    # 6. Create initial database record.
    document = Document(
        id=document_id,
        company=company,
        ticker=ticker,
        exchange=exchange,
        filename=file.filename,
        document_type=doc_type.value,
        source=DocumentSource.COMPANY.value,
        source_url=source_url,
        storage_bucket="local",
        storage_path=str(file_path),
        file_size=len(content),
        status="pending",
        chunks_indexed=0,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # 7. Construct RawDocument.
    raw_document = RawDocument(
        document_id=str(document_id),
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
        # 8. Run existing ingestion pipeline.
        chunks_indexed = await run_in_threadpool(
            services["indexing_pipeline"].index_document,
            raw_document,
        )

        if chunks_indexed == 0:
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in the PDF.",
            )

        # 9. Refresh BM25.
        updated_chunks = await run_in_threadpool(
            load_all_chunks,
            services["vector_store"],
        )

        services["sparse_retriever"].index(updated_chunks)
        services["chunks"] = updated_chunks

        # 10. Update database record.
        document.status = "completed"
        document.chunks_indexed = chunks_indexed
        document.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(document)

    except Exception as exc:
        db.rollback()

        # Mark document as failed.
        failed_document = db.get(Document, document_id)

        if failed_document:
            failed_document.status = "failed"
            failed_document.error_message = str(exc)
            failed_document.updated_at = datetime.now(UTC)
            db.commit()

        raise

    return {
        "document_id": str(document_id),
        "filename": file.filename,
        "company": company,
        "status": document.status,
        "chunks_indexed": chunks_indexed,
        "source_url": source_url,
    }


@router.get("/")
def list_documents(
    db: Session = Depends(get_db),
):
    statement = (
        select(Document)
        .order_by(Document.created_at.desc())
        .limit(50)
    )

    documents = db.scalars(statement).all()

    return [
        {
            "document_id": str(document.id),
            "filename": document.filename,
            "company": document.company,
            "ticker": document.ticker,
            "document_type": document.document_type,
            "status": document.status,
            "chunks_indexed": document.chunks_indexed,
            "file_size": document.file_size,
            "created_at": document.created_at,
            "source_url": document.source_url,
        }
        for document in documents
    ]


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