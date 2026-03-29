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
            f"then produce a complete specification following the format in your system prompt.\n\n"
            f"IMPORTANT: You have read-only tools. Do NOT attempt to write any files. "
            f"Instead, output the full specification content directly to stdout. "
            f"The orchestrator will write it to handoffs/spec.md for you.\n\n"
            f"Return ONLY the specification content (in markdown)."
        )
        return self.invoke_claude(message)
