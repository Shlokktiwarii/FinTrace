import re

from fintrace.generation.models import GeneratedAnswer
from fintrace.verification.models import Claim


CITATION_PATTERN = re.compile(
    r"\[([A-Za-z][A-Za-z0-9_-]*)\]"
)

SENTENCE_PATTERN = re.compile(
    r"(?<=[.!?])\s+|\n+"
)


class ClaimExtractor:
    """Extract sentence-level claims and their inline citations."""

    def extract(
        self,
        answer: GeneratedAnswer,
    ) -> tuple[Claim, ...]:
        if answer.abstained:
            return ()

        structured_citation_ids = {
            citation.evidence_id
            for citation in answer.citations
        }

        claims: list[Claim] = []

        sentences = SENTENCE_PATTERN.split(answer.answer.strip())

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            citation_ids = tuple(
                dict.fromkeys(
                    CITATION_PATTERN.findall(sentence)
                )
            )

            claim_text = CITATION_PATTERN.sub("", sentence)
            claim_text = claim_text.strip()
            claim_text = claim_text.rstrip(" \t\n-•.!?").strip()

            if not claim_text:
                continue

            # If a single structured citation exists and the sentence
            # has no inline citation, associate that citation.
            if not citation_ids and len(structured_citation_ids) == 1:
                citation_ids = tuple(structured_citation_ids)

            claims.append(
                Claim(
                    claim_id=f"C{len(claims) + 1}",
                    text=claim_text,
                    citation_ids=citation_ids,
                )
            )

        return tuple(claims)