"""Evaluator agent — grades the implementation against the spec."""

from pathlib import Path

from agents.base import BaseAgent


class EvaluatorAgent(BaseAgent):
    name = "evaluator"

    @property
    def allowed_tools(self) -> list[str]:
        return self.config.evaluator_tools

    @property
    def mcp_config_path(self) -> str | None:
        """Return the Playwright MCP config path if eval_mode includes browser testing."""
        if self.config.eval_mode in ("playwright", "both"):
            # Check relative to CWD first, then relative to Symphony root
            config_path = Path("playwright-mcp.json")
            if config_path.exists():
                return str(config_path)
            symphony_path = self._src_dir / "playwright-mcp.json"
            if symphony_path.exists():
                return str(symphony_path)
        return None

    def run(self, spec: str, iteration: int) -> str:
        browser_instructions = ""
        if self.config.eval_mode in ("playwright", "both"):
            browser_instructions = (
                "\n\n## MANDATORY: Live Browser Testing\n"
                "You have Playwright MCP tools available. You MUST:\n"
                "1. Start the dev server (`npm run dev &` or equivalent) and wait for it\n"
                "2. Navigate to the app URL with Playwright\n"
                "3. Take a full-page screenshot\n"
                "4. Check every affected component visually\n"
                "5. Click interactive elements and verify they work\n"
                "6. For any component showing no data, curl the API directly to diagnose\n"
                "7. Take screenshots as evidence for your verdict\n"
                "8. Kill the dev server when done\n\n"
                "A component that renders without crashing but shows no data is NOT a PASS.\n"
            )

        message = (
            f"This is evaluation iteration {iteration}.\n\n"
            f"Read the spec at handoffs/spec.md.\n"
            f"Read the generator state at handoffs/generator_state.md.\n"
            f"Run `git diff main` to see what changed.\n"
            f"Run the project build command.\n"
            f"{browser_instructions}\n"
            f"Evaluate every acceptance criterion with specific evidence.\n"
            f"For any data that fails to load, curl the underlying API to determine "
            f"if it's a code bug or an external API issue. Report external issues "
            f"separately in an 'External Issues' section.\n\n"
            f"Write your structured evaluation to handoffs/eval_feedback.md.\n\n"
            f"Return the full contents of the evaluation you wrote."
        )
        return self.invoke_claude(message)
