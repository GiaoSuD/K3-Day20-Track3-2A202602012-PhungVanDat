"""Optional critic agent for fact-checking and quality review."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent.

    The critic:
    1. Reviews the final answer for accuracy
    2. Checks citation coverage
    3. Identifies potential hallucinations or weak claims
    4. Provides quality assessment
    """

    name = "critic"

    SYSTEM_PROMPT = """You are a critical reviewer. Your task is to:
1. Fact-check the claims in the response against the sources
2. Identify any unsupported or weak claims
3. Check if citations are properly used
4. Flag potential hallucinations or inaccuracies
5. Provide a quality assessment

Be thorough and constructive. Flag issues clearly but suggest improvements."""

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        from multi_agent_research_lab.services.llm_client import LLMClient

        state.add_trace_event("critic_start", {"query": state.request.query})

        if not state.final_answer:
            state.errors.append("No final answer to critique")
            return state

        llm = LLMClient()

        # Build context with final answer and sources
        context = self._build_critique_context(state)

        response = llm.complete(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=context,
        )

        state.add_trace_event("critic_complete", {
            "critique": response.content,
            "tokens_used": response.input_tokens + response.output_tokens if response.input_tokens and response.output_tokens else 0,
        })

        # Append critique to final answer for transparency
        state.final_answer = f"{state.final_answer}\n\n---\n## Quality Review\n\n{response.content}"

        return state

    def _build_critique_context(self, state: ResearchState) -> str:
        """Build context for critique."""
        context_parts = [
            f"Original Query: {state.request.query}",
            "",
            "=== Final Answer to Review ===",
            state.final_answer,
            "",
        ]

        if state.sources:
            context_parts.append("=== Sources ===")
            for i, source in enumerate(state.sources, 1):
                context_parts.append(f"[{i}] {source.title} - {source.snippet}")
            context_parts.append("")

        context_parts.append(
            "Review the final answer against the sources and provide quality feedback."
        )

        return "\n".join(context_parts)
