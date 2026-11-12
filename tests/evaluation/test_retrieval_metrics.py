import math
import pytest

from fintrace.evaluation.retrieval_metrics import (
    dcg_at_k,
    evaluate_retrieval,
    hit_rate_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank_at_k,
)


RELEVANT = {"b", "d"}


def test_precision_recall_hit_rate_and_mrr():
    ranked = ["a", "b", "c", "d"]
    assert precision_at_k(ranked, RELEVANT, 3) == pytest.approx(1 / 3)
    assert recall_at_k(ranked, RELEVANT, 3) == pytest.approx(1 / 2)
    assert hit_rate_at_k(ranked, RELEVANT, 3) == 1.0
    assert reciprocal_rank_at_k(ranked, RELEVANT, 3) == 0.5


def test_no_relevant_result():
    ranked = ["a", "c"]
    assert hit_rate_at_k(ranked, RELEVANT, 2) == 0.0
    assert reciprocal_rank_at_k(ranked, RELEVANT, 2) == 0.0
    assert recall_at_k(ranked, RELEVANT, 2) == 0.0


def test_ndcg_perfect_and_reversed():
    assert ndcg_at_k(["b", "d", "a"], RELEVANT, 2) == pytest.approx(1.0)
    assert ndcg_at_k(["a", "b", "c", "d"], RELEVANT, 4) < 1.0
    assert dcg_at_k(["b", "d"], RELEVANT, 2) == pytest.approx(
        1 + 1 / math.log2(3)
    )


def test_duplicates_are_counted_once():
    assert recall_at_k(["b", "b", "a", "d"], RELEVANT, 4) == pytest.approx(1.0)
    assert precision_at_k(["b", "b", "a"], RELEVANT, 3) == pytest.approx(1 / 3)


def test_evaluate_retrieval_returns_all_metrics():
    result = evaluate_retrieval(["b", "a"], ["b"], ks=(1, 5))
    assert result["precision@1"] == 1.0
    assert result["recall@5"] == 1.0
    assert result["mrr@5"] == 1.0
    assert result["ndcg@1"] == 1.0


@pytest.mark.parametrize("k", [0, -1, 1.5, True])
def test_invalid_k_raises(k):
    with pytest.raises(ValueError):
        precision_at_k(["a"], ["a"], k)


def test_empty_relevance_is_rejected():
    with pytest.raises(ValueError, match="relevant_ids"):
        recall_at_k(["a"], [], 5)
