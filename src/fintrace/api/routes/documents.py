import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from fintrace.api.dependencies import load_all_chunks
from fintrace.core.config import get_settings
from fintrace.database.models import Document
from fintrace.database.session import get_db
from fintrace.ingestion.models import (
    DocumentSource,
    DocumentType,
    RawDocument,
)
from fintrace.storage.supabase_storage import SupabaseStorage


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

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
        raise HTTPException(
            status_code=400,
            detail="Empty PDF.",
        )

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

    # 5. Initialize Supabase Storage.
    settings = get_settings()
    storage = SupabaseStorage()

    storage_bucket = settings.supabase_storage_bucket
    storage_path = f"documents/{document_id}.pdf"

    # 6. Upload PDF to Supabase Storage.
    try:
        await run_in_threadpool(
            storage.upload,
            storage_path,
            content,
        )

        logger.info(
            "PDF uploaded to Supabase Storage: %s",
            storage_path,
        )

    except Exception:
        logger.exception(
            "Supabase Storage upload failed for document %s",
            document_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to upload PDF to document storage. Check backend logs.",
        ) from None

    source_url = (
        f"{str(request.base_url).rstrip('/')}"
        f"/api/v1/documents/{document_id}/file"
    )

    # 7. Create database record.
    document = Document(
        id=document_id,
        company=company,
        ticker=ticker,
        exchange=exchange,
        filename=file.filename,
        document_type=doc_type.value,
        source=DocumentSource.COMPANY.value,
        source_url=source_url,
        storage_bucket=storage_bucket,
        storage_path=storage_path,
        file_size=len(content),
        status="pending",
        chunks_indexed=0,
    )

    try:
        db.add(document)
        db.commit()
        db.refresh(document)

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to save document metadata for %s",
            document_id,
        )

        # Remove uploaded PDF to avoid orphaned storage.
        try:
            await run_in_threadpool(
                storage.delete,
                storage_path,
            )
        except Exception:
            logger.exception(
                "Failed to clean up uploaded PDF: %s",
                storage_path,
            )

        raise HTTPException(
            status_code=500,
            detail="Failed to save document metadata.",
        ) from None

    # 8. Construct RawDocument.
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
        # 9. Run existing ingestion pipeline.
        chunks_indexed = await run_in_threadpool(
            services["indexing_pipeline"].index_document,
            raw_document,
        )

        if chunks_indexed == 0:
            raise HTTPException(
                status_code=422,
                detail="No extractable text found in the PDF.",
            )

        # 10. Refresh BM25 index.
        updated_chunks = await run_in_threadpool(
            load_all_chunks,
            services["vector_store"],
        )

        services["sparse_retriever"].index(updated_chunks)
        services["chunks"] = updated_chunks

        # 11. Update database record.
        document.status = "completed"
        document.chunks_indexed = chunks_indexed
        document.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(document)

        logger.info(
            "Document ingestion completed: %s (%s chunks)",
            document_id,
            chunks_indexed,
        )

    except Exception:
        db.rollback()

        logger.exception(
            "Document ingestion failed: %s",
            document_id,
        )

        failed_document = db.get(Document, document_id)

        if failed_document:
            failed_document.status = "failed"
            failed_document.error_message = "Document ingestion failed. Check backend logs."
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
async def get_document_file(
    document_id: str,
    db: Session = Depends(get_db),
):
    # 1. Validate document ID.
    try:
        parsed_id = UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID.",
        ) from None

    # 2. Retrieve document metadata.
    document = db.get(Document, parsed_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # 3. Download PDF from Supabase Storage.
    storage = SupabaseStorage()

    try:
        content = await run_in_threadpool(
            storage.download,
            document.storage_path,
        )

    except Exception:
        logger.exception(
            "Failed to retrieve PDF from Supabase Storage: %s",
            document.storage_path,
        )

        raise HTTPException(
            status_code=404,
            detail="Stored PDF could not be retrieved.",
        ) from None

    # 4. Return PDF.
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="{document.filename}"'
            )
        },
    )
