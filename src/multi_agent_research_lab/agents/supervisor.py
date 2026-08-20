"""Supervisor / router agent - decides which worker should run next."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop.

    The supervisor inspects the current state and decides:
    1. If no research has been done -> call Researcher
    2. If research done but no analysis -> call Analyst
    3. If analysis done but no final answer -> call Writer
    4. If everything is complete OR max iterations reached -> stop
    """

    name = "supervisor"

    SYSTEM_PROMPT = """You are a research supervisor coordinating a multi-agent research team.
Your job is to route the next task to the appropriate agent based on the current state.

Routing rules:
- If research_notes is empty or missing -> return "researcher"
- If research exists but analysis_notes is empty -> return "analyst"
- If analysis exists but final_answer is empty -> return "writer"
- If final_answer exists -> return "done" (workflow complete)
- If iteration >= max_iterations -> return "done" (safety limit)

Always prefer making progress over stopping early."""

    def run(self, state: ResearchState) -> ResearchState:
        """Inspect state and decide the next route."""
        from multi_agent_research_lab.services.llm_client import LLMClient

        state.add_trace_event("supervisor_decision", {
            "iteration": state.iteration,
            "has_research": bool(state.research_notes),
            "has_analysis": bool(state.analysis_notes),
            "has_answer": bool(state.final_answer),
        })

        # Use LLM to decide route
        context = self._build_routing_context(state)

        try:
            llm = LLMClient()
            response = llm.complete(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=context,
            )

            # Parse the route from LLM response
            route = response.content.strip().lower()

            # Fallback to rule-based if LLM response is unclear
            if "researcher" in route:
                route = "researcher"
            elif "analyst" in route:
                route = "analyst"
            elif "writer" in route:
                route = "writer"
            else:
                route = self._rule_based_route(state)

        except Exception:
            # Fallback to rule-based routing
            route = self._rule_based_route(state)

        state.record_route(route)

        state.add_trace_event("supervisor_routed", {"route": route})

        return state

    def _build_routing_context(self, state: ResearchState) -> str:
        """Build context string for routing decision."""
        context = f"""Current state:
- Iteration: {state.iteration}
- Request: {state.request.query}
- Has research_notes: {bool(state.research_notes)}
- Has analysis_notes: {bool(state.analysis_notes)}
- Has final_answer: {bool(state.final_answer)}

Route to:"""
        return context

    def _rule_based_route(self, state: ResearchState) -> str:
        """Fallback rule-based routing."""
        if not state.research_notes:
            return "researcher"
        elif not state.analysis_notes:
            return "analyst"
        elif not state.final_answer:
            return "writer"
        return "done"
