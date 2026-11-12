# FinTrace retrieval evaluation patch

## What this adds

- Binary relevance metrics: Precision@k, Recall@k, HitRate@k, MRR@k, nDCG@k.
- A retriever-agnostic benchmark runner that times each query and records ranked
  chunk IDs and contexts.
- Strict benchmark-label validation: every question must have at least one
  relevant chunk ID, and every labelled ID must exist in the indexed corpus.
- JSON and Markdown report writers.
- Unit tests for metrics, duplicate handling, dataset-label validation, and
  compatibility with the `SearchResult(chunk=DocumentChunk(...), score=...)`
  shape used by FinTrace retrieval.

## Copy files

Copy the `src/` and `tests/` directories from this patch into the root of the
FinTrace repository, preserving paths.

## Run tests

```bash
uv run pytest tests/evaluation/test_retrieval_metrics.py tests/evaluation/test_benchmark.py -q
```

## Add strict mode to the existing dataset loader

Keep draft loading backward-compatible, but add the keyword-only argument below
to `load_golden_dataset` in `src/fintrace/evaluation/dataset.py`:

```python
def load_golden_dataset(
    file_path: str | Path,
    *,
    require_relevant_chunk_ids: bool = False,
) -> list[EvaluationExample]:
```

After `_parse_example(...)` and before appending, add:

```python
if require_relevant_chunk_ids and not example.relevant_chunk_ids:
    raise ValueError(
        f"Empty 'relevant_chunk_ids' on line {line_number}; "
        "benchmark mode requires verified relevance labels."
    )
```

Update `load_dataset` to accept and forward the same keyword:

```python
def load_dataset(
    file_path: str | Path,
    *,
    require_relevant_chunk_ids: bool = False,
) -> list[EvaluationExample]:
    return load_golden_dataset(
        file_path,
        require_relevant_chunk_ids=require_relevant_chunk_ids,
    )
```

Draft authoring can continue to use the default. A benchmark must call
`load_golden_dataset(path, require_relevant_chunk_ids=True)` and then call
`validate_dataset_labels(examples, indexed_chunk_ids)` from
`fintrace.evaluation.benchmark`.

## Connect your four existing retrieval methods

The benchmark runner intentionally does not construct services. This avoids
guessing your project's current constructor signatures. After initializing and
warming up your existing dense, BM25, hybrid-RRF and hybrid-plus-reranker
services exactly as your current `scripts/compare_retrieval.py` does, pass
callables with the following contract:

```python
retrievers = {
    "dense": lambda question, limit: dense_service.search(question, limit=limit),
    "bm25": lambda question, limit: bm25_service.search(question, limit=limit),
    "hybrid_rrf": lambda question, limit: hybrid_service.search(question, limit=limit),
    "hybrid_reranked": lambda question, limit: reranked_service.search(question, limit=limit),
}
```

Adapt only the method/keyword names to the actual service APIs in your checkout.
Each callable must return a ranked sequence of FinTrace `SearchResult` objects
(or strings / mappings containing `chunk_id`). Do not include model initialization
inside the callable, or latency will include cold-start cost.

Then:

```python
from fintrace.evaluation.benchmark import (
    run_retrieval_benchmark,
    write_benchmark_reports,
)
from fintrace.evaluation.dataset import load_golden_dataset

examples = load_golden_dataset(
    "src/fintrace/evaluation/datasets/golden_questions.jsonl",
    require_relevant_chunk_ids=True,
)

# Build this set from the same indexed corpus loaded by your comparison script.
indexed_chunk_ids = {chunk.chunk_id for chunk in chunks}

report = run_retrieval_benchmark(
    examples,
    retrievers,
    indexed_chunk_ids=indexed_chunk_ids,
    ks=(1, 3, 5, 10),
    candidate_limit=10,
)
write_benchmark_reports(report, "reports/retrieval")
```

If your current services expose `retrieve(...)` rather than `search(...)`, use
that method in the lambdas. Keep the four methods on the same corpus, questions,
candidate limit, and warm-up policy.

## Current verified seed question

The first Reliance example supported by the available comparison output is:

```json
{"question_id":"RELIANCE_001","question":"What was Reliance Industries' consolidated revenue from operations in FY2025?","reference":"Reliance Industries reported consolidated revenue from operations of ₹9,80,136 crore in FY2025, compared with ₹9,14,472 crore in FY2024.","company":"Reliance Industries Limited","filing":"Integrated Annual Report 2024-25","fiscal_year":"FY2025","reference_contexts":["Revenue from Operations 25 9,80,136 9,14,472"],"relevant_chunk_ids":["bd088224-81f0-59e6-b14b-7449e65f9278-475"],"evaluation_type":"numerical"}
```

Important distinction in that report:
- Revenue from Operations: ₹9,80,136 crore
- Total Income: ₹9,98,114 crore
- Value of Sales & Services (Revenue): ₹10,71,174 crore

The label above is verified against the retrieved chunk shown in the comparison
output. It is a single-question smoke-test seed, not a statistically meaningful
golden benchmark. Do not fabricate more labels or claim general improvement from
one query. Build a broader set by reading the indexed filing chunks and manually
verifying both reference answers and relevant chunk IDs.

## Reports and interpretation

The JSON report preserves per-question ranked IDs, contexts, metrics, and
latency. The Markdown report aggregates mean metrics by retrieval method.
Review per-question failures before choosing a winner: an aggregate score can
hide numerical/section-specific failures. For financial RAG, separately test
consolidated vs standalone, revenue vs revenue from operations vs total income,
fiscal-year comparisons, units, signs, and table-row alignment.

## Limitations

This patch does not silently modify your current service constructors or claim
to have run against your live Qdrant collection. The local test suite covers the
new pure evaluation code. The four-service benchmark must be wired into your
existing comparison script and run in your Windows environment where the
Qdrant credentials, indexed chunks, and cached models are available.
