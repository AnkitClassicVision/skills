---
name: run-project
description: Universal project conductor. One command, full pipeline. Auto-detects everything.
version: 2.1.0
author: Public Maintainer
category: software-development
surfaces: [hermes, claude-code, codex]
---

# /run-project

## Invocation

```
/run-project [path]
```

- `path`: Repo path (defaults to current directory)
- That's it. No flags. The skill decides the rest.

## What It Does

Runs any repo through a pipeline that produces a spec-backed, issue-tracker-ready implementation plan.

Blind evals are generated after every artifact phase and hidden until execution QA.

```
Grill → PRD → [Blind Eval] → Agent Spec → [Blind Eval] → Context Layer → [Blind Eval]
  → SEEIT → To-Issues → [Blind Eval] → Writing-Plans → [Blind Eval]
  → Execute (all evals revealed to QA) → Accept
```

## Auto-Detection (No Flags Needed)

| Decision | How It Decides |
|----------|---------------|
| **AAC pre-phase?** | Sees "agent", "workflow", "automation", "bot", "RAG", "LLM pipeline" in intent or finds `agent_registry`, `aac-v2`, `agenttwin` files → runs AAC. Otherwise skips. |
| **Brownfield deepening?** | Repo exists + >1000 LOC → auto-runs codebase analysis during Grill. Presents findings. User says yes/no. |
| **QA checks?** | Finds tests → runs them. Finds lint config → runs it. No config → skips. |
| **Resume?** | Finds `.run-project/state.json` → asks "Resume from Phase N?" One yes/no. |
| **Surface dispatch?** | Detects Hermes vs Claude Code vs Codex automatically. |

## Human Gates (Two Only)

1. **After Grill** — "Good to write the PRD?" (yes/no)
2. **After SEEIT** — "Looks right? Proceed to issues?" (yes/no)

Everything else flows automatically. No other stopping points.

## Global Guardrails (Apply to ALL phases)

### Execution Focus Rule
When the user is mid-execution of a multi-slice project (especially Phase 13 Execute), **complete the current slice before discussing skill evolution, framework design, or meta-tooling improvements.**

- If the user asks a tangential question (e.g., "can we create a universal method for X?"), acknowledge briefly, capture the idea, then **ask**: "Finish current slice first, or pause to discuss?"
- User signal to defer: "Wait finish the project first", "not now", "later", "let's get back to..."
- Never abandon a partially-implemented slice for a side conversation.

### Pause / Resume
The user may pause at any time. When they say "pause", "stop", "not yet", "I don't want to finish this just yet":

1. **Kill running processes** (servers, background jobs)
2. **Write current state** to `.run-project/state.json` with phase, slice, and last action
3. **Identify the clean stopping point**: completed slice boundary, not mid-file
4. **Summarize what's done vs. not done** in 5 bullets
5. **Write resume notes** to local project memory or the project tracker
6. **Update active task tracker entries** with "Paused by user request — do not continue until explicitly unblocked"

Resume: read `state.json`, verify files exist, pick up at the next uncompleted slice.

### Fresh Restart Over Existing State
When the user asks to restart or run a fresh `/run-project` on a repo that already has `.run-project/` artifacts:

1. **Do not `git reset`, clean, or delete uncommitted work.** Treat dirty state as user-owned unless they explicitly authorize cleanup.
2. **Archive before overwrite**: copy `.run-project/` to a timestamped external artifact directory, e.g. `~/.agent/artifacts/<repo>-run-project-archive-<UTC>/`.
3. **Run baseline verification before new artifacts** when tests are available, and report the exact pass/fail count.
4. **Write the fresh state intentionally**: new `.run-project/state.json`, `organizer-report.json`, and `handoffs/grill.md` should mention the archive path and the chosen Gate 1 recommendation.
5. **For AI workflow / bot / automation repos**, trigger AAC before making any readiness claim. Say "no production-readiness claim made" unless an AAC pass has actually happened.

See `references/fresh-restart-existing-run-project.md` for a concrete paid-ads agent workflow example.

See `references/execution-pitfalls.md` for common execution-phase traps and fixes.

## Pipeline

