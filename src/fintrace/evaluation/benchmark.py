"""Reusable, retriever-agnostic benchmark runner for FinTrace.

The runner deliberately accepts retriever callables instead of importing
project-specific services. This keeps the evaluation layer decoupled from
Qdrant/BM25/service construction and makes it straightforward to test.
"""
from __future__ import annotations

import json
import statistics
import time
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from fintrace.evaluation.retrieval_metrics import evaluate_retrieval


Retriever = Callable[[str, int], Sequence[Any]]


def _chunk_id(item: Any) -> str:
    """Extract chunk ID from common FinTrace result shapes."""
    if isinstance(item, str):
        return item
    if isinstance(item, Mapping):
        if "chunk_id" in item:
            return str(item["chunk_id"])
        chunk = item.get("chunk")
        if chunk is not None:
            return _chunk_id(chunk)
    chunk = getattr(item, "chunk", None)
    if chunk is not None:
        return _chunk_id(chunk)
    value = getattr(item, "chunk_id", None)
    if value is not None:
        return str(value)
    raise TypeError(f"Cannot extract chunk_id from {type(item).__name__}")


def _context(item: Any) -> str:
    if isinstance(item, Mapping):
        if "text" in item:
            return str(item["text"])
        if "chunk" in item:
            return _context(item["chunk"])
    chunk = getattr(item, "chunk", None)
    if chunk is not None:
        return _context(chunk)
    text = getattr(item, "text", None)
    if text is not None:
        return str(text)
    return ""


def _example_value(example: Any, key: str):
    if isinstance(example, Mapping):
        return example[key]
    return getattr(example, key)


def validate_dataset_labels(examples: Sequence[Any], indexed_chunk_ids: set[str]) -> None:
    """Fail fast on missing labels or IDs that are absent from the corpus."""
    if not examples:
        raise ValueError("Benchmark dataset is empty")
    errors: list[str] = []
    seen_questions: set[str] = set()
    for example in examples:
        qid = str(_example_value(example, "question_id"))
        labels = tuple(_example_value(example, "relevant_chunk_ids"))
        if qid in seen_questions:
            errors.append(f"{qid}: duplicate question_id")
        seen_questions.add(qid)
        if not labels:
            errors.append(f"{qid}: relevant_chunk_ids is empty")
        unknown = sorted(set(labels) - indexed_chunk_ids)
        if unknown:
            errors.append(f"{qid}: unknown chunk IDs: {unknown}")
    if errors:
        raise ValueError("Invalid benchmark labels:\n- " + "\n- ".join(errors))


def run_retrieval_benchmark(
    examples: Sequence[Any],
    retrievers: Mapping[str, Retriever],
    *,
    indexed_chunk_ids: set[str],
    ks: Sequence[int] = (1, 3, 5, 10),
    candidate_limit: int = 10,
) -> dict[str, Any]:
    """Run identical questions through each retriever and aggregate metrics."""
    if candidate_limit <= 0:
        raise ValueError("candidate_limit must be positive")
    if not retrievers:
        raise ValueError("At least one retriever is required")
    validate_dataset_labels(examples, indexed_chunk_ids)

    per_method: dict[str, list[dict[str, Any]]] = {}
    summaries: dict[str, Any] = {}
    for method_name, retrieve in retrievers.items():
        rows: list[dict[str, Any]] = []
        metric_values: dict[str, list[float]] = defaultdict(list)
        latencies: list[float] = []
        for example in examples:
            question = str(_example_value(example, "question"))
            qid = str(_example_value(example, "question_id"))
            relevant = list(_example_value(example, "relevant_chunk_ids"))
            start = time.perf_counter()
            results = list(retrieve(question, candidate_limit))
            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)
            ids = [_chunk_id(result) for result in results]
            metrics = evaluate_retrieval(ids, relevant, ks)
            for name, value in metrics.items():
                metric_values[name].append(value)
            rows.append({
                "question_id": qid,
                "question": question,
                "relevant_chunk_ids": relevant,
                "retrieved_chunk_ids": ids,
                "latency_ms": round(elapsed_ms, 3),
                "metrics": metrics,
                "retrieved_contexts": [_context(result) for result in results],
            })
        per_method[method_name] = rows
        summaries[method_name] = {
            "questions": len(rows),
            "candidate_limit": candidate_limit,
            "mean_latency_ms": round(statistics.mean(latencies), 3),
            "median_latency_ms": round(statistics.median(latencies), 3),
            "metrics": {
                name: round(statistics.mean(values), 6)
                for name, values in sorted(metric_values.items())
            },
        }

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_limit": candidate_limit,
        "ks": list(ks),
        "dataset_size": len(examples),
        "summary": summaries,
        "results": per_method,
    }


def write_benchmark_reports(report: dict[str, Any], output_dir: str | Path) -> tuple[Path, Path]:
    """Write machine-readable JSON and a human-readable Markdown report."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "retrieval_benchmark.json"
    md_path = output / "retrieval_benchmark.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# FinTrace Retrieval Benchmark",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Questions: {report['dataset_size']}",
        f"- Candidate limit: {report['candidate_limit']}",
        f"- Cutoffs: {', '.join(map(str, report['ks']))}",
        "",
        "| Method | Questions | Mean latency (ms) | " +
        " | ".join(f"{metric}@{k}" for k in report["ks"] for metric in ("Recall", "MRR", "nDCG")) +
        " |",
        "|---|---:|---:|" + "---:|" * (len(report["ks"]) * 3),
    ]
    for method, summary in report["summary"].items():
        metrics = summary["metrics"]
        values = [f"{metrics[f'recall@{k}']:.3f}" for k in report["ks"]]
        values += [f"{metrics[f'mrr@{k}']:.3f}" for k in report["ks"]]
        values += [f"{metrics[f'ndcg@{k}']:.3f}" for k in report["ks"]]
        lines.append(
            f"| {method} | {summary['questions']} | {summary['mean_latency_ms']:.2f} | "
            + " | ".join(values) + " |"
        )
    lines += [
        "",
        "## Interpretation notes",
        "",
        "- Compare methods on the same labelled questions and candidate limit.",
        "- Recall@k measures coverage of labelled relevant chunks.",
        "- MRR@k rewards placing the first relevant chunk near the top.",
        "- nDCG@k accounts for the ranking positions of all relevant chunks.",
        "- Latency is measured around the supplied retriever callable; model loading",
        "  and one-time warm-up should happen before invoking this runner.",
        "- A small or single-question dataset is a smoke test, not evidence of general",
        "  retrieval quality. Expand and manually verify the golden set before claims.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path
