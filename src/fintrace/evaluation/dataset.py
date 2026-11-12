import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvaluationExample:
    question_id: str
    question: str
    reference: str
    company: str
    filing: str
    fiscal_year: str
    reference_contexts: tuple[str, ...]
    relevant_chunk_ids: tuple[str, ...]
    evaluation_type: str


VALID_EVALUATION_TYPES = {
    "numerical",
    "comparative",
    "qualitative",
}

REQUIRED_FIELDS = {
    "question_id",
    "question",
    "reference",
    "company",
    "filing",
    "fiscal_year",
    "reference_contexts",
    "relevant_chunk_ids",
    "evaluation_type",
}


def _validate_string(
    data: dict[str, Any],
    field: str,
    line_number: int,
) -> str:
    value = data.get(field)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Invalid or empty '{field}' on line {line_number}"
        )

    return value.strip()


def _validate_string_list(
    data: dict[str, Any],
    field: str,
    line_number: int,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    values = data.get(field)

    if not isinstance(values, list):
        raise ValueError(
            f"Invalid '{field}' on line {line_number}: expected a list"
        )

    if not allow_empty and not values:
        raise ValueError(
            f"Empty '{field}' on line {line_number}"
        )

    if not all(
        isinstance(value, str) and value.strip()
        for value in values
    ):
        raise ValueError(
            f"Invalid values in '{field}' on line {line_number}"
        )

    cleaned_values = tuple(value.strip() for value in values)

    if len(cleaned_values) != len(set(cleaned_values)):
        raise ValueError(
            f"Duplicate values in '{field}' on line {line_number}"
        )

    return cleaned_values


def _parse_example(
    data: dict[str, Any],
    line_number: int,
) -> EvaluationExample:
    missing_fields = REQUIRED_FIELDS - data.keys()

    if missing_fields:
        raise ValueError(
            f"Missing fields on line {line_number}: "
            f"{', '.join(sorted(missing_fields))}"
        )

    question_id = _validate_string(
        data, "question_id", line_number
    )
    question = _validate_string(
        data, "question", line_number
    )
    reference = _validate_string(
        data, "reference", line_number
    )
    company = _validate_string(
        data, "company", line_number
    )
    filing = _validate_string(
        data, "filing", line_number
    )
    fiscal_year = _validate_string(
        data, "fiscal_year", line_number
    )
    evaluation_type = _validate_string(
        data, "evaluation_type", line_number
    ).lower()

    if evaluation_type not in VALID_EVALUATION_TYPES:
        raise ValueError(
            f"Invalid evaluation_type '{evaluation_type}' "
            f"on line {line_number}. "
            f"Expected one of: {', '.join(sorted(VALID_EVALUATION_TYPES))}"
        )

    reference_contexts = _validate_string_list(
        data,
        "reference_contexts",
        line_number,
        allow_empty=False,
    )

    relevant_chunk_ids = _validate_string_list(
        data,
        "relevant_chunk_ids",
        line_number,
        allow_empty=True,
    )

    return EvaluationExample(
        question_id=question_id,
        question=question,
        reference=reference,
        company=company,
        filing=filing,
        fiscal_year=fiscal_year,
        reference_contexts=reference_contexts,
        relevant_chunk_ids=relevant_chunk_ids,
        evaluation_type=evaluation_type,
    )


def load_golden_dataset(
    file_path: str | Path,
) -> list[EvaluationExample]:
    """
    Load and validate a golden evaluation dataset from JSONL.

    Each line must contain one complete JSON object.

    Empty relevant_chunk_ids are allowed during initial dataset
    creation. Populate them later with actual indexed chunk IDs.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Golden dataset not found: {path}"
        )

    examples: list[EvaluationExample] = []
    seen_question_ids: set[str] = set()

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {exc.msg}"
                ) from exc

            if not isinstance(data, dict):
                raise ValueError(
                    f"Expected a JSON object on line {line_number}"
                )

            example = _parse_example(data, line_number)

            if example.question_id in seen_question_ids:
                raise ValueError(
                    f"Duplicate question_id "
                    f"'{example.question_id}' on line {line_number}"
                )

            seen_question_ids.add(example.question_id)
            examples.append(example)

    if not examples:
        raise ValueError(
            f"Golden dataset is empty: {path}"
        )

    return examples

def load_dataset(
    file_path: str | Path,
) -> list[EvaluationExample]:
    """Load the golden evaluation dataset."""
    return load_golden_dataset(file_path)