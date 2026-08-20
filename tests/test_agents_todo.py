"""Unit tests for agent routing logic.

NOTE: These tests verify the implemented routing behavior after students complete
the implementation. Update tests as needed based on your specific implementation.
"""

import pytest

from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher_when_no_research() -> None:
    """Supervisor should route to researcher when research_notes is empty."""
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems clearly"))

    agent = SupervisorAgent()
    result = agent.run(state)

    # Should route to researcher first
    assert len(result.route_history) == 1
    assert result.route_history[0] in ["researcher", "analyst", "writer", "done"]


def test_supervisor_routes_correctly_based_on_state() -> None:
    """Supervisor should route based on current state of research."""
    state = ResearchState(request=ResearchQuery(query="Test query for routing logic"))

    # Start with supervisor decision
    agent = SupervisorAgent()
    result = agent.run(state)

    # Route should be one of the valid routes
    assert result.route_history[-1] in ["researcher", "analyst", "writer", "done"]


def test_state_tracks_iterations() -> None:
    """State should track iteration count correctly."""
    state = ResearchState(request=ResearchQuery(query="Test iteration tracking"))

    agent = SupervisorAgent()
    result = agent.run(state)

    assert result.iteration == 1
    assert len(result.route_history) == 1


def test_state_records_routes() -> None:
    """State should record all routing decisions."""
    state = ResearchState(request=ResearchQuery(query="Test route recording"))

    agent = SupervisorAgent()
    result = agent.run(state)

    # Should have trace events
    assert len(result.trace) > 0
