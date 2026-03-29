"""Base agent class — handles Claude CLI invocation, logging, and context management."""

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from config import SymphonyConfig


class BaseAgent:
    """Base class for Symphony agents. Each agent runs as a `claude -p` subprocess."""

    name: str = "base"
    allowed_tools: list[str] = []

    # Resolve the Symphony source directory once, so prompt paths work even when
    # Symphony is symlinked into a project and CWD is the project root.
    _src_dir: Path = Path(__file__).resolve().parent.parent  # symphony/src/../ → symphony/

    def __init__(self, config: SymphonyConfig, run_id: str):
        self.config = config
        self.run_id = run_id
        self.log_file = Path(config.logs_dir) / f"{run_id}_{self.name}.jsonl"

    @property
    def model(self) -> str:
        return getattr(self.config, f"{self.name}_model", self.config.model)

    @property
    def _preview_len(self) -> int:
        return 2000 if self.config.verbose else 500

    @property
    def prompts_dir(self) -> Path:
        """Resolve the prompts directory.

        First checks relative to CWD (allows user overrides), then falls back
        to the directory relative to Symphony's own source tree.  This way the
        prompts are always found even when Symphony is symlinked into a project
        and CWD != the symphony directory.
        """
        cwd_path = Path(self.config.prompts_dir)
        if cwd_path.is_dir():
            return cwd_path

        # Fall back to <symphony_root>/prompts
        symphony_path = self._src_dir / self.config.prompts_dir
        if symphony_path.is_dir():
            return symphony_path

        raise FileNotFoundError(
            f"Prompts directory not found at '{cwd_path}' (CWD) or '{symphony_path}' (Symphony root). "
            f"Ensure the prompts/ directory exists."
        )

    @property
    def system_prompt(self) -> str:
        prompt_path = self.prompts_dir / f"{self.name}.md"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text()

    @property
    def mcp_config_path(self) -> str | None:
        """Override in subclasses to provide an MCP server config."""
        return None

    def invoke_claude(self, message: str) -> str:
        """Invoke claude CLI with the given message, streaming output live.

        Retries once on timeout or non-zero exit (transient CLI errors).
        """
        cmd = [
            "claude", "-p", message,
            "--model", self.model,
            "--output-format", "text",
            "--system-prompt", self.system_prompt,
        ]

        if self.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(self.allowed_tools)])

        if self.mcp_config_path:
            cmd.extend(["--mcp-config", self.mcp_config_path])

        self.log("invoke", {"message_preview": message[:200], "model": self.model})

        max_attempts = 2
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                stdout, stderr, returncode, elapsed = self._run_streaming(cmd)
            except subprocess.TimeoutExpired:
                if attempt < max_attempts:
                    self.log("retry", {"reason": "timeout", "attempt": attempt})
                    time.sleep(5 * attempt)
                    continue
                raise RuntimeError(f"{self.name} agent timed out after {max_attempts} attempts")

            self.log("result", {
                "exit_code": returncode,
                "elapsed_seconds": round(elapsed, 1),
                "stdout_preview": stdout[:self._preview_len] if stdout else "",
                "stderr_preview": stderr[:self._preview_len] if stderr else "",
            })

            if returncode == 0:
                return stdout

            last_error = f"{self.name} agent failed (exit {returncode}): {stderr[:self._preview_len]}"
            if attempt < max_attempts:
                self.log("retry", {"reason": f"exit_{returncode}", "attempt": attempt})
                time.sleep(5 * attempt)

        raise RuntimeError(last_error)

    def _run_streaming(self, cmd: list[str]) -> tuple[str, str, int, float]:
        """Run a subprocess, streaming stdout line-by-line while capturing it.

        Stderr is drained concurrently in a background thread to prevent the
        pipe buffer from filling up and blocking the process.
        """
        start = time.time()
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        stderr_lines: list[str] = []

        def _drain_stderr():
            for line in proc.stderr:
                stderr_lines.append(line)

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        stdout_lines = []
        try:
            for line in proc.stdout:
                sys.stdout.write(f"  [{self.name}] {line}")
                sys.stdout.flush()
                stdout_lines.append(line)
            proc.wait(timeout=self.config.agent_timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise
        finally:
            stderr_thread.join()

        elapsed = time.time() - start
        return "".join(stdout_lines), "".join(stderr_lines), proc.returncode, elapsed

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
