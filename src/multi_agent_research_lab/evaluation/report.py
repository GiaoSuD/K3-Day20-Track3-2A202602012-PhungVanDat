"""Benchmark report rendering with rich analysis."""

from typing import Any

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to a comprehensive markdown report.

    Args:
        metrics: List of BenchmarkMetrics from different runs

    Returns:
        Formatted markdown report string
    """
    if not metrics:
        return "# Benchmark Report\n\nNo metrics collected yet.\n"

    # Group metrics by run type
    baseline_metrics = [m for m in metrics if "baseline" in m.run_name.lower()]
    multi_metrics = [m for m in metrics if "multi" in m.run_name.lower()]

    lines = [
        "# 📊 Benchmark Report: Single-Agent vs Multi-Agent",
        "",
        "## Executive Summary",
        "",
        _generate_summary_table(baseline_metrics, multi_metrics),
        "",
        "## Detailed Metrics",
        "",
    ]

    # Individual run details
    for metric in metrics:
        lines.append(f"### {metric.run_name}")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Latency | {metric.latency_seconds:.2f}s |")
        if metric.estimated_cost_usd is not None:
            lines.append(f"| Est. Cost | ${metric.estimated_cost_usd:.6f} |")
        if metric.quality_score is not None:
            lines.append(f"| Quality Score | {metric.quality_score:.1f}/10 |")
        if metric.citation_coverage is not None:
            lines.append(f"| Citation Coverage | {metric.citation_coverage:.0%} |")
        if metric.failure_rate is not None:
            lines.append(f"| Failure Rate | {metric.failure_rate:.0%} |")
        if metric.notes:
            lines.append(f"| Notes | {metric.notes} |")
        lines.append("")

    # Analysis section
    lines.extend([
        "## Analysis",
        "",
        _generate_analysis(baseline_metrics, multi_metrics),
        "",
        "## Recommendations",
        "",
        _generate_recommendations(baseline_metrics, multi_metrics),
        "",
        "---",
        "*Report generated automatically by Multi-Agent Research Lab*",
    ])

    return "\n".join(lines)


def _generate_summary_table(
    baseline_metrics: list[BenchmarkMetrics],
    multi_metrics: list[BenchmarkMetrics],
) -> str:
    """Generate summary comparison table."""
    def avg(metrics: list[BenchmarkMetrics], attr: str) -> str:
        values = [getattr(m, attr) for m in metrics if getattr(m, attr) is not None]
        if not values:
            return "N/A"
        return f"{sum(values) / len(values):.2f}"

    def compare_latency(baseline_val: str, multi_val: str) -> str:
        try:
            b = float(baseline_val.rstrip('s'))
            m = float(multi_val.rstrip('s'))
            return 'Single' if b < m else 'Multi'
        except ValueError:
            return '-'

    table = [
        "| Metric | Single-Agent | Multi-Agent | Winner |",
        "|--------|--------------|-------------|--------|",
        f"| Avg Latency | {avg(baseline_metrics, 'latency_seconds')}s | {avg(multi_metrics, 'latency_seconds')}s | {compare_latency(avg(baseline_metrics, 'latency_seconds'), avg(multi_metrics, 'latency_seconds'))} |",
        f"| Avg Cost | ${avg(baseline_metrics, 'estimated_cost_usd')} | ${avg(multi_metrics, 'estimated_cost_usd')} | - |",
        f"| Citation Coverage | {avg(baseline_metrics, 'citation_coverage')} | {avg(multi_metrics, 'citation_coverage')} | - |",
        f"| Failure Rate | {avg(baseline_metrics, 'failure_rate')} | {avg(multi_metrics, 'failure_rate')} | - |",
    ]
    return "\n".join(table)


def _generate_analysis(
    baseline_metrics: list[BenchmarkMetrics],
    multi_metrics: list[BenchmarkMetrics],
) -> str:
    """Generate analysis text based on metrics."""
    analysis_parts = []

    # Latency analysis
    baseline_latency = [m.latency_seconds for m in baseline_metrics if m.latency_seconds]
    multi_latency = [m.latency_seconds for m in multi_metrics if m.latency_seconds]

    if baseline_latency and multi_latency:
        avg_baseline = sum(baseline_latency) / len(baseline_latency)
        avg_multi = sum(multi_latency) / len(multi_latency)

        if avg_baseline < avg_multi:
            analysis_parts.append(
                f"**Latency**: Single-agent is {avg_multi / avg_baseline:.1f}x faster than multi-agent. "
                f"This is expected because multi-agent has coordination overhead."
            )
        else:
            analysis_parts.append(
                f"**Latency**: Multi-agent is {avg_baseline / avg_multi:.1f}x faster. "
                f"This suggests parallel processing is effective."
            )

    # Cost analysis
    baseline_cost = [m.estimated_cost_usd for m in baseline_metrics if m.estimated_cost_usd]
    multi_cost = [m.estimated_cost_usd for m in multi_metrics if m.estimated_cost_usd]

    if baseline_cost and multi_cost:
        avg_baseline_cost = sum(baseline_cost) / len(baseline_cost)
        avg_multi_cost = sum(multi_cost) / len(multi_cost)

        if avg_baseline_cost < avg_multi_cost:
            analysis_parts.append(
                f"**Cost**: Single-agent is more cost-effective (${avg_baseline_cost:.6f} vs ${avg_multi_cost:.6f}). "
                f"Fewer LLM calls mean lower API costs."
            )
        else:
            analysis_parts.append(
                f"**Cost**: Multi-agent is more cost-effective. This may indicate efficient task distribution."
            )

    # Citation coverage analysis
    baseline_citation = [m.citation_coverage for m in baseline_metrics if m.citation_coverage is not None]
    multi_citation = [m.citation_coverage for m in multi_metrics if m.citation_coverage is not None]

    if baseline_citation and multi_citation:
        avg_baseline_cite = sum(baseline_citation) / len(baseline_citation)
        avg_multi_cite = sum(multi_citation) / len(multi_citation)

        analysis_parts.append(
            f"**Citation Coverage**: Multi-agent ({avg_multi_cite:.0%}) vs Single-agent ({avg_baseline_cite:.0%}). "
            f"Specialized agents may produce better-cited content."
        )

    if not analysis_parts:
        return "Not enough data for detailed analysis. Run more benchmarks to gather statistics."

    return "\n\n".join(analysis_parts)


def _generate_recommendations(
    baseline_metrics: list[BenchmarkMetrics],
    multi_metrics: list[BenchmarkMetrics],
) -> str:
    """Generate recommendations based on analysis."""
    recommendations = [
        "### When to Use Single-Agent",
        "- Simple, straightforward queries",
        "- Speed is critical",
        "- Limited API budget",
        "- When specialized research isn't needed",
        "",
        "### When to Use Multi-Agent",
        "- Complex queries requiring deep research",
        "- When quality and citations matter",
        "- When explainability and traceability are important",
        "- When different aspects (research, analysis, writing) need distinct expertise",
    ]
    return "\n".join(recommendations)


def render_json_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render metrics as JSON for programmatic consumption."""
    import json
    return json.dumps([m.model_dump() for m in metrics], indent=2)
