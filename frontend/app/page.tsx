"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  FileText,
  Loader2,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  XCircle,
  Upload,
  FileUp,
  X,
  Database,
} from "lucide-react";

import {
  askFinTrace,
  uploadDocument,
  getDocuments,
  QueryResponse,
  DocumentUploadResponse,
  StoredDocument,
} from "@/lib/api";

const suggestions = [
  "What was Reliance Industries' revenue from operations in FY2025?",
  "Compare Reliance's revenue in FY2024 and FY2025.",
  "What was the total income of Reliance Industries in FY2025?",
];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState("");

  const [expandedCitation, setExpandedCitation] = useState<string | null>(
    null
  );

  // Document upload state
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const [file, setFile] = useState<File | null>(null);
  const [company, setCompany] = useState("");
  const [ticker, setTicker] = useState("");
  const [exchange, setExchange] = useState("NSE");
  const [documentType, setDocumentType] = useState("annual_report");

  const [uploadResult, setUploadResult] =
    useState<DocumentUploadResponse | null>(null);

  // Persistent document history
  const [uploadedDocuments, setUploadedDocuments] = useState<
    StoredDocument[]
  >([]);

  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentsError, setDocumentsError] = useState("");

  // Fetch document history when workspace loads
  useEffect(() => {
    async function fetchDocuments() {
      try {
        const documents = await getDocuments();
        setUploadedDocuments(documents);
        setDocumentsError("");
      } catch (err) {
        setDocumentsError(
          err instanceof Error
            ? err.message
            : "Unable to load documents."
        );
      } finally {
        setDocumentsLoading(false);
      }
    }

    fetchDocuments();
  }, []);

  async function refreshDocuments() {
    try {
      const documents = await getDocuments();
      setUploadedDocuments(documents);
      setDocumentsError("");
    } catch (err) {
      setDocumentsError(
        err instanceof Error
          ? err.message
          : "Unable to refresh documents."
      );
    }
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!question.trim() || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await askFinTrace(question.trim());
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!file || !company.trim() || uploading) return;

    setUploading(true);
    setUploadError("");
    setUploadResult(null);

    try {
      const response = await uploadDocument({
        file,
        company: company.trim(),
        ticker: ticker.trim(),
        exchange,
        document_type: documentType,
      });

      setUploadResult(response);

      // Refresh persistent document history from PostgreSQL
      await refreshDocuments();

      setFile(null);
      setCompany("");
      setTicker("");
    } catch (err) {
      setUploadError(
        err instanceof Error
          ? err.message
          : "Document upload failed."
      );
    } finally {
      setUploading(false);
    }
  }

  function closeUploadModal() {
    if (uploading) return;

    setUploadOpen(false);
    setUploadError("");
    setUploadResult(null);
    setFile(null);
  }

  function statusIcon(status: string) {
    switch (status) {
      case "pass":
        return <CheckCircle2 size={16} className="status-pass" />;

      case "fail":
        return <XCircle size={16} className="status-fail" />;

      case "warning":
        return <CircleAlert size={16} className="status-warning" />;

      default:
        return <Activity size={16} className="status-muted" />;
    }
  }

  function documentStatusClass(status: string) {
    switch (status) {
      case "completed":
        return "text-emerald-400";
      case "failed":
        return "text-red-400";
      default:
        return "text-amber-400";
    }
  }

  return (
    <main className="workspace">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <TrendingUp size={21} />
          </div>

          <div>
            <h1>FinTrace</h1>
            <span>Financial Intelligence</span>
          </div>
        </div>

        <button
          className="new-research"
          onClick={() => {
            setResult(null);
            setQuestion("");
            setError("");
          }}
        >
          <Sparkles size={17} />
          New research
        </button>

        <div className="sidebar-section">
          <span className="sidebar-label">WORKSPACE</span>

          <div className="nav-item active">
            <Search size={17} />
            Research
          </div>

          <button
            className="nav-item"
            onClick={() => setUploadOpen(true)}
          >
            <BookOpen size={17} />
            Documents
            <span className="nav-soon">Upload</span>
          </button>

          <div className="nav-item">
            <ShieldCheck size={17} />
            Verification
            <span className="nav-soon">Soon</span>
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="live-dot" />

            <div>
              <strong>System operational</strong>
              <small>FinTrace API workspace</small>
            </div>
          </div>

          <div className="sidebar-footer">
            FINTRACE · RESEARCH ENGINE
          </div>
        </div>
      </aside>

      <section className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> Research
          </div>

          <div className="topbar-right">
            <span className="environment">
              <span className="live-dot" />
              Development
            </span>

            <div className="avatar">FT</div>
          </div>
        </header>

        <div className="content-area">
          <div className="heading">
            <div className="eyebrow">
              <Sparkles size={14} />
              EVIDENCE-FIRST FINANCIAL RESEARCH
            </div>

            <h2>
              Research with
              <span> confidence.</span>
            </h2>

            <p>
              Ask questions about financial filings. Get grounded answers
              with traceable evidence and transparent verification.
            </p>

            <button
              type="button"
              onClick={() => setUploadOpen(true)}
              className="mt-5 inline-flex items-center gap-2 rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-2.5 text-sm font-medium text-blue-400 transition hover:bg-blue-500/20"
            >
              <Upload size={16} />
              Upload financial report
            </button>
          </div>

          {/* Persistent document history */}
          <section className="mb-7 rounded-xl border border-white/10 bg-white/[0.02] p-5">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database size={17} className="text-blue-400" />
                <h3 className="text-sm font-semibold">
                  Recently uploaded
                </h3>
              </div>

              <span className="text-xs text-slate-500">
                {uploadedDocuments.length} documents
              </span>
            </div>

            {documentsLoading ? (
              <div className="flex items-center gap-2 py-5 text-sm text-slate-400">
                <Loader2 size={16} className="animate-spin" />
                Loading document history...
              </div>
            ) : documentsError ? (
              <div className="flex items-center gap-2 py-4 text-sm text-red-400">
                <CircleAlert size={16} />
                {documentsError}
              </div>
            ) : uploadedDocuments.length === 0 ? (
              <div className="py-6 text-center">
                <FileText
                  className="mx-auto mb-2 text-slate-500"
                  size={25}
                />
                <p className="text-sm text-slate-400">
                  No documents uploaded yet.
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Upload a financial report to get started.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {uploadedDocuments.map((document) => (
                  <div
                    key={document.document_id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-white/5 bg-white/[0.02] p-3"
                  >
                    <div className="flex min-w-0 items-center gap-3">
                      <FileText
                        size={19}
                        className="shrink-0 text-blue-400"
                      />

                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-white">
                          {document.company}
                        </p>

                        <p className="truncate text-xs text-slate-500">
                          {document.filename}
                        </p>

                        <p className="mt-1 text-xs text-slate-600">
                          {new Date(
                            document.created_at
                          ).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <span className="text-xs text-slate-400">
                        {document.chunks_indexed} chunks
                      </span>

                      <span
                        className={`text-xs ${documentStatusClass(
                          document.status
                        )}`}
                      >
                        {document.status === "completed"
                          ? "Indexed"
                          : document.status}
                      </span>

                      <a
                        href={document.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        title="Open PDF"
                        className="rounded-md p-2 text-slate-400 transition hover:bg-white/10 hover:text-white"
                      >
                        <ArrowUpRight size={16} />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <form className="query-box" onSubmit={handleSubmit}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about a company, financial statement, or annual report..."
              rows={3}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
            />

            <div className="query-bottom">
              <span>
                <ShieldCheck size={14} />
                Answers grounded in retrieved evidence
              </span>

              <button
                type="submit"
                disabled={loading || !question.trim()}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="spin" />
                    Researching
                  </>
                ) : (
                  <>
                    Research <ArrowUpRight size={17} />
                  </>
                )}
              </button>
            </div>
          </form>

          {!result && !loading && (
            <div className="suggestions">
              <span className="suggestion-label">TRY ASKING</span>

              {suggestions.map((item) => (
                <button
                  key={item}
                  onClick={() => setQuestion(item)}
                  className="suggestion"
                >
                  {item}
                  <ArrowUpRight size={14} />
                </button>
              ))}
            </div>
          )}

          {loading && (
            <div className="loading-panel">
              <Loader2 size={25} className="spin" />

              <div>
                <strong>Analyzing financial evidence</strong>

                <p>
                  Retrieving relevant passages, generating an answer and
                  running verification checks.
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="error-panel">
              <CircleAlert size={19} />

              <div>
                <strong>Unable to complete research</strong>
                <p>{error}</p>

                <small>
                  Check that your FastAPI server is running and CORS is
                  configured.
                </small>
              </div>
            </div>
          )}

          {result && (
            <div className="results">
              <div className="result-heading">
                <div>
                  <span className="result-label">RESEARCH RESULT</span>
                  <h3>{result.question}</h3>
                </div>

                <span className="result-count">
                  {result.citations.length} sources
                </span>
              </div>

              <section className="answer-card">
                <div className="card-heading">
                  <div className="card-title">
                    <Sparkles size={17} />
                    Generated answer
                  </div>

                  <span className="answer-badge">
                    {result.abstained ? "Abstained" : "Response"}
                  </span>
                </div>

                <p className="answer-text">{result.answer}</p>

                <div className="answer-meta">
                  <span>
                    <FileText size={14} />
                    {result.citations.length} cited evidence items
                  </span>
                </div>
              </section>

              <section className="verification-card">
                <div className="card-heading">
                  <div className="card-title">
                    <ShieldCheck size={17} />
                    Verification report
                  </div>

                  <span
                    className={`decision decision-${result.verification.decision}`}
                  >
                    {result.verification.decision.toUpperCase()}
                  </span>
                </div>

                <p className="verification-note">
                  Verification reflects the checks configured in the
                  backend. A passing decision does not necessarily mean
                  every claim has undergone semantic verification.
                </p>

                <div className="checks">
                  {result.verification.checks.map((check) => (
                    <div className="check-row" key={check.name}>
                      {statusIcon(check.status)}

                      <div className="check-content">
                        <strong>
                          {check.name.replaceAll("_", " ")}
                        </strong>

                        <p>{check.message}</p>
                      </div>

                      <span className={`check-status ${check.status}`}>
                        {check.status.replaceAll("_", " ")}
                      </span>
                    </div>
                  ))}
                </div>
              </section>

              <section className="evidence-section">
                <div className="evidence-heading">
                  <div>
                    <span className="result-label">SOURCE MATERIAL</span>
                    <h3>Retrieved evidence</h3>
                  </div>

                  <span className="result-count">
                    {result.citations.length} citations
                  </span>
                </div>

                {result.citations.map((citation) => (
                  <article
                    className="evidence-card"
                    key={citation.evidence_id}
                  >
                    <div className="evidence-top">
                      <span className="evidence-id">
                        {citation.evidence_id}
                      </span>

                      <span className="page-label">
                        PDF page {citation.page_number}
                      </span>
                    </div>

                    <h4>{citation.company}</h4>

                    <div className="evidence-section-name">
                      {citation.section || "Financial document"}
                    </div>

                    <p
                      className={`evidence-text ${
                        expandedCitation === citation.evidence_id
                          ? "expanded"
                          : ""
                      }`}
                    >
                      {citation.text}
                    </p>

                    <button
                      className="expand-button"
                      onClick={() =>
                        setExpandedCitation(
                          expandedCitation === citation.evidence_id
                            ? null
                            : citation.evidence_id
                        )
                      }
                    >
                      {expandedCitation === citation.evidence_id
                        ? "Show less"
                        : "Read full excerpt"}

                      <ChevronDown
                        size={15}
                        className={
                          expandedCitation === citation.evidence_id
                            ? "rotate"
                            : ""
                        }
                      />
                    </button>

                    <div className="evidence-footer">
                      <span>
                        Chunk: {citation.chunk_id.slice(-12)}
                      </span>

                      <a
                        href={citation.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Open original report
                        <ArrowUpRight size={14} />
                      </a>
                    </div>
                  </article>
                ))}
              </section>
            </div>
          )}

          <footer className="page-footer">
            FinTrace · Evidence-first financial intelligence
          </footer>
        </div>
      </section>

      {/* PDF Upload Modal */}
      {uploadOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/70 p-4 backdrop-blur-sm"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeUploadModal();
            }
          }}
        >
          <div className="my-auto w-full max-w-xl rounded-2xl border border-white/10 bg-[#101827] p-6 shadow-2xl sm:p-8">
            <div className="mb-6 flex items-start justify-between">
              <div>
                <div className="mb-3 flex items-center gap-2 text-blue-400">
                  <FileUp size={19} />
                  <span className="text-xs font-semibold tracking-wider">
                    DOCUMENT INGESTION
                  </span>
                </div>

                <h3 className="text-xl font-semibold text-white">
                  Add financial document
                </h3>

                <p className="mt-1 text-sm text-slate-400">
                  Upload and index a financial report in FinTrace.
                </p>
              </div>

              <button
                type="button"
                onClick={closeUploadModal}
                disabled={uploading}
                className="rounded-lg p-2 text-slate-400 transition hover:bg-white/10 hover:text-white disabled:opacity-40"
              >
                <X size={19} />
              </button>
            </div>

            {uploadResult ? (
              <div className="space-y-5">
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-5">
                  <div className="mb-3 flex items-center gap-2 text-emerald-400">
                    <CheckCircle2 size={21} />

                    <strong>
                      Document indexed successfully
                    </strong>
                  </div>

                  <p className="text-sm text-slate-300">
                    {uploadResult.filename}
                  </p>

                  <div className="mt-4 grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-black/20 p-3">
                      <p className="text-xs text-slate-400">
                        Indexed chunks
                      </p>

                      <p className="mt-1 text-2xl font-semibold text-white">
                        {uploadResult.chunks_indexed}
                      </p>
                    </div>

                    <div className="rounded-lg bg-black/20 p-3">
                      <p className="text-xs text-slate-400">
                        Status
                      </p>

                      <p className="mt-2 font-semibold text-emerald-400">
                        {uploadResult.status}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4">
                    <p className="text-xs text-slate-400">
                      Document ID
                    </p>

                    <p className="mt-1 break-all font-mono text-xs text-slate-200">
                      {uploadResult.document_id}
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setUploadResult(null);
                      setFile(null);
                    }}
                    className="flex-1 rounded-lg border border-white/10 px-4 py-3 text-sm text-slate-300 transition hover:bg-white/5"
                  >
                    Upload another
                  </button>

                  <button
                    type="button"
                    onClick={closeUploadModal}
                    className="flex-1 rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-blue-500"
                  >
                    Back to research
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleUpload} className="space-y-5">
                <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-white/15 bg-[#0b1220] px-5 py-8 text-center transition hover:border-blue-500/60">
                  <Upload
                    size={27}
                    className="mb-3 text-blue-400"
                  />

                  <span className="text-sm font-medium text-white">
                    {file ? file.name : "Choose a PDF document"}
                  </span>

                  <span className="mt-2 text-xs text-slate-500">
                    PDF files up to 50 MB
                  </span>

                  <input
                    type="file"
                    accept=".pdf,application/pdf"
                    className="hidden"
                    onChange={(event) => {
                      const selectedFile =
                        event.target.files?.[0] || null;

                      setFile(selectedFile);
                      setUploadError("");
                    }}
                  />
                </label>

                <div>
                  <label className="mb-2 block text-sm text-slate-300">
                    Company name *
                  </label>

                  <input
                    required
                    value={company}
                    onChange={(event) => setCompany(event.target.value)}
                    placeholder="e.g. Infosys Limited"
                    className="w-full rounded-lg border border-white/10 bg-[#0b1220] px-4 py-3 text-sm text-white outline-none transition focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="mb-2 block text-sm text-slate-300">
                      Stock ticker
                    </label>

                    <input
                      value={ticker}
                      onChange={(event) => setTicker(event.target.value)}
                      placeholder="e.g. INFY"
                      className="w-full rounded-lg border border-white/10 bg-[#0b1220] px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm text-slate-300">
                      Exchange
                    </label>

                    <select
                      value={exchange}
                      onChange={(event) => setExchange(event.target.value)}
                      className="w-full rounded-lg border border-white/10 bg-[#0b1220] px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
                    >
                      <option value="NSE">NSE</option>
                      <option value="BSE">BSE</option>
                      <option value="NYSE">NYSE</option>
                      <option value="NASDAQ">NASDAQ</option>
                      <option value="">Not specified</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="mb-2 block text-sm text-slate-300">
                    Document type
                  </label>

                  <select
                    value={documentType}
                    onChange={(event) =>
                      setDocumentType(event.target.value)
                    }
                    className="w-full rounded-lg border border-white/10 bg-[#0b1220] px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
                  >
                    <option value="annual_report">
                      Annual Report
                    </option>

                    <option value="financial_result">
                      Financial Result
                    </option>

                    <option value="corporate_filing">
                      Corporate Filing
                    </option>

                    <option value="earnings_presentation">
                      Earnings Presentation
                    </option>
                  </select>
                </div>

                {uploadError && (
                  <div className="flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
                    <CircleAlert size={17} className="shrink-0" />
                    {uploadError}
                  </div>
                )}

                <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
                  <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-300">
                    <Database size={14} className="text-blue-400" />
                    Ingestion pipeline
                  </div>

                  <p className="text-xs leading-5 text-slate-500">
                    PDF extraction → Normalization → Chunking →
                    Embeddings → Qdrant indexing → BM25 refresh
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={uploading || !file || !company.trim()}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {uploading ? (
                    <>
                      <Loader2 size={17} className="animate-spin" />
                      Processing and indexing...
                    </>
                  ) : (
                    <>
                      <Upload size={17} />
                      Upload and index document
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </main>
  );
}