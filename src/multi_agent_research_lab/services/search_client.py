"""Search client abstraction for ResearcherAgent."""

from typing import Any

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Search client using Tavily API or mock fallback."""

    def __init__(self) -> None:
        settings = get_settings()
        self._tavily_key = settings.tavily_api_key
        self._max_results = 5

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Uses Tavily API if available, otherwise falls back to mock data.
        """
        if self._tavily_key:
            try:
                return self._search_tavily(query, max_results)
            except Exception:
                # If Tavily fails, fall back to mock
                return self._search_mock(query, max_results)
        return self._search_mock(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        """Search using Tavily API."""
        try:
            from tavily import TavilyClient
        except ImportError:
            # Fall back to mock if package not installed
            return self._search_mock(query, max_results)

        client = TavilyClient(api_key=self._tavily_key)
        results = client.search(query=query, max_results=max_results)

        sources = []
        for item in results.get("results", []):
            sources.append(
                SourceDocument(
                    title=item.get("title", "Untitled"),
                    url=item.get("url"),
                    snippet=item.get("content", ""),
                    metadata={"score": item.get("score", 0), "engine": "tavily"},
                )
            )
        return sources

    def _search_mock(self, query: str, max_results: int) -> list[SourceDocument]:
        """Mock search for demo/testing when no API key is available.

        Returns generic research sources for any query.
        """
        mock_sources = [
            SourceDocument(
                title=f"Overview: {query}",
                url="https://example.com/research",
                snippet=f"Comprehensive overview of {query} covering key concepts, "
                f"applications, and current developments in the field.",
                metadata={"engine": "mock", "note": "Configure TAVILY_API_KEY for real search"},
            ),
            SourceDocument(
                title=f"Technical Deep Dive: {query}",
                url="https://example.com/technical",
                snippet=f"Technical analysis of {query} including architecture details, "
                f"implementation considerations, and best practices.",
                metadata={"engine": "mock"},
            ),
            SourceDocument(
                title=f"Research Trends: {query}",
                url="https://example.com/trends",
                snippet=f"Current research trends and future directions for {query}, "
                f"including recent papers, conferences, and emerging applications.",
                metadata={"engine": "mock"},
            ),
        ]
        return mock_sources[:max_results]
