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