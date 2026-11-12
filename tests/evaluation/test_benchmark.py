from dataclasses import dataclass
import pytest

from fintrace.evaluation.benchmark import (
    run_retrieval_benchmark,
    validate_dataset_labels,
)


@dataclass
class Chunk:
    chunk_id: str
    text: str


@dataclass
class Result:
    chunk: Chunk
    score: float


@dataclass
class Example:
    question_id: str
    question: str
    relevant_chunk_ids: tuple[str, ...]


def test_runner_accepts_fintrace_search_result_shape():
    examples = [Example("Q1", "question", ("good",))]
    def dense(question, limit):
        assert limit == 3
        return [Result(Chunk("bad", "wrong"), 0.9), Result(Chunk("good", "right"), 0.8)]

    report = run_retrieval_benchmark(
        examples,
        {"dense": dense},
        indexed_chunk_ids={"bad", "good"},
        candidate_limit=3,
        ks=(1, 2),
    )
    summary = report["summary"]["dense"]
    assert summary["metrics"]["recall@2"] == 1.0
    assert summary["metrics"]["mrr@2"] == 0.5
    assert report["results"]["dense"][0]["retrieved_contexts"] == ["wrong", "right"]


def test_empty_labels_rejected():
    with pytest.raises(ValueError, match="relevant_chunk_ids is empty"):
        validate_dataset_labels(
            [Example("Q1", "question", ())],
            {"known"},
        )


def test_unknown_labels_rejected():
    with pytest.raises(ValueError, match="unknown chunk IDs"):
        validate_dataset_labels(
            [Example("Q1", "question", ("missing",))],
            {"known"},
        )
