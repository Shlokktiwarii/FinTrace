from fintrace.generation.answer_parser import AnswerParser
from fintrace.generation.models import GeneratedAnswer
from fintrace.generation.prompt_builder import EvidencePromptBuilder
from fintrace.generation.provider import LLMProvider
from fintrace.retrieval.models import SearchResult


class GenerationService:
    """Generate answers grounded in retrieved evidence."""

    def __init__(
        self,
        provider: LLMProvider,
        prompt_builder: EvidencePromptBuilder | None = None,
        answer_parser: AnswerParser | None = None,
    ) -> None:
        self._provider = provider
        self._prompt_builder = (
            prompt_builder or EvidencePromptBuilder()
        )
        self._answer_parser = answer_parser or AnswerParser()

    def answer(
        self,
        question: str,
        results: list[SearchResult],
    ) -> GeneratedAnswer:
        if not question.strip():
            raise ValueError("Question must not be empty")

        evidence = self._prompt_builder.build_evidence(results)

        # Fail closed when retrieval supplies no evidence.
        if not evidence:
            return GeneratedAnswer(
                question=question,
                answer=(
                    "The available evidence is insufficient "
                    "to answer this question."
                ),
                citations=(),
                abstained=True,
            )

        prompt = self._prompt_builder.build_prompt(
            question=question,
            evidence=evidence,
        )

        response = self._provider.generate(prompt)

        return self._answer_parser.parse(
            question=question,
            response=response,
            evidence=evidence,
        )