from fastapi import APIRouter, HTTPException, Request

from fintrace.generation.prompt_builder import EvidencePromptBuilder
from fintrace.api.schemas import (
    CitationResponse,
    QueryRequest,
    QueryResponse,
    VerificationCheckResponse,
    VerificationResponse,
)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_financial_documents(
    payload: QueryRequest,
    request: Request,
):
    services = request.app.state.services

    try:
        # 1. Retrieve and rerank evidence.
        results = services["retrieval"].search(
            query=payload.question,
            limit=payload.limit,
            candidate_limit=payload.candidate_limit,
        )

        # 2. Build evidence using the same builder as generation.
        prompt_builder = EvidencePromptBuilder()
        evidence = prompt_builder.build_evidence(results)

        # 3. Generate answer.
        generated_answer = services["generation"].answer(
            question=payload.question,
            results=results,
        )

        # 4. Verify citations and numerical consistency.
        verification = services["verification"].verify(
            answer=generated_answer,
            evidence=evidence,
        )

        # 5. Map citations to their evidence.
        evidence_by_id = {
            item.evidence_id: item
            for item in evidence
        }

        citations = [
            CitationResponse(
                evidence_id=citation.evidence_id,
                chunk_id=evidence_by_id[citation.evidence_id].chunk_id,
                document_id=evidence_by_id[citation.evidence_id].document_id,
                company=evidence_by_id[citation.evidence_id].company,
                source_url=evidence_by_id[citation.evidence_id].source_url,
                page_number=evidence_by_id[citation.evidence_id].page_number,
                section=evidence_by_id[citation.evidence_id].section,
                text=evidence_by_id[citation.evidence_id].text,
            )
            for citation in generated_answer.citations
        ]

        return QueryResponse(
            question=generated_answer.question,
            answer=generated_answer.answer,
            abstained=generated_answer.abstained,
            citations=citations,
            verification=VerificationResponse(
                passed=verification.passed,
                decision=verification.decision.value,
                checks=[
                    VerificationCheckResponse(
                        name=check.name,
                        status=check.status.value,
                        message=check.message,
                        details=list(check.details),
                    )
                    for check in verification.checks
                ],
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Log the exception in production; do not expose internals.
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question.",
        ) from exc