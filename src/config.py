"""Symphony configuration."""

from dataclasses import dataclass, field


@dataclass
class SymphonyConfig:
    model: str = "sonnet"
    planner_model: str = "sonnet"
    generator_model: str = "sonnet"
    evaluator_model: str = "sonnet"
    max_iterations: int = 3
    eval_mode: str = "both"  # "code_review", "playwright", or "both"
    branch: str | None = None
    agent_timeout: int = 1800  # seconds per agent invocation (30 min)

    # Paths
    prompts_dir: str = "prompts"
    handoffs_dir: str = "handoffs"
    logs_dir: str = "logs"

    # Tool scoping
    planner_tools: list[str] = field(default_factory=lambda: [
        "Read", "Glob", "Grep",
    ])
    generator_tools: list[str] = field(default_factory=lambda: [
        "Read", "Write", "Edit", "Bash", "Glob", "Grep",
    ])
    evaluator_tools: list[str] = field(default_factory=lambda: [
        "Read", "Glob", "Grep", "Bash",
    ])
