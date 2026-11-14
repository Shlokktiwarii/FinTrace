const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface Citation {
  evidence_id: string;
  chunk_id: string;
  document_id: string;
  company: string;
  source_url: string;
  page_number: number;
  section: string | null;
  text: string;
}

export interface VerificationCheck {
  name: string;
  status: "pass" | "fail" | "warning" | "not_checked";
  message: string;
  details: string[];
}

export interface QueryResponse {
  question: string;
  answer: string;
  abstained: boolean;
  citations: Citation[];
  verification: {
    passed: boolean;
    decision: string;
    checks: VerificationCheck[];
  };
}

export async function askFinTrace(
  question: string
): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      limit: 5,
      candidate_limit: 20,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `API error: ${response.status}`);
  }

  return response.json();
}
export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  company: string;
  status: string;
  chunks_indexed: number;
  source_url: string;
}

export interface DocumentUploadInput {
  file: File;
  company: string;
  ticker?: string;
  exchange?: string;
  document_type: string;
}

export async function uploadDocument(
  input: DocumentUploadInput
): Promise<DocumentUploadResponse> {
  const formData = new FormData();

  formData.append("file", input.file);
  formData.append("company", input.company);
  formData.append("ticker", input.ticker || "");
  formData.append("exchange", input.exchange || "");
  formData.append("document_type", input.document_type);

  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  const responseText = await response.text();

  if (!response.ok) {
    let message = responseText;

    try {
      const parsed = JSON.parse(responseText);
      message = parsed.detail || parsed.message || responseText;
    } catch {
      // Response wasn't JSON; preserve the original error.
    }

    throw new Error(
      `Upload failed (${response.status}): ${message.slice(0, 500)}`
    );
  }

  return JSON.parse(responseText) as DocumentUploadResponse;
}

export interface StoredDocument {
  document_id: string;
  filename: string;
  company: string;
  ticker: string | null;
  document_type: string;
  status: string;
  chunks_indexed: number;
  file_size: number;
  created_at: string;
  source_url: string;
}

export async function getDocuments(): Promise<StoredDocument[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/documents/`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch documents.");
  }

  return response.json();
}