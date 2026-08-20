"""Tracing hooks with LangSmith support.

This module provides tracing capabilities that can be used by all agents.
LangSmith is enabled when LANGSMITH_API_KEY is configured.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any
from time import perf_counter

from multi_agent_research_lab.core.config import get_settings


@lru_cache(maxsize=1)
def _get_langsmith_client():
    """Get LangSmith client if configured."""
    settings = get_settings()
    if not settings.langsmith_api_key:
        return None

    try:
        from langsmith import Client

        return Client(
            api_key=settings.langsmith_api_key,
            project_name=settings.langsmith_project,
        )
    except ImportError:
        return None


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    run_type: str = "chain",
) -> Iterator[dict[str, Any]]:
    """Context manager for tracing spans.

    When LangSmith is configured, this creates a proper trace.
    Otherwise, it falls back to a simple timing context.

    Args:
        name: Name of the span (e.g., "researcher", "analyst")
        attributes: Optional metadata for the span
        run_type: Type of run (chain, tool, llm, etc.)

    Yields:
        A span dictionary that can be updated with results
    """
    span: dict[str, Any] = {
        "name": name,
        "attributes": attributes or {},
        "duration_seconds": None,
    }

    # Try to use LangSmith if available
    client = _get_langsmith_client()

    if client:
        # Use LangSmith tracing
        with client.trace(
            name=name,
            run_type=run_type,
            metadata=attributes or {},
        ) as langsmith_span:
            started = perf_counter()
            try:
                yield span
            finally:
                span["duration_seconds"] = perf_counter() - started
                langsmith_span.end()
    else:
        # Fallback to simple timing
        started = perf_counter()
        try:
            yield span
        finally:
            span["duration_seconds"] = perf_counter() - started


def trace_llm_call(
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    response: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Record an LLM call in the trace.

    Args:
        agent_name: Name of the agent making the call
        system_prompt: System prompt used
        user_prompt: User prompt used
        response: Model response
        metadata: Additional metadata (tokens, cost, etc.)
    """
    client = _get_langsmith_client()

    span_data = {
        "agent": agent_name,
        "system_prompt_length": len(system_prompt),
        "user_prompt_length": len(user_prompt),
        "response_length": len(response),
    }

    if metadata:
        span_data.update(metadata)

    if client:
        # Log to LangSmith
        client.create_run(
            name=f"{agent_name}_llm",
            run_type="llm",
            inputs={
                "system": system_prompt[:500],  # Truncate for storage
                "user": user_prompt[:500],
            },
            outputs={"response": response[:500]},
            metadata=span_data,
        )
