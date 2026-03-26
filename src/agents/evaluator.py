"""Evaluator agent — grades the implementation against the spec."""

from agents.base import BaseAgent


class EvaluatorAgent(BaseAgent):
    name = "evaluator"

    @property
    def allowed_tools(self) -> list[str]:
        return self.config.evaluator_tools

    def run(self, spec: str, iteration: int) -> str:
        message = (
            f"This is evaluation iteration {iteration}.\n\n"
            f"Read the spec at handoffs/spec.md.\n"
            f"Read the generator state at handoffs/generator_state.md.\n"
            f"Run `git diff main` to see what changed.\n"
            f"Run the project build command.\n\n"
            f"Evaluate every acceptance criterion with specific evidence.\n"
            f"Write your structured evaluation to handoffs/eval_feedback.md.\n\n"
            f"Return the full contents of the evaluation you wrote."
        )
        return self.invoke_claude(message)
