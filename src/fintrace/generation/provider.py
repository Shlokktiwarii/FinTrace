from typing import Protocol


class LLMProvider(Protocol):
    """Interface for a language model used by FinTrace."""

    def generate(self, prompt: str) -> str:
        """Generate a response from a complete prompt."""
        ...