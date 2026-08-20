"""Command-line entrypoint for the lab starter."""

import time
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _parse_query(query: str) -> ResearchQuery:
    try:
        return ResearchQuery(query=query)
    except ValidationError as exc:
        console.print(
            Panel.fit(
                f"Invalid query: {exc.errors()[0]['msg']}",
                title="Input Error",
                style="red",
            )
        )
        raise typer.Exit(code=1) from exc


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output file")] = None,
) -> None:
    """Run a single-agent baseline using a single LLM call.

    This demonstrates the simplest approach: one agent does everything.
    """
    _init()
    request = _parse_query(query)

    console.print(Panel.fit("[bold cyan]Single-Agent Baseline[/bold cyan]", title="Mode"))
    console.print(f"Query: {query}\n")

    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Researching...", total=None)

        try:
            llm = LLMClient()
            response = llm.complete(
                system_prompt="""You are a research assistant. Answer the user's question thoroughly
with proper structure and citations. Write in a clear, informative style.""",
                user_prompt=f"Research and write about: {query}",
            )

            elapsed = time.time() - start_time

            console.print(Panel.fit(
                response.content,
                title=f"Single-Agent Response (took {elapsed:.2f}s)",
            ))

            # Show metrics
            if response.input_tokens and response.output_tokens:
                console.print(f"\n[dim]Tokens: {response.input_tokens} in / {response.output_tokens} out[/dim]")
            if response.cost_usd:
                console.print(f"[dim]Est. cost: ${response.cost_usd:.4f}[/dim]")

            # Save to output file if specified
            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(f"# Single-Agent Baseline\n\n")
                    f.write(f"Query: {query}\n")
                    f.write(f"Time: {elapsed:.2f}s\n")
                    if response.input_tokens and response.output_tokens:
                        f.write(f"Tokens: {response.input_tokens} in / {response.output_tokens} out\n")
                    if response.cost_usd:
                        f.write(f"Cost: ${response.cost_usd:.4f}\n\n")
                    f.write("## Response\n\n")
                    f.write(response.content)
                console.print(f"\n[green]Saved to {output}[/green]")

        except Exception as exc:
            console.print(Panel.fit(
                f"Error: {exc}",
                title="Execution Error",
                style="red",
            ))
            raise typer.Exit(code=1) from exc


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output file")] = None,
) -> None:
    """Run the multi-agent workflow with Supervisor + Researcher + Analyst + Writer.

    This demonstrates the multi-agent approach with specialized roles.
    """
    _init()
    state = ResearchState(request=_parse_query(query))

    console.print(Panel.fit("[bold cyan]Multi-Agent Workflow[/bold cyan]", title="Mode"))
    console.print(f"Query: {query}\n")

    workflow = MultiAgentWorkflow()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Running workflow...", total=None)

            result = workflow.run(state)

        # Display results
        console.print("\n[bold green]=== Workflow Complete ===[/bold green]\n")
        console.print(f"Total iterations: {result.iteration}")
        console.print(f"Route history: {' → '.join(result.route_history)}")

        if result.final_answer:
            console.print(Panel.fit(
                result.final_answer,
                title="Final Answer",
            ))

        # Show trace summary
        if result.trace:
            console.print("\n[bold]Execution Trace:[/bold]")
            for event in result.trace:
                name = event.get("name", "unknown")
                console.print(f"  • {name}")

        # Save to output file if specified
        if output:
            import json
            with open(output, "w", encoding="utf-8") as f:
                f.write(f"# Multi-Agent Workflow\n\n")
                f.write(f"Query: {query}\n")
                f.write(f"Iterations: {result.iteration}\n")
                f.write(f"Route history: {' → '.join(result.route_history)}\n\n")
                if result.final_answer:
                    f.write("## Final Answer\n\n")
                    f.write(result.final_answer)
                f.write("\n\n## Trace\n\n")
                json.dump(result.trace, f, indent=2)
            console.print(f"\n[green]Saved to {output}[/green]")

    except Exception as exc:
        console.print(Panel.fit(
            f"Error: {exc}",
            title="Execution Error",
            style="red",
        ))
        raise typer.Exit(code=1) from exc


@app.command()
def compare(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
    output: Annotated[str, typer.Option("--output", "-o", help="Output file")] = "benchmark_report.md",
) -> None:
    """Run both baseline and multi-agent, then generate a comparison report."""
    _init()
    console.print(Panel.fit("[bold cyan]Benchmark Comparison[/bold cyan]", title="Mode"))

    baseline_start = time.time()
    baseline_state = ResearchState(request=_parse_query(query))

    # Run baseline
    with console.status("[bold green]Running baseline..."):
        try:
            llm = LLMClient()
            baseline_response = llm.complete(
                system_prompt="You are a research assistant. Answer thoroughly.",
                user_prompt=f"Research and write about: {query}",
            )
        except Exception as exc:
            console.print(f"[red]Baseline failed: {exc}[/red]")
            raise typer.Exit(code=1) from exc

    baseline_time = time.time() - baseline_start

    # Run multi-agent
    multi_start = time.time()
    multi_state = ResearchState(request=_parse_query(query))
    workflow = MultiAgentWorkflow()

    with console.status("[bold green]Running multi-agent workflow..."):
        try:
            multi_result = workflow.run(multi_state)
        except Exception as exc:
            console.print(f"[red]Multi-agent failed: {exc}[/red]")
            raise typer.Exit(code=1) from exc

    multi_time = time.time() - multi_start

    # Generate report
    report = f"""# Benchmark Report: Single-Agent vs Multi-Agent

## Query
{query}

## Results Summary

| Metric | Single-Agent Baseline | Multi-Agent |
|--------|----------------------|--------------|
| Total Time | {baseline_time:.2f}s | {multi_time:.2f}s |
| Tokens In | {baseline_response.input_tokens or 'N/A'} | N/A (see trace) |
| Tokens Out | {baseline_response.output_tokens or 'N/A'} | N/A (see trace) |
| Est. Cost | ${baseline_response.cost_usd or 0:.4f} | N/A |
| Iterations | 1 | {multi_result.iteration} |
| Route | direct | {' → '.join(multi_result.route_history)} |

## Analysis

### Single-Agent Approach
- **Pros**: Simpler, faster for simple queries, lower overhead
- **Cons**: One agent handles everything, harder to debug, less specialized

### Multi-Agent Approach
- **Pros**: Specialized roles, better separation of concerns, easier to debug
- **Cons**: More overhead, more complex, higher latency

## Conclusion
{'Multi-agent is faster' if multi_time < baseline_time else 'Single-agent is faster'} for this query.
{'Multi-agent is cheaper' if (baseline_response.cost_usd or 0) > 0 else 'Cost comparison requires token tracking'}.

---
*Report generated automatically*
"""

    with open(output, "w", encoding="utf-8") as f:
        f.write(report)

    console.print(f"\n[green]Report saved to {output}[/green]")
    console.print(Panel.fit(report, title="Benchmark Report"))


if __name__ == "__main__":
    app()