### Phase 1: Grill
- Uses `grill-me` (Matt's skill)
- **Auto-runs `codebase-organizer`** if repo exists + >1000 LOC. User controls whether to include organizer output in grill.
- `codebase-organizer` can be invoked standalone at any time via `/organize [path]`. Its output auto-binds to `.run-project/organizer-report.json`.
- `/skillify [path]` can be invoked standalone to turn any repo into a `.skill-pack/` — a persistent skill manifest consumed by all pipeline phases. Runs `/organize` internally.
- Presents deepening candidates from organizer analysis
- Explores codebase instead of asking when possible
- Checks available project memory, repo ADRs, CONTEXT.md, and prior handoffs for existing decisions
- **Output**: Decision tree + shared understanding
- **Gate**: User approves → continue

### Phase 2: PRD
- Uses `to-prd` (Matt's skill)
- Problem, solution, user stories, decisions
- **Output**: `.run-project/prd.md`

### Phase 3: Blind Eval (PRD)
- Fresh subagent. Zero context. Reads ONLY `.run-project/prd.md`.
- Generates 5-10 testable criteria: "What must the implementation deliver?"
- **Hidden**: `.run-project/evals/prd-eval.md`
- PRD writer never sees this

### Phase 4: Agent Spec
- Uses `agent-spec-writer`
- Given/When/Then, boundaries, non-behaviors
- **Output**: `.run-project/agent-spec.md`

### Phase 5: Blind Eval (Spec)
- Fresh subagent. Reads spec + prior evals. NOT the PRD writer's context.
- Generates behavioral eval criteria
- **Hidden**: `.run-project/evals/spec-eval.md`

### Phase 6: Context Layer
- Uses `context-layer-generator` + `/skillify` if `.skill-pack/` exists
- Structural, semantic, philosophical
- Built on Agent Spec + `.skill-pack/PROJECT.md` if present
- **Auto-runs `/skillify`** if `.skill-pack/` does not exist — produces repo-as-skill manifest for all downstream phases
- **Greenfield fast-path**: If spec is already detailed (PRD + Spec >50 decisions locked) AND repo has no src/ or <100 LOC, the pipeline MAY offer to merge Context Layer into To-Issues and skip SEEIT. This is OPT-IN — user must explicitly say "skip context layer" or "fast path". Default is full process.
- **Output**: `.run-project/context-layer.md` or merged into `HANDOFF.md` (only if user opts in)

### Phase 7: Blind Eval (Context)
- Fresh subagent. Reads all outputs so far.
- Generates architectural eval criteria
- **Hidden**: `.run-project/evals/context-eval.md`

### Phase 8: SEEIT
- Uses `seeit`
- Interactive HTML
- **Output**: `.run-project/seeit.html`
- **Deployment**: Deploy to Vercel for live viewing (see `references/seeit-deployment.md`)
- **Gate**: User approves → continue

### Phase 9: To-Issues
- Uses `to-issues` (Matt's)
- Tracer-bullet slices
- **Output**: `.run-project/issues.md`

### Phase 10: Blind Eval (Issues)
- Fresh subagent. Reads issues + plan.
- Generates completeness eval criteria
- **Hidden**: `.run-project/evals/issues-eval.md`

### Phase 11: Writing-Plans
- Uses `writing-plans`
- 2-5 min tasks, exact paths
- **Output**: `.run-project/plan.md`

### Phase 12: Blind Eval (Plans)
- Fresh subagent. Reads plan + all outputs.
- Generates implementation eval criteria
- **Hidden**: `.run-project/evals/plan-eval.md`

### Phase 13: Execute
- Uses surface-appropriate execution skill
- **QA Gate — ALL evals revealed NOW**: QA subagent gets all 5 eval files. Checks implementation against every criterion.
- Auto-detected checks (tests, lint, types, security) + accumulated eval criteria
- **Pass**: All evals + checks pass, or 3 tries
- **Output**: Working code

### Phase 14: Accept
- AI workflows: `agenttwin` / AAC
- Standard: all checks passed
- **Output**: `.run-project/acceptance.md`

## Blind Eval Rules

1. **Fresh context**: Eval subagent gets ONLY the artifact. No handoff notes.
2. **Hidden until QA**: Files in `.run-project/evals/`. No phase references them.
3. **Accumulative**: Each eval builds on prior evals but each generator is blind to process.
4. **Revealed only at Execute**: QA is the first agent to see both implementation + evals.
5. **Human never sees evals**: Machine-generated, machine-checked. User sees pass/fail summary.

See `references/blind-eval-mechanism.md` for the full enumeration mechanism (how QA subagent reads evals, automated vs manual checks, information barrier diagram).

## Eval Generation Prompt

Each eval subagent receives:

```
You are a blind evaluator. You have NO context about how this artifact was created.
You have NOT seen previous phases, decisions, or conversations.

Read the artifact below. Generate specific, testable evaluation criteria.
What would you expect to see in the next phase based ONLY on this artifact?

Focus on:
- What must be true for this to be a good foundation?
- What gaps or ambiguities would make implementation fail?
- What specific behaviors, structures, or decisions must be present?

Write 5-10 eval items. Each must be a pass/fail check.
5. **Human never sees evals**: Machine-generated, machine-checked. User sees pass/fail summary.

See `references/blind-eval-mechanism.md` for the full enumeration mechanism (how QA subagent reads evals, automated vs manual checks, information barrier diagram).

## Dual-Persistence Convention: `.run-project/` vs `.skill-pack/`

| Directory | Purpose | Lifetime | Created By |
|-----------|---------|----------|------------|
| `.run-project/` | Pipeline state — phase tracker, evals, handoffs, QA results | Ephemeral per project run | `/run-project` |
| `.skill-pack/` | **Repo identity** — skill manifest, context layers, interfaces, ADRs | Travels with the repo, re-run monthly | `/skillify` |

**Why two directories**: `.run-project/` tracks where we are in the pipeline; `.skill-pack/` describes what the repo IS. One is a process artifact, the other is a product artifact. Both are gitignored.

**When to re-skillify**: Major refactor, 3+ new files, new dependencies, new feature branch, or when an agent asks "I need more context about this repo."

## Context Layer Decision Logic

When reaching Phase 6, the pipeline decides:

```
IF .skill-pack/ exists AND < 7 days old:
  → Load PROJECT.md + context/*.json, skip full generation
ELIF greenfield (no src/ OR < 100 LOC):
  → OFFER fast-path: "PRD + Spec are detailed. Skip Context Layer + SEEIT and go straight to To-Issues?"
  → If user says YES → produce HANDOFF.md with vertical slices, skip SEEIT
  → If user says NO → full Context Layer + SEEIT
ELIF brownfield (> 1000 LOC + existing src/):
  → Full Context Layer: structural, semantic, philosophical
  → THEN run SEEIT
ELSE:
  → Lean Context Layer (structural + key interfaces only)
```

Greenfield fast-path rationale: With a detailed PRD + Agent Spec (>50 decisions locked), the Context Layer is redundant. The spec already encodes what would be in the philosophical layer. SEEIT visualizes existing code — on greenfield there is nothing to SEE. Better to hand off directly to To-Issues. **But the user must explicitly opt in.** Default is full process.

**Phase enforcement**: If user says "follow the full process" or "don't skip anything", all fast-path offers are suppressed. Every phase runs.

## Context Flow

Each phase reads the previous phase's output. No repeated questions. If an answer exists in:
- Project memory or prior handoffs
- `.run-project/handoffs/`
- `.skill-pack/PROJECT.md` or `context/*.json`
- Repo ADRs / CONTEXT.md
- Prior phase outputs

...the skill uses it. Never asks twice.

## Files Created

```
.run-project/
  state.json           # Current phase, resume point
  handoffs/            # Phase outputs for next phase
  prd.md
  agent-spec.md
  context-layer.md     # Or HANDOFF.md (greenfield fast-path)
  seeit.html
  issues.md            # Or merged into HANDOFF.md (greenfield fast-path)
  plan.md
  acceptance.md
  evals/               # Hidden until Execute QA
    prd-eval.md
    spec-eval.md
    context-eval.md
    issues-eval.md
    plan-eval.md
  adrs/                # Rejected deepening candidates
  qa/
    results/           # QA loop outputs

.skill-pack/           # Persistent repo-as-skill manifest (auto-created by /skillify)
  PROJECT.md           # Human-readable, agent-consumable repo manifest
  context/
    structural.json    # Module map, import graph, circular deps
    semantic.json      # Type signatures, contracts, complexity
    philosophical.json # Deep modules, hotspots, recommendations
  interfaces/          # Annotated public API per module
  adrs/                # Inferred architectural decisions
```

## Coding-agent handoff

When the user asks to finish a `/run-project` effort in a local coding-agent session, create a repo-local resume context at `.run-project/handoffs/codex-cli-resume-context.md`, launch the coding agent from the repo with PTY, seed a read-only instruction, and verify Codex is waiting before reporting ready. See `references/codex-cli-handoff.md`.

## Cross-Surface Dispatch

| Phase | Hermes | Claude Code | Codex |
|-------|--------|-------------|-------|
| Grill | `grill-me` | `grill-me` | `grill-me` |
| PRD | `to-prd` | `to-prd` | `to-prd` |
| Agent Spec | `agent-spec-writer` | `agent-spec-writer` | `agent-spec-writer` |
| Context Layer | `context-layer-generator` | `context-layer-generator` | `context-layer-generator` |
| SEEIT | `seeit` | `seeit` | `seeit` |
| To-Issues | `to-issues` | `to-issues` | `to-issues` |
| Writing-Plans | `writing-plans` | `writing-plans` | `writing-plans` |
| Execute | local executor or coding agent | local executor or coding agent | local executor or coding agent |
| Accept | `agenttwin` / `aac-process-design` | `agenttwin` | `agenttwin` |

## Dependencies

Required:
- `grill-me`, `to-prd`, `to-issues`, `handoff`
- `agent-spec-writer`, `context-layer-generator`
- `seeit`, `writing-plans`, `skillify`
- `writing-plans` plus the available local coding agent or executor

Auto-detected:
- `aac-process-design` — if AI workflow detected
- `improve-codebase-architecture` — if brownfield detected
- `agenttwin` — if AI workflow detected

## Version History

- v2.1.0 (2026-05-28): Blind evals after every artifact phase. Hidden until Execute QA.
- v2.0.0 (2026-05-28): Simplified to zero flags. Auto-detect everything.
- v1.1.0 (2026-05-28): Added Dark Factory QA integration
- v1.0.0 (2026-05-28): Initial orchestrator
