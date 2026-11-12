from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI, OpenAI
from langchain_core.outputs import Generation, LLMResult
from langchain_core.prompt_values import PromptValue
from ragas.llms.base import BaseRagasLLM


@dataclass
class OpenRouterRagasLLM(BaseRagasLLM):
    """RAGAS-compatible LLM backed by OpenRouter."""

    api_key: str = ""
    model: str = "openrouter/free"
    base_url: str = "https://openrouter.ai/api/v1"
    timeout: float = 90.0
    max_tokens: int = 4096
    temperature: float = 0.0

    _sync_client: Any = field(init=False, repr=False, default=None)
    _async_client: Any = field(init=False, repr=False, default=None)

    def __post_init__(self) -> None:
        super().__post_init__()

        if not self.api_key:
            raise ValueError("OpenRouter API key is required.")

        if not self.model:
            raise ValueError("OpenRouter model is required.")

        self._sync_client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=2,
        )

        self._async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=2,
        )

    @staticmethod
    def _prompt_text(prompt: PromptValue) -> str:
        return prompt.to_string()

    def _request_kwargs(
        self,
        prompt: PromptValue,
        temperature: float | None,
        stop: list[str] | None,
    ) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": self._prompt_text(prompt),
                }
            ],
            "temperature": (
                self.temperature if temperature is None else temperature
            ),
            "max_tokens": self.max_tokens,
            **({"stop": stop} if stop else {}),
        }

    def generate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float = 0.01,
        stop: list[str] | None = None,
        callbacks: Any = None,
    ) -> LLMResult:
        """Synchronous generation."""

        generations: list[Generation] = []

        for _ in range(n):
            response = self._sync_client.chat.completions.create(
                **self._request_kwargs(prompt, temperature, stop)
            )

            content = response.choices[0].message.content

            if not content or not content.strip():
                raise RuntimeError(
                    "OpenRouter returned an empty response to RAGAS."
                )

            generations.append(
                Generation(
                    text=content.strip(),
                    generation_info={
                        "finish_reason": response.choices[0].finish_reason
                    },
                )
            )

        return LLMResult(generations=[generations])

    async def agenerate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float | None = 0.01,
        stop: list[str] | None = None,
        callbacks: Any = None,
    ) -> LLMResult:
        """Asynchronous generation used by RAGAS metrics."""

        generations: list[Generation] = []

        for _ in range(n):
            response = await self._async_client.chat.completions.create(
                **self._request_kwargs(prompt, temperature, stop)
            )

            content = response.choices[0].message.content

            if not content or not content.strip():
                raise RuntimeError(
                    "OpenRouter returned an empty response to RAGAS."
                )

            generations.append(
                Generation(
                    text=content.strip(),
                    generation_info={
                        "finish_reason": response.choices[0].finish_reason
                    },
                )
            )

        return LLMResult(generations=[generations])

    def is_finished(self, response: LLMResult) -> bool:
        """Check whether the model returned completed, non-empty output."""

        try:
            for generation_list in response.generations:
                for generation in generation_list:
                    if not generation.text.strip():
                        return False

                    finish_reason = (
                        generation.generation_info or {}
                    ).get("finish_reason")

                    if finish_reason in {"length", "content_filter"}:
                        return False

            return True
        except (AttributeError, TypeError):
            return False

    async def aclose(self) -> None:
        await self._async_client.close()

    def close(self) -> None:
        self._sync_client.close()