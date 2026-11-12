from pathlib import Path

from fintrace.evaluation.dataset import load_dataset


def test_load_golden_dataset():
    path = (
        Path(__file__).parents[2]
        / "src"
        / "fintrace"
        / "evaluation"
        / "datasets"
        / "golden_questions.jsonl"
    )

    examples = load_dataset(path)

    assert len(examples) > 0

    for example in examples:
        assert example.question_id
        assert example.question
        assert example.reference
        assert example.company
        assert example.fiscal_year
        assert example.evaluation_type in {
            "numerical",
            "comparative",
            "qualitative",
        }
        assert len(example.reference_contexts) > 0