# Generator State — Iteration 1

## Changes Made

- `src/agents/base.py`: Replaced `--output-format text` with `--output-format stream-json` in `invoke_claude`. Updated `_run_streaming` to parse NDJSON line-by-line: prints assistant text chunks in real-time via `sys.stdout.write/flush`, captures `result` event for full text and token usage. Returns 5-tuple `(stdout, stderr, returncode, elapsed, usage_dict)`. Updated `invoke_claude` to return `tuple[str, dict]` and include `input_tokens`/`output_tokens` in the `log("result", ...)` call. Fallback: if no `result`-type JSON found, returns raw joined lines and `{"input_tokens": 0, "output_tokens": 0}`.

- `src/agents/planner.py`: `run()` now unpacks `text, usage = self.invoke_claude(message)` and returns `(text, usage)` as `tuple[str, dict]`.

- `src/agents/generator.py`: `run()` now unpacks `text, usage = self.invoke_claude(message)` and returns `(text, usage)` as `tuple[str, dict]`.

- `src/agents/evaluator.py`: `run()` now unpacks `text, usage = self.invoke_claude(message)` and returns `(text, usage)` as `tuple[str, dict]`.

- `src/config.py`: Added `"Bash"` to `planner_tools` default list. Now: `["Read", "Glob", "Grep", "Bash"]`.

- `prompts/planner.md`: Added `Bash` entry to "Tools Available" section with the note that it is read-only verification only and MUST NOT be used to write/modify/delete/create files.

- `src/orchestrator.py`:
  - `parse_args()`: `--prompt` changed to `required=False, default=""` with explicit check. Added `--continue` flag (`dest="resume"`). Added `parser.error` if neither `--continue` nor `--prompt` provided.
  - Added `_print_token_summary(per_agent_tokens, total_input, total_output)` helper function.
  - `run()`: Added `--continue`/`--spec` mutual exclusion check (exits with code 1). Added token accumulators (`total_input_tokens`, `total_output_tokens`, `per_agent_tokens`). Added `_accumulate(agent_name, usage)` inner function. When `args.resume=True`: skip stale-handoff cleanup, skip Planner, read `spec_path` directly, read `eval_feedback_path` if exists as initial `feedback`. When `args.resume=False` and spec not found: raises `FileNotFoundError`. Token summary printed before PASS/FAIL messages and on dry-run.

## Commits

- `d50f0a2` — feat: replace text streaming with stream-json and return 5-tuple with token usage
- `76b6a36` — feat: update agent run() methods to return (text, usage) tuple
- `68f2e5d` — feat: add Bash to planner_tools and document read-only restriction in planner.md
- `87a20c4` — feat: add token tracking/summary and --continue resume flag to orchestrator

## Build Status

PASS — All Python imports succeed. Verified with `python3 -c "from agents.base import BaseAgent; from agents.planner import PlannerAgent; from agents.generator import GeneratorAgent; from agents.evaluator import EvaluatorAgent; from config import SymphonyConfig"`. All 14 acceptance criteria verified programmatically.

## Decisions

- Used `nonlocal` for token accumulators in the `_accumulate` closure inside `run()` rather than a class or module-level variable, keeping it self-contained within the run invocation.
- `import json as _json` inside `_run_streaming` method body avoids any name collision; `json` is already imported at module level so this is redundant but safe — actually kept module-level import and used it directly.
- Token summary printed before the dry-run spec output so it appears before the spec dump.
- `--continue` resume mode sets `feedback = None` when `eval_feedback.md` doesn't exist (first resume with no prior evaluation), which is consistent with how the loop initializes `feedback = None` on a fresh run.

## Known Issues

- None.
