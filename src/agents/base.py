"""Base agent class — handles Claude CLI invocation, logging, and context management."""

import json
import os
import subprocess
import time
from pathlib import Path

from config import SymphonyConfig


class BaseAgent:
    """Base class for Symphony agents. Each agent runs as a `claude -p` subprocess."""

    name: str = "base"
    allowed_tools: list[str] = []

    def __init__(self, config: SymphonyConfig, run_id: str):
        self.config = config
        self.run_id = run_id
        self.log_file = Path(config.logs_dir) / f"{run_id}_{self.name}.jsonl"

    @property
    def model(self) -> str:
        return getattr(self.config, f"{self.name}_model", self.config.model)

    @property
    def system_prompt(self) -> str:
        prompt_path = Path(self.config.prompts_dir) / f"{self.name}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text()

    @property
    def mcp_config_path(self) -> str | None:
        """Override in subclasses to provide an MCP server config."""
        return None

    def invoke_claude(self, message: str) -> str:
        """Invoke claude CLI with the given message and return the output."""
        cmd = [
            "claude", "-p", message,
            "--model", self.model,
            "--output-format", "text",
        ]

        if self.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(self.allowed_tools)])

        if self.mcp_config_path:
            cmd.extend(["--mcp-config", self.mcp_config_path])

        self.log("invoke", {"message_preview": message[:200], "model": self.model})

        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.config.agent_timeout)
        elapsed = time.time() - start

        self.log("result", {
            "exit_code": result.returncode,
            "elapsed_seconds": round(elapsed, 1),
            "stdout_preview": result.stdout[:500] if result.stdout else "",
            "stderr_preview": result.stderr[:500] if result.stderr else "",
        })

        if result.returncode != 0:
            raise RuntimeError(
                f"{self.name} agent failed (exit {result.returncode}): {result.stderr[:500]}"
            )

        return result.stdout

    def log(self, event: str, data: dict):
        """Append a log entry to the agent's JSONL log file."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "agent": self.name,
            "event": event,
            **data,
        }
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
