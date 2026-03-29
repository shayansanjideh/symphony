# Symphony

**Autonomous multi-agent orchestration for Claude Code.**

Symphony is a Claude Code skill that coordinates three specialized AI agents — Planner, Generator, and Evaluator — in an iterative loop to autonomously build features from a single sentence. Inspired by Anthropic's research on [harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps), Symphony brings GAN-inspired adversarial quality control to your development workflow.

> *"Every component in a harness encodes an assumption about what the model can't do on its own."*
> — Anthropic Engineering

---

## The Problem

Claude Code is powerful, but complex features still require human oversight at every step: reviewing specs, catching bugs, validating implementations, iterating on feedback. You end up being the QA layer between the AI and your codebase.

**Symphony removes you from the loop.** You describe what you want in 1-4 sentences. Three agents handle the rest — planning, building, and ruthlessly testing — until the feature passes evaluation or the iteration budget is exhausted.

---

## Quick Start

### Install

```bash
# Clone into your project (or globally)
git clone https://github.com/shayansanjideh/symphony.git

# Install dependencies
pip install -r symphony/requirements.txt
```

### Add to your project

Copy the skill command into your project's Claude Code commands:

```bash
mkdir -p .claude/commands
cp symphony/.claude/commands/symphony.md .claude/commands/
```

Or symlink for automatic updates:

```bash
ln -s "$(pwd)/symphony/.claude/commands/symphony.md" .claude/commands/symphony.md
```

### Use

```
/symphony Add a search bar to the navigation header with autocomplete
```

---

## Architecture

```
  User Prompt
       |
       v
┌─────────────────────────────────────────┐
│              SYMPHONY                   │
│                                         │
│   ┌───────────┐                         │
│   │  PLANNER  │────> handoffs/spec.md   │
│   └───────────┘                         │
│         │                               │
│         v                               │
│   ┌─────────────┐    ┌──────────────┐   │
│   │  GENERATOR  │───>│  EVALUATOR   │   │
│   └─────────────┘    └──────────────┘   │
│         ^                   │           │
│         │     FAIL?         │           │
│         └───────────────────┘           │
│                             │           │
│                          PASS?          │
│                             │           │
└─────────────────────────────────────────┘
                              |
                              v
                      Feature Branch
```

---

## How It Works

### Phase 1: Planner

The Planner agent receives the user's brief prompt and explores the codebase to understand architecture, patterns, and constraints. It produces a detailed specification including:

- Scoped requirements (in-scope / out-of-scope)
- Functional and non-functional requirements
- Testable acceptance criteria the Evaluator can verify
- Technical context discovered from reading the code

**Tools:** Read-only codebase access (Read, Glob, Grep)
**Output:** `handoffs/spec.md`

### Phase 2: Generator

The Generator reads the spec and implements it, following existing codebase patterns. It creates a feature branch, makes iterative commits, and runs the build to verify correctness.

When receiving Evaluator feedback (iteration 2+), the Generator makes targeted fixes — it doesn't rewrite working code, only addresses the specific issues reported.

**Tools:** Full codebase access (Read, Write, Edit, Bash)
**Output:** Committed code on a feature branch + `handoffs/generator_state.md`

### Phase 3: Evaluator

The Evaluator is the critical counterweight. It is tuned to be **skeptical** — its job is to find problems, not praise. It grades the implementation against four criteria:

| Criterion | What it checks |
|-----------|---------------|
| **Functionality** | Does each acceptance criterion pass? Edge cases? |
| **Code Quality** | Follows project patterns? Bugs? Type errors? Dead code? |
| **Visual Design** | Consistent UI? Proper styling? Dark mode support? |
| **Completeness** | All acceptance criteria addressed? Any gaps? |

Each criterion gets a **PASS** or **FAIL** with specific evidence (file paths, line numbers, observed behaviors). If ANY criterion fails, the overall verdict is FAIL and detailed bug reports are sent back to the Generator.

**Tools:** Read-only codebase + Bash (for `git diff`, build commands, etc.)
**Output:** `handoffs/eval_feedback.md` with structured verdict

### The Loop

```
Generator implements → Evaluator grades → FAIL? → Generator fixes → Evaluator re-grades → ...
```

This continues until:
- **PASS** — all criteria met, feature is ready
- **Max iterations reached** — feedback is preserved for human review

---

## Why Three Agents?

This architecture is borrowed from GANs (Generative Adversarial Networks) and Anthropic's research on the **self-evaluation problem**:

> *"Tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work."*

When an agent evaluates its own output, it exhibits **self-leniency** — confidently praising mediocre work. The solution is structural: make evaluation a separate agent's entire job.

1. **The Generator builds.** It focuses purely on implementation without judging quality.
2. **The Evaluator breaks.** It assumes the code is broken until proven otherwise.
3. **The tension between them produces quality.** Each iteration tightens the gap between spec and implementation.

**The Planner is load-bearing.** Without it, brief prompts lead to under-scoping — the Generator builds a minimal version that misses the user's actual intent. The Planner expands scope, discovers constraints, and writes acceptance criteria that hold the Generator accountable.

