from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)
    candidate_limit: int = Field(default=10, ge=5, le=30)


class CitationResponse(BaseModel):
    evidence_id: str
    chunk_id: str
    document_id: str
    company: str
    source_url: str
    page_number: int
    section: str | None
    text: str


class VerificationCheckResponse(BaseModel):
    name: str
    status: str
    message: str
    details: list[str]


class VerificationResponse(BaseModel):
    passed: bool
    decision: str
    checks: list[VerificationCheckResponse]


class QueryResponse(BaseModel):
    question: str
    answer: str
    abstained: bool
    citations: list[CitationResponse]
    verification: VerificationResponse