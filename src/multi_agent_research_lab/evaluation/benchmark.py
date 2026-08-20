"""Benchmark for single-agent vs multi-agent comparison."""

import re
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and compute metrics for a workflow run.

    Metrics collected:
    - Latency: wall-clock time in seconds
    - Token usage: estimated from state trace
    - Citation coverage: ratio of cited claims to total claims
    - Error rate: presence of errors in state

    Args:
        run_name: Name identifier for this benchmark run
        query: The research query to test
        runner: Function that executes the workflow and returns state

    Returns:
        Tuple of (ResearchState, BenchmarkMetrics)
    """
    started = perf_counter()

    try:
        state = runner(query)
        latency = perf_counter() - started

        # Extract token counts from trace
        total_tokens = 0
        for event in state.trace:
            if "tokens_used" in event.get("payload", {}):
                total_tokens += event["payload"]["tokens_used"]

        # Calculate citation coverage
        citation_coverage = _calculate_citation_coverage(state.final_answer or "")

        # Determine failure rate
        failure_rate = 1.0 if state.errors else 0.0

        metrics = BenchmarkMetrics(
            run_name=run_name,
            latency_seconds=latency,
            estimated_cost_usd=total_tokens * 0.00000015,  # Rough estimate for gpt-4o-mini
            citation_coverage=citation_coverage,
            failure_rate=failure_rate,
            notes=f"Iterations: {state.iteration}, Route: {' → '.join(state.route_history)}" if state.route_history else "",
        )

        return state, metrics

    except Exception as e:
        latency = perf_counter() - started
        metrics = BenchmarkMetrics(
            run_name=run_name,
            latency_seconds=latency,
            failure_rate=1.0,
            notes=f"Error: {str(e)[:100]}",
        )
        # Return empty state for error case
        empty_state = ResearchState(request=lambda: None)  # type: ignore
        return empty_state, metrics


def _calculate_citation_coverage(text: str) -> float:
    """Calculate the ratio of cited claims to total claims.

    A claim is identified as a sentence ending with a period.
    Citation patterns: [Source X], (Source X), or footnote markers.
    """
    if not text:
        return 0.0

    # Split into sentences (rough approximation)
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return 0.0

    # Count sentences with citations
    cited_patterns = [
        r"\[Source",
        r"\[.*\]",  # Generic bracket citations
        r"source:",  # "Source: ..."
        r"according to",
    ]

    cited_count = 0
    for sentence in sentences:
        if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in cited_patterns):
            cited_count += 1

    return cited_count / len(sentences)


def run_comparative_benchmark(
    query: str,
    baseline_runner: Runner,
    multi_runner: Runner,
) -> tuple[ResearchState, BenchmarkMetrics, ResearchState, BenchmarkMetrics]:
    """Run both baseline and multi-agent workflows and compare.

    Args:
        query: Research query to test
        baseline_runner: Single-agent baseline runner
        multi_runner: Multi-agent workflow runner

    Returns:
        Tuple of (baseline_state, baseline_metrics, multi_state, multi_metrics)
    """
    print(f"Running benchmark for query: {query[:50]}...")

    print("  Running baseline...")
    baseline_state, baseline_metrics = run_benchmark("baseline", query, baseline_runner)

    print("  Running multi-agent...")
    multi_state, multi_metrics = run_benchmark("multi-agent", query, multi_runner)

    return baseline_state, baseline_metrics, multi_state, multi_metrics