---

## Usage

### Basic

```
/symphony Add a search bar to the navigation header with autocomplete
```

### With Options

```
/symphony --iterations 5 Refactor the settings page to use a tabbed layout
```

```
/symphony --model opus Add an analytics dashboard with interactive charts
```

### Dry Run (Plan Only)

```
/symphony --dry-run Add user profile avatars with upload support
```

### Bring Your Own Spec

```
/symphony --spec docs/my-feature-spec.md
```

### Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--iterations` | `3` | Max Generator ↔ Evaluator cycles |
| `--eval-mode` | `code_review` | `code_review`, `playwright`, or `both` |
| `--model` | `sonnet` | Model for all agents (`sonnet`, `opus`, `haiku`) |
| `--planner-model` | — | Override model for Planner only |
| `--generator-model` | — | Override model for Generator only |
| `--evaluator-model` | — | Override model for Evaluator only |
| `--spec` | — | Path to existing spec (skips Planner) |
| `--branch` | auto | Git branch name for the feature |
| `--dry-run` | false | Run only Planner, show spec, stop for approval |

---

## Example Run

**Input:**
```
/symphony Add a dark mode toggle to the settings page
```

**What happens:**

| Phase | Agent | Duration | Result |
|-------|-------|----------|--------|
| Plan | Planner | ~1 min | 8 acceptance criteria, discovered existing theme context and CSS variables |
| Build (iter 1) | Generator | ~3 min | New `ThemeToggle` component, updated `SettingsPage`, added CSS variables for dark palette. Committed to `symphony/dark-mode-toggle`. |
| QA (iter 1) | Evaluator | ~2 min | **FAIL** — Toggle doesn't persist preference to `localStorage`. Also, dark mode doesn't apply to the modal overlay component. |
| Build (iter 2) | Generator | ~2 min | Fixed: added `localStorage` persistence with `useEffect` hook. Extended dark variables to modal overlay. |
| QA (iter 2) | Evaluator | ~2 min | **PASS** — All 8 criteria verified with specific evidence. |

**Total: ~10 minutes, 2 iterations, zero human intervention.**

The Evaluator caught a real persistence bug (toggle resets on page reload) and an incomplete style coverage issue — the kind of gaps that are easy to miss in self-review but obvious to a dedicated critic.

---

## Project Structure

```
symphony/
├── README.md                     # This file
├── LICENSE
├── requirements.txt              # Python dependencies
├── .claude/
│   └── commands/
│       └── symphony.md           # Claude Code slash command definition
├── src/
│   ├── orchestrator.py           # Main loop: Planner → Generator ↔ Evaluator
│   ├── config.py                 # Configuration defaults and CLI arg parsing
│   └── agents/
│       ├── base.py               # Base agent class (CLI invocation, logging)
│       ├── planner.py            # Planner agent
│       ├── generator.py          # Generator agent
│       └── evaluator.py          # Evaluator agent
├── prompts/
│   ├── planner.md                # Planner system prompt
│   ├── generator.md              # Generator system prompt
│   └── evaluator.md              # Evaluator system prompt (with calibration examples)
└── examples/                     # (planned) Example runs with full handoff files
```

---

## Design Principles

### File-Based Handoffs
Agents communicate through shared markdown files, not direct message passing. This enables async coordination, artifact preservation, and debuggability — you can read exactly what each agent saw and produced.

### Context Resets Over Compaction
When context gets long, starting fresh with a structured handoff is better than summarizing in-place. Each agent gets a clean slate with exactly the information it needs.

### Skeptical Evaluation with Calibration
The Evaluator prompt includes few-shot examples of good and bad evaluations to calibrate judgment. Bad: *"Looks good."* Good: *"FAIL — AC-3 requires persisting the toggle state, but there is no localStorage call. Location: src/components/ThemeToggle.tsx:42"*

### Stress-Test Your Assumptions
Every harness component encodes an assumption about what the model can't do alone. These assumptions go stale as models improve. Symphony is designed to be simplified over time — remove components, test if quality holds, keep only what's load-bearing.

---

## Roadmap

- [x] **v0.1** — Core loop: Planner → Generator ↔ Evaluator via `claude -p`, with progress streaming and `--verbose` flag
- [x] **v0.2** — `--dry-run` mode (plan-only with user approval gate), resume from handoff state, retry logic on transient CLI errors
- [x] **v0.3** — Playwright integration for visual and interactive testing
- [ ] **v0.4** — Sprint decomposition for large features (auto-chunk into phases) with parallel execution
- [ ] **v1.0** — Stable release with cost estimation, prompt library, and comprehensive docs

---

## Attribution

Symphony is inspired by Anthropic's engineering research on [harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps). The three-agent architecture, GAN-inspired adversarial evaluation, file-based handoffs, and evaluator calibration patterns are adapted from their published findings.

---

## License

MIT

---

*Symphony: let the agents play.*
