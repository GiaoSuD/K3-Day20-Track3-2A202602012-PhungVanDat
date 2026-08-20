"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client using OpenAI."""

    # Token pricing per 1M tokens (gpt-4o-mini)
    COST_PER_MILLION_INPUT = 0.15
    COST_PER_MILLION_OUTPUT = 0.60

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise StudentTodoError(
                "OPENAI_API_KEY not set. Please configure your .env file."
            )
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion with retry, timeout, and token logging.

        Args:
            system_prompt: The system instructions for the agent role.
            user_prompt: The user's query or task description.

        Returns:
            LLMResponse with content and usage metrics.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        settings = get_settings()

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            timeout=settings.timeout_seconds,
        )

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None

        # Calculate cost
        cost = None
        if input_tokens and output_tokens:
            cost = (
                input_tokens / 1_000_000 * self.COST_PER_MILLION_INPUT
                + output_tokens / 1_000_000 * self.COST_PER_MILLION_OUTPUT
            )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
