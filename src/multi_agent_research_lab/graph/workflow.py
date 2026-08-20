"""LangGraph workflow - orchestrates the multi-agent research system."""

import time
from typing import Literal

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    The workflow follows this pattern:
    1. Supervisor decides which agent should run next
    2. The selected agent performs its task
    3. State is updated and returned to supervisor
    4. Repeat until done or max iterations reached

    Agents:
    - supervisor: Decides routing (researcher -> analyst -> writer -> done)
    - researcher: Searches and collects information
    - analyst: Analyzes research and creates insights
    - writer: Produces final answer
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._supervisor = SupervisorAgent()
        self._researcher = ResearcherAgent()
        self._analyst = AnalystAgent()
        self._writer = WriterAgent()

    def build(self) -> object:
        """Create a LangGraph graph.

        This implementation uses a simple sequential pattern with supervisor routing.
        For production, you would use LangGraph's StateGraph for more complex flows.
        """
        # This is a simplified implementation
        # Full LangGraph implementation would use:
        # - StateGraph with ResearchState
        # - Nodes for each agent
        # - Conditional edges based on supervisor routing
        return self

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the workflow and return final state.

        The workflow:
        1. Start with supervisor routing decision
        2. Execute the selected agent
        3. Repeat until done or max iterations
        """
        start_time = time.time()
        state.add_trace_event("workflow_start", {"query": state.request.query})

        max_iterations = self._settings.max_iterations

        while state.iteration < max_iterations:
            # Step 1: Ask supervisor for routing decision
            state = self._supervisor.run(state)

            route = state.route_history[-1] if state.route_history else "unknown"

            state.add_trace_event("route_decision", {"route": route, "iteration": state.iteration})

            # Step 2: Execute the selected agent
            if route == "done":
                state.add_trace_event("workflow_complete", {
                    "reason": "done",
                    "total_iterations": state.iteration,
                    "total_time": time.time() - start_time,
                })
                break

            elif route == "researcher":
                state = self._researcher.run(state)

            elif route == "analyst":
                state = self._analyst.run(state)

            elif route == "writer":
                state = self._writer.run(state)

                # Writer completes the workflow
                state.add_trace_event("workflow_complete", {
                    "reason": "writer_complete",
                    "total_iterations": state.iteration,
                    "total_time": time.time() - start_time,
                })
                break

            else:
                state.errors.append(f"Unknown route: {route}")
                break

        else:
            # Max iterations reached
            state.add_trace_event("workflow_complete", {
                "reason": "max_iterations",
                "total_iterations": state.iteration,
                "total_time": time.time() - start_time,
            })

        return state
