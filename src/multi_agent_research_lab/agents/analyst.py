"""Analyst agent - turns research notes into structured insights."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights.

    The analyst:
    1. Reviews research notes and sources
    2. Extracts key claims and compares viewpoints
    3. Identifies patterns, relationships, and insights
    4. Flags weak evidence and knowledge gaps
    5. Creates structured analysis notes
    """

    name = "analyst"

    SYSTEM_PROMPT = """You are a research analyst. Your task is to:
1. Review the research notes and identify key themes
2. Extract and compare different viewpoints
3. Identify patterns, relationships, and trends
4. Flag weak evidence, contradictions, or gaps
5. Provide structured analytical insights

Format your analysis with:
- Key Insights (numbered list)
- Viewpoints Comparison (pros/cons)
- Evidence Quality Assessment
- Knowledge Gaps / Limitations
- Recommendations for further research

Be critical and thorough in your analysis."""

    def run(self, state: ResearchState) -> ResearchState:
        """Analyze research notes and create structured insights."""
        from multi_agent_research_lab.services.llm_client import LLMClient

        state.add_trace_event("analyst_start", {"query": state.request.query})

        if not state.research_notes:
            state.analysis_notes = "No research notes available for analysis."
            return state

        llm = LLMClient()

        # Build context with research notes and sources
        context = self._build_analysis_context(state)

        response = llm.complete(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=context,
        )

        state.analysis_notes = response.content

        state.add_trace_event("analyst_complete", {
            "notes_length": len(response.content),
            "tokens_used": response.input_tokens + response.output_tokens if response.input_tokens and response.output_tokens else 0,
        })

        return state

    def _build_analysis_context(self, state: ResearchState) -> str:
        """Build context string for analysis."""
        context_parts = [
            f"Research Query: {state.request.query}",
            "",
            "=== Research Notes ===",
            state.research_notes or "No research notes available.",
            "",
        ]

        if state.sources:
            context_parts.append("=== Sources ===")
            for i, source in enumerate(state.sources, 1):
                context_parts.append(f"[{i}] {source.title}: {source.snippet}")
            context_parts.append("")

        context_parts.append(
            "Provide a structured analysis of the research above."
        )

        return "\n".join(context_parts)
