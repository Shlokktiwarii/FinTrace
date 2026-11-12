from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ragas import SingleTurnSample
from ragas.metrics import (
    AnswerRelevancy,
    Faithfulness,
    FactualCorrectness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
)


@dataclass(frozen=True)
class RagasEvaluationResult:
    """Scores returned by the FinTrace RAGAS evaluation."""

    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    factual_correctness: float

    def to_dict(self) -> dict[str, float]:
        """Convert evaluation scores into a dictionary."""
        return asdict(self)

    @property
    def average_score(self) -> float:
        """Calculate the unweighted average of all five metrics."""
        scores = (
            self.faithfulness,
            self.answer_relevancy,
            self.context_precision,
            self.context_recall,
            self.factual_correctness,
        )

        return sum(scores) / len(scores)


class RagasEvaluator:
    """
    Evaluates FinTrace answers using RAGAS 0.3.1.

    Metrics:
        1. Faithfulness
        2. Answer Relevancy
        3. Context Precision
        4. Context Recall
        5. Factual Correctness

    The evaluator accepts injected metrics for deterministic unit tests.
    """

    def __init__(
        self,
        llm: Any | None = None,
        embeddings: Any | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the evaluator.

        Args:
            llm:
                RAGAS-compatible LLM, such as OpenRouterRagasLLM.

            embeddings:
                RAGAS-compatible embeddings, such as
                FinTraceRagasEmbeddings.

            metrics:
                Optional metric dictionary. Primarily useful for testing.
        """

        if metrics is not None:
            self.metrics = metrics
        else:
            if llm is None:
                raise ValueError(
                    "An LLM must be provided to initialize RAGAS."
                )

            if embeddings is None:
                raise ValueError(
                    "Embeddings must be provided to initialize RAGAS."
                )

            self.metrics = self._build_metrics(
                llm=llm,
                embeddings=embeddings,
            )

        self._validate_metrics()

    @staticmethod
    def _build_metrics(
        llm: Any,
        embeddings: Any,
    ) -> dict[str, Any]:
        """Construct the five RAGAS metrics."""

        return {
            "faithfulness": Faithfulness(
                llm=llm,
            ),
            "answer_relevancy": AnswerRelevancy(
                llm=llm,
                embeddings=embeddings,
            ),
            "context_precision": LLMContextPrecisionWithReference(
                llm=llm,
            ),
            "context_recall": LLMContextRecall(
                llm=llm,
            ),
            "factual_correctness": FactualCorrectness(
                llm=llm,
            ),
        }

    def _validate_metrics(self) -> None:
        """Ensure all required metrics are available."""

        required_metrics = {
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
            "factual_correctness",
        }

        missing_metrics = required_metrics - set(self.metrics)

        if missing_metrics:
            raise ValueError(
                f"Missing RAGAS metrics: {sorted(missing_metrics)}"
            )

    @staticmethod
    def create_sample(
        question: str,
        answer: str,
        retrieved_contexts: list[str],
        reference: str,
        reference_contexts: list[str],
    ) -> SingleTurnSample:
        """
        Construct a RAGAS SingleTurnSample.

        Args:
            question: Original user question.
            answer: Generated FinTrace answer.
            retrieved_contexts: Contexts retrieved by FinTrace.
            reference: Human-verified reference answer.
            reference_contexts: Ground-truth supporting passages.
        """

        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if not answer.strip():
            raise ValueError("Answer cannot be empty.")

        if not retrieved_contexts:
            raise ValueError(
                "Retrieved contexts cannot be empty."
            )

        if not reference.strip():
            raise ValueError("Reference answer cannot be empty.")

        if not reference_contexts:
            raise ValueError(
                "Reference contexts cannot be empty."
            )

        return SingleTurnSample(
            user_input=question,
            response=answer,
            retrieved_contexts=retrieved_contexts,
            reference=reference,
            reference_contexts=reference_contexts,
        )

    async def _score_metric(
        self,
        metric_name: str,
        sample: SingleTurnSample,
    ) -> float:
        """Run one RAGAS metric asynchronously."""

        metric = self.metrics[metric_name]

        score = await metric.single_turn_ascore(sample)

        score = float(score)

        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f"Metric '{metric_name}' returned an invalid "
                f"score: {score}. Expected a value between 0 and 1."
            )

        return score

    async def evaluate_sample(
        self,
        sample: SingleTurnSample,
    ) -> RagasEvaluationResult:
        """
        Evaluate one RAGAS sample using all five metrics.

        Metrics run sequentially to avoid sending several simultaneous
        requests to free OpenRouter models.
        """

        faithfulness = await self._score_metric(
            "faithfulness",
            sample,
        )

        answer_relevancy = await self._score_metric(
            "answer_relevancy",
            sample,
        )

        context_precision = await self._score_metric(
            "context_precision",
            sample,
        )

        context_recall = await self._score_metric(
            "context_recall",
            sample,
        )

        factual_correctness = await self._score_metric(
            "factual_correctness",
            sample,
        )

        return RagasEvaluationResult(
            faithfulness=faithfulness,
            answer_relevancy=answer_relevancy,
            context_precision=context_precision,
            context_recall=context_recall,
            factual_correctness=factual_correctness,
        )

    async def evaluate(
        self,
        question: str,
        answer: str,
        retrieved_contexts: list[str],
        reference: str,
        reference_contexts: list[str],
    ) -> RagasEvaluationResult:
        """
        Convenience method to construct and evaluate a sample.
        """

        sample = self.create_sample(
            question=question,
            answer=answer,
            retrieved_contexts=retrieved_contexts,
            reference=reference,
            reference_contexts=reference_contexts,
        )

        return await self.evaluate_sample(sample)