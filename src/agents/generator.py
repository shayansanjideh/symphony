"""Generator agent — implements the spec and addresses eval feedback."""

from pathlib import Path

from agents.base import BaseAgent


class GeneratorAgent(BaseAgent):
    name = "generator"

    @property
    def allowed_tools(self) -> list[str]:
        return self.config.generator_tools

    def run(self, spec: str, feedback: str | None, iteration: int) -> tuple[str, dict]:
        if iteration == 1:
            message = (
                f"Implement the following feature specification.\n\n"
                f"<spec>\n{spec}\n</spec>\n\n"
                f"The spec is also saved at {Path(self.config.handoffs_dir) / 'spec.md'} for reference.\n\n"
                f"Create a feature branch (if the branch already exists, check it out instead "
                f"of failing), implement all acceptance criteria, "
                f"commit your changes, and run the build to verify.\n\n"
                f"Write a summary of what you did to {Path(self.config.handoffs_dir) / 'generator_state.md'}."
            )
        else:
            eval_feedback_path = Path(self.config.handoffs_dir) / "eval_feedback.md"
            generator_state_path = Path(self.config.handoffs_dir) / "generator_state.md"
            message = (
                f"This is iteration {iteration}. The Evaluator found issues.\n\n"
                f"<spec>\n{spec}\n</spec>\n\n"
                f"<eval_feedback>\n{feedback}\n</eval_feedback>\n\n"
                f"The feedback is also at {eval_feedback_path}.\n"
                f"Make targeted fixes for ONLY the issues raised. "
                f"Do not rewrite working code.\n\n"
                f"Commit your fixes and run the build to verify.\n"
                f"Update {generator_state_path} with what you fixed."
            )

        if self.config.branch and iteration == 1:
            message += f"\n\nUse branch name: {self.config.branch}"

        text, usage = self.invoke_claude(message)
        return text, usage
