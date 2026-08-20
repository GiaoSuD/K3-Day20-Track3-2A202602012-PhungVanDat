"""Researcher agent - collects sources and creates research notes."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes.

    The researcher:
    1. Searches for relevant information using SearchClient
    2. Collects and filters sources
    3. Creates structured research notes with citations
    """

    name = "researcher"

    SYSTEM_PROMPT = """You are a research assistant. Your task is to:
1. Review the search results provided
2. Extract key information relevant to the research query
3. Create concise research notes with proper source citations

Format your notes with:
- Key findings (bullet points)
- Important facts and data
- Source references in brackets [Source: Title]

Keep notes focused and informative."""

    def run(self, state: ResearchState) -> ResearchState:
        """Search for information and create research notes."""
        from multi_agent_research_lab.services.llm_client import LLMClient
        from multi_agent_research_lab.services.search_client import SearchClient

        state.add_trace_event("researcher_start", {"query": state.request.query})

        # Step 1: Search for relevant sources
        search_client = SearchClient()
        sources = search_client.search(
            query=state.request.query,
            max_results=state.request.max_sources,
        )
        state.sources = sources

        # Step 2: Synthesize research notes using LLM
        llm = LLMClient()

        # Build context from sources
        sources_context = self._build_sources_context(sources)

        response = llm.complete(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=f"""Research Query: {state.request.query}

Search Results:
{sources_context}

Create comprehensive research notes based on these results.""",
        )

        state.research_notes = response.content

        state.add_trace_event("researcher_complete", {
            "num_sources": len(sources),
            "notes_length": len(response.content),
            "tokens_used": response.input_tokens + response.output_tokens if response.input_tokens and response.output_tokens else 0,
        })

        return state

    def _build_sources_context(self, sources: list) -> str:
        """Build context string from sources."""
        if not sources:
            return "No sources found."

        context_parts = []
        for i, source in enumerate(sources, 1):
            context_parts.append(
                f"[{i}] {source.title}\n"
                f"URL: {source.url or 'N/A'}\n"
                f"Content: {source.snippet}\n"
            )
        return "\n".join(context_parts)
