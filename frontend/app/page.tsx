"use client";

import { useState } from "react";
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
} from "lucide-react";

import { askFinTrace, QueryResponse } from "@/lib/api";

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

        <button className="new-research" onClick={() => {
          setResult(null);
          setQuestion("");
          setError("");
        }}>
          <Sparkles size={17} />
          New research
        </button>

        <div className="sidebar-section">
          <span className="sidebar-label">WORKSPACE</span>

          <div className="nav-item active">
            <Search size={17} />
            Research
          </div>

          <div className="nav-item">
            <BookOpen size={17} />
            Sources
            <span className="nav-soon">Soon</span>
          </div>

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
          <div className="sidebar-footer">FINTRACE · RESEARCH ENGINE</div>
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
          </div>

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
    </main>
  );
}