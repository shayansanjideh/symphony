"""Planner agent — explores codebase and produces a specification."""

from agents.base import BaseAgent


class PlannerAgent(BaseAgent):
    name = "planner"

    @property
    def allowed_tools(self) -> list[str]:
        return self.config.planner_tools

    def run(self, prompt: str) -> str:
        message = (
            f"User request: {prompt}\n\n"
            f"Read the system prompt carefully. Explore the codebase thoroughly, "
            f"then write a complete specification to handoffs/spec.md.\n\n"
            f"Return the full contents of the spec you wrote."
        )
        return self.invoke_claude(message)
