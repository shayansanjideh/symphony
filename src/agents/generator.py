"""Generator agent — implements the spec and addresses eval feedback."""

from agents.base import BaseAgent


class GeneratorAgent(BaseAgent):
    name = "generator"

    @property
    def allowed_tools(self) -> list[str]:
        return self.config.generator_tools

    def run(self, spec: str, feedback: str | None, iteration: int) -> str:
        if iteration == 1:
            message = (
                f"Read the spec at handoffs/spec.md and implement the feature.\n\n"
                f"Create a feature branch, implement all acceptance criteria, "
                f"commit your changes, and run the build to verify.\n\n"
                f"Write a summary of what you did to handoffs/generator_state.md."
            )
        else:
            message = (
                f"This is iteration {iteration}. The Evaluator found issues.\n\n"
                f"Read the feedback at handoffs/eval_feedback.md.\n"
                f"Make targeted fixes for ONLY the issues raised. "
                f"Do not rewrite working code.\n\n"
                f"Commit your fixes and run the build to verify.\n"
                f"Update handoffs/generator_state.md with what you fixed."
            )

        if self.config.branch and iteration == 1:
            message += f"\n\nUse branch name: {self.config.branch}"

        return self.invoke_claude(message)
