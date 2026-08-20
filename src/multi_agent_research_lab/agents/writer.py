"""Writer agent - produces final answer from research and analysis."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes.

    The writer:
    1. Reviews research notes and analysis
    2. Synthesizes a clear, coherent response
    3. Includes proper citations and references
    4. Formats output appropriately for the audience
    """

    name = "writer"

    SYSTEM_PROMPT = """You are a technical writer. Your task is to:
1. Synthesize research notes and analysis into a clear response
2. Write in a style appropriate for the target audience
3. Include proper citations and source references
4. Structure the content logically
5. Be concise but comprehensive

Output format:
- Clear, organized sections
- Proper heading hierarchy
- Inline citations [Source X]
- References section at the end"""

    def run(self, state: ResearchState) -> ResearchState:
        """Create the final answer from research and analysis."""
        from multi_agent_research_lab.services.llm_client import LLMClient

        state.add_trace_event("writer_start", {"query": state.request.query})

        llm = LLMClient()

        # Build context from research and analysis
        context = self._build_writing_context(state)

        response = llm.complete(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=context,
        )

        state.final_answer = response.content

        state.add_trace_event("writer_complete", {
            "answer_length": len(response.content),
            "tokens_used": response.input_tokens + response.output_tokens if response.input_tokens and response.output_tokens else 0,
        })

        return state

    def _build_writing_context(self, state: ResearchState) -> str:
        """Build context for writing the final answer."""
        audience = state.request.audience or "technical learners"

        context_parts = [
            f"Research Query: {state.request.query}",
            f"Target Audience: {audience}",
            "",
            "=== Research Notes ===",
            state.research_notes or "No research notes available.",
            "",
            "=== Analysis ===",
            state.analysis_notes or "No analysis available.",
            "",
        ]

        if state.sources:
            context_parts.append("=== Sources ===")
            for i, source in enumerate(state.sources, 1):
                context_parts.append(f"[{i}] {source.title} - {source.url or 'N/A'}")
            context_parts.append("")

        context_parts.append(
            "Write a comprehensive, well-structured response based on the above research and analysis."
        )

        return "\n".join(context_parts)
