"""Pure retrieval-ranking metrics for FinTrace.

All functions accept ranked chunk IDs. Duplicate retrieved IDs are ignored after
their first occurrence. Empty relevance labels are rejected: an unlabelled
question is not a valid retrieval benchmark example.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Any


def _validate_k(k: int) -> None:
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer")


def _unique_in_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("chunk IDs must be non-empty strings")
        value = value.strip()
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _inputs(retrieved_ids: Sequence[str], relevant_ids: Iterable[str]):
    retrieved = _unique_in_order(retrieved_ids)
    relevant = set(_unique_in_order(relevant_ids))
    if not relevant:
        raise ValueError("relevant_ids cannot be empty for retrieval evaluation")
    return retrieved, relevant


def precision_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Relevant unique results in the first k positions divided by k."""
    _validate_k(k)
    retrieved, relevant = _inputs(retrieved_ids, relevant_ids)
    return sum(chunk_id in relevant for chunk_id in retrieved[:k]) / k


def recall_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Fraction of all labelled relevant chunks found in the first k."""
    _validate_k(k)
    retrieved, relevant = _inputs(retrieved_ids, relevant_ids)
    return sum(chunk_id in relevant for chunk_id in retrieved[:k]) / len(relevant)


def hit_rate_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """1 if at least one relevant chunk occurs in the first k, else 0."""
    _validate_k(k)
    retrieved, relevant = _inputs(retrieved_ids, relevant_ids)
    return float(any(chunk_id in relevant for chunk_id in retrieved[:k]))


def reciprocal_rank_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Reciprocal rank of the first relevant result within k."""
    _validate_k(k)
    retrieved, relevant = _inputs(retrieved_ids, relevant_ids)
    for rank, chunk_id in enumerate(retrieved[:k], start=1):
        if chunk_id in relevant:
            return 1.0 / rank
    return 0.0


def dcg_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Binary-relevance discounted cumulative gain at k."""
    _validate_k(k)
    retrieved, relevant = _inputs(retrieved_ids, relevant_ids)
    return sum(
        1.0 / math.log2(rank + 1)
        for rank, chunk_id in enumerate(retrieved[:k], start=1)
        if chunk_id in relevant
    )


def ndcg_at_k(retrieved_ids: Sequence[str], relevant_ids: Iterable[str], k: int) -> float:
    """Normalized DCG at k with binary relevance."""
    _validate_k(k)
    retrieved, relevant = _inputs(retrieved_ids, relevant_ids)
    dcg = sum(
        1.0 / math.log2(rank + 1)
        for rank, chunk_id in enumerate(retrieved[:k], start=1)
        if chunk_id in relevant
    )
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0


def evaluate_retrieval(
    retrieved_ids: Sequence[str],
    relevant_ids: Iterable[str],
    ks: Sequence[int] = (1, 3, 5, 10),
) -> dict[str, float]:
    """Return P@k, R@k, HitRate@k, MRR@k and nDCG@k for each requested k."""
    retrieved, relevant = _inputs(retrieved_ids, relevant_ids)
    if not ks:
        raise ValueError("ks cannot be empty")
    metrics: dict[str, float] = {}
    for k in ks:
        _validate_k(k)
        metrics[f"precision@{k}"] = precision_at_k(retrieved, relevant, k)
        metrics[f"recall@{k}"] = recall_at_k(retrieved, relevant, k)
        metrics[f"hit_rate@{k}"] = hit_rate_at_k(retrieved, relevant, k)
        metrics[f"mrr@{k}"] = reciprocal_rank_at_k(retrieved, relevant, k)
        metrics[f"ndcg@{k}"] = ndcg_at_k(retrieved, relevant, k)
    return metrics
