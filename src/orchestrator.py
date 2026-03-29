#!/usr/bin/env python3
"""Symphony Orchestrator — coordinates Planner → Generator ↔ Evaluator loop."""

import argparse
import os
import re
import sys
import time

from agents.planner import PlannerAgent
from agents.generator import GeneratorAgent
from agents.evaluator import EvaluatorAgent
from config import SymphonyConfig


def extract_spec(planner_output: str) -> str:
    """Extract the specification from planner output.

    The Planner has read-only tools, so it returns the spec via stdout.
    Sometimes the output includes preamble text before or a summary after
    the actual spec.  This function extracts the spec content, falling back
    to the full output if no clear spec boundary is found.
    """
    def _strip_trailing_chat(text: str) -> str:
        """Remove trailing conversational text that isn't part of the spec."""
        # Stop at lines that look like conversational wrap-up
        lines = text.split("\n")
        cutoff = len(lines)
        for i, line in enumerate(lines):
            stripped = line.strip().lower()
            if i > 5 and re.match(
                r"^(let me know|feel free|happy to|i hope|if you|shall i|want me to|do you)",
                stripped,
            ):
                cutoff = i
                break
        return "\n".join(lines[:cutoff]).strip()

    # Look for the spec starting with the expected heading
    match = re.search(
        r"(# Feature Specification:.*)",
        planner_output,
        re.DOTALL,
    )
    if match:
        return _strip_trailing_chat(match.group(1))

    # Fallback: look for any markdown heading that looks like a spec
    match = re.search(
        r"(# (?:Feature|Specification|Spec).*)",
        planner_output,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return _strip_trailing_chat(match.group(1))

    # Last resort: return the full output
    return planner_output.strip()


def parse_args():
    parser = argparse.ArgumentParser(description="Symphony: multi-agent orchestration for Claude Code")
    parser.add_argument("--prompt", required=True, help="Feature description (1-4 sentences)")
    parser.add_argument("--iterations", type=int, default=3, help="Max Generator ↔ Evaluator cycles")
    parser.add_argument("--model", default="sonnet", choices=["sonnet", "opus", "haiku"], help="Model for all agents")
    parser.add_argument("--planner-model", default=None, help="Override model for Planner")
    parser.add_argument("--generator-model", default=None, help="Override model for Generator")
    parser.add_argument("--evaluator-model", default=None, help="Override model for Evaluator")
    parser.add_argument("--eval-mode", default="code_review", choices=["code_review", "playwright", "both"])
    parser.add_argument("--spec", default=None, help="Path to existing spec (skips Planner)")
    parser.add_argument("--branch", default=None, help="Git branch name")
    parser.add_argument("--dry-run", action="store_true", help="Run Planner only, show spec, stop")
    parser.add_argument("--verbose", action="store_true", help="Widen JSONL log previews to 2000 chars (default: 500)")
    return parser.parse_args()


def ensure_directories():
    """Create handoffs/ and logs/ directories if they don't exist."""
    os.makedirs("handoffs", exist_ok=True)
    os.makedirs("logs", exist_ok=True)


def run(args):
    config = SymphonyConfig(
        model=args.model,
        planner_model=args.planner_model or args.model,
        generator_model=args.generator_model or args.model,
        evaluator_model=args.evaluator_model or args.model,
        max_iterations=args.iterations,
        eval_mode=args.eval_mode,
        branch=args.branch,
        verbose=args.verbose,
    )

    ensure_directories()
    run_id = f"{int(time.time())}"

    # Phase 1: Plan
    if args.spec:
        print(f"[symphony] Using provided spec: {args.spec}")
        with open(args.spec, "r") as f:
            spec = f.read()
        with open("handoffs/spec.md", "w") as f:
            f.write(spec)
    else:
        print("[symphony] Phase 1: Planning...")
        planner = PlannerAgent(config, run_id)
        raw_output = planner.run(args.prompt)
        spec = extract_spec(raw_output)
        with open("handoffs/spec.md", "w") as f:
            f.write(spec)
        print("[symphony] Spec written to handoffs/spec.md")

    if args.dry_run:
        print("[symphony] Dry run complete. Review the spec at handoffs/spec.md")
        print(spec)
        return

    # Phase 2-3: Generate ↔ Evaluate
    generator = GeneratorAgent(config, run_id)
    evaluator = EvaluatorAgent(config, run_id)
    feedback = None

    for i in range(config.max_iterations):
        iteration = i + 1

        # Generate
        print(f"[symphony] Phase 2: Building (iteration {iteration}/{config.max_iterations})...")
        generator.run(spec, feedback, iteration)

        # Evaluate
        print(f"[symphony] Phase 3: Evaluating (iteration {iteration}/{config.max_iterations})...")
        eval_output = evaluator.run(spec, iteration, prior_feedback=feedback)
        with open("handoffs/eval_feedback.md", "w") as f:
            f.write(eval_output)

        if re.search(r"#*\s*VERDICT:\s*PASS", eval_output, re.IGNORECASE):
            print(f"[symphony] PASS after {iteration} iteration(s)")
            return

        print(f"[symphony] FAIL on iteration {iteration}. Evaluator found issues.")
        feedback = eval_output

    print(f"[symphony] FAIL after {config.max_iterations} iterations.")
    print("[symphony] Review handoffs/eval_feedback.md for remaining issues.")


def main():
    args = parse_args()
    try:
        run(args)
    except KeyboardInterrupt:
        print("\n[symphony] Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"[symphony] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
