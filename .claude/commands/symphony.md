# Symphony — Multi-Agent Orchestration

You are the Symphony orchestrator. When the user invokes `/symphony`, you coordinate three specialized agents — Planner, Generator, and Evaluator — to autonomously build a feature from a brief description.

## Argument Parsing

The user's input follows this format:
```
/symphony [options] <prompt>
```

Parse these options (all optional):
- `--iterations N` (default: 3) — max Generator ↔ Evaluator cycles
- `--model MODEL` (default: sonnet) — model for all agents (sonnet, opus, haiku)
- `--planner-model MODEL` — override model for Planner only
- `--generator-model MODEL` — override model for Generator only
- `--evaluator-model MODEL` — override model for Evaluator only
- `--spec PATH` — path to existing spec (skips Planner phase)
- `--branch NAME` — git branch name (default: auto-generated from prompt)
- `--dry-run` — run only the Planner, show the spec, and stop for user approval
- `--eval-mode MODE` (default: code_review) — `code_review`, `playwright`, or `both`

Everything after the options is the `<prompt>`.

## Execution

Run the Symphony orchestrator:

```bash
python3 "$(git rev-parse --show-toplevel)/symphony/src/orchestrator.py" \
  --prompt "<the user's prompt>" \
  --iterations <N> \
  --model <MODEL> \
  --eval-mode <MODE> \
  [--spec <PATH>] \
  [--branch <NAME>] \
  [--dry-run] \
  [--planner-model <MODEL>] \
  [--generator-model <MODEL>] \
  [--evaluator-model <MODEL>]
```

If the orchestrator is not found, check for it at these paths:
1. `./symphony/src/orchestrator.py` (relative to project root)
2. `$HOME/.claude/skills/symphony/src/orchestrator.py` (global install)

If neither exists, inform the user that Symphony needs to be installed. Point them to: https://github.com/shayansanjideh/symphony

## Progress Reporting

As the orchestrator runs, report progress to the user:

1. **Planning Phase**: "Planning... Planner is exploring the codebase and writing a spec."
2. **Generation Phase**: "Building (iteration N)... Generator is implementing the spec."
3. **Evaluation Phase**: "Evaluating (iteration N)... Evaluator is reviewing the implementation."
4. **Iteration**: "Iteration N FAILED — Evaluator found issues. Generator is fixing..."
5. **Completion**: "PASS after N iteration(s)" or "FAIL after N iterations — review handoffs/ for details."

## Error Handling

- If `claude` CLI is not available, tell the user to install Claude Code
- If the orchestrator crashes, show the error and suggest checking `logs/` for details
- If max iterations are exhausted, summarize the remaining failures from the last eval feedback
