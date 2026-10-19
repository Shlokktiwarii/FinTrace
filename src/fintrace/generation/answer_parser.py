import json
import re

from fintrace.generation.models import Citation, Evidence, GeneratedAnswer


_CITATION_PATTERN = re.compile(r"\[(E\d+)\]")


class AnswerParser:
    """Parse structured LLM output and validate evidence references."""

    def parse(
        self,
        question: str,
        response: str,
        evidence: list[Evidence],
    ) -> GeneratedAnswer:
        try:
            payload = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM response must be valid JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise ValueError("LLM response must be a JSON object")

        answer = payload.get("answer")
        citation_ids = payload.get("citation_ids")
        abstained = payload.get("abstained")

        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Answer must be a non-empty string")

        if not isinstance(citation_ids, list):
            raise ValueError("citation_ids must be a list")

        if not all(
            isinstance(item, str)
            for item in citation_ids
        ):
            raise ValueError("Every citation ID must be a string")

        if not isinstance(abstained, bool):
            raise ValueError("abstained must be a boolean")

        allowed_ids = {item.evidence_id for item in evidence}

        if len(citation_ids) != len(set(citation_ids)):
            raise ValueError("Duplicate citation IDs are not allowed")

        invalid_ids = set(citation_ids) - allowed_ids

        if invalid_ids:
            raise ValueError(
                f"Unknown evidence IDs: {sorted(invalid_ids)}"
            )

        # Every inline citation must refer to supplied evidence.
        inline_ids = set(_CITATION_PATTERN.findall(answer))

        if inline_ids - allowed_ids:
            raise ValueError(
                "Answer contains references to unknown evidence IDs"
            )

        # Ensure structured citation metadata covers inline citations.
        if not inline_ids.issubset(set(citation_ids)):
            raise ValueError(
                "Inline citations are missing from citation_ids"
            )

        if abstained and citation_ids:
            raise ValueError(
                "Abstained answers must not claim supporting citations"
            )

        return GeneratedAnswer(
            question=question,
            answer=answer.strip(),
            citations=tuple(
                Citation(evidence_id=item)
                for item in citation_ids
            ),
            abstained=abstained,
        )