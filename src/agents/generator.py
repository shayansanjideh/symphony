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
                f"Implement the following feature specification.\n\n"
                f"<spec>\n{spec}\n</spec>\n\n"
                f"The spec is also saved at handoffs/spec.md for reference.\n\n"
                f"Create a feature branch (if the branch already exists, check it out instead "
                f"of failing), implement all acceptance criteria, "
                f"commit your changes, and run the build to verify.\n\n"
                f"Write a summary of what you did to handoffs/generator_state.md."
            )
        else:
            message = (
                f"This is iteration {iteration}. The Evaluator found issues.\n\n"
                f"<eval_feedback>\n{feedback}\n</eval_feedback>\n\n"
                f"The feedback is also at handoffs/eval_feedback.md.\n"
                f"Make targeted fixes for ONLY the issues raised. "
                f"Do not rewrite working code.\n\n"
                f"Commit your fixes and run the build to verify.\n"
                f"Update handoffs/generator_state.md with what you fixed."
            )

        if self.config.branch and iteration == 1:
            message += f"\n\nUse branch name: {self.config.branch}"

        return self.invoke_claude(message)
