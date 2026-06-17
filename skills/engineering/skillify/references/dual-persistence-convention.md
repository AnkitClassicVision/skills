# Dual-Persistence Convention: `.run-project/` vs `.skill-pack/`

**Created**: 2026-05-28
**Applies to**: `/run-project` and `/skillify` skills
**Status**: Active convention

---

## Quick Reference

| Directory | Purpose | Lifetime | Created By | What It Holds |
|-----------|---------|----------|------------|---------------|
| `.run-project/` | Pipeline state | Ephemeral per project run | `/run-project` | Phase tracker, evals, handoffs, QA results, blind evals |
| `.skill-pack/` | Repo identity | Travels with repo, re-run monthly | `/skillify` | PROJECT.md, context layers, interfaces, ADRs |

**Both are gitignored.** Both are regenerated on demand.

---

## Why Two Directories?

` .run-project/` tracks **process**: Where are we in the pipeline? What did the blind evals say? What was the last handoff?

`.skill-pack/` describes **product**: What IS this repo? What are its modules, interfaces, boundaries? What to do when agents need to understand it?

Mental model:
- `.run-project/` = the meeting notes
- `.skill-pack/` = the product spec

One is a log of what happened during this project session. The other is a description of what the codebase IS.

---

## When Each Is Created

| Action | `.run-project/` | `.skill-pack/` |
|--------|----------------|----------------|
| `/run-project [path]` | Always | Auto-created if not present; uses existing if fresh |
| `/skillify [path]` | No touch | Always; appends non-destructively |
| `/organize [path]` only | If `.run-project/` exists | No touch |
| Re-run `/skillify` | No touch | Yes — appends with timestamp |

---

## When to Re-Run

### Re-run `/skillify` when:
- Major refactor completed
- 3+ new files or 1 new directory added
- New dependencies introduced
- Starting a new feature branch on brownfield
- Any AI agent says "I need more context about this repo"
- `.skill-pack/` is >7 days old and `/run-project` starts

### `.run-project/` auto-archives:
- After `Accept` phase completes
- When a new `/run-project` run starts on the same repo
- Old state is timestamped and moved to `.run-project/archives/`

---

## For Agents Consuming These

### If you are an **implementation agent** starting on a repo:
1. Read `.skill-pack/PROJECT.md` first (if it exists)
2. Then read PRD.md, AGENT_SPEC.md, or HANDOFF.md in that order
3. `.skill-pack/context/*.json` is machine-readable — use it for structure but prefer human-readable docs for decisions

### If you are a **pipeline orchestrator** (`/run-project`):
1. Check `.skill-pack/` status at Phase 1 (Grill)
2. If fresh (< 7 days), load `PROJECT.md` into context
3. If stale or missing, optionally run `/skillify` inline or defer
4. At Phase 6 (Context Layer), check repo size:
   - Greenfield (< 100 LOC): Merge Context Layer into To-Issues, produce HANDOFF.md
   - Brownfield (> 1000 LOC): Full Context Layer + SEEIT
   - Mid-size: Lean Context Layer

---

## Migration Notes

Before 2026-05-28, `/run-project` used only `.run-project/` and `codebase-organizer` bound to it. After 2026-05-28, `/skillify` produces `.skill-pack/` as the persistent identity layer. Older repos without `.skill-pack/` will auto-create it on next `/skillify` or `/run-project` invocation.

---

## Questions?

- "Should I commit either directory?" → No. Add both to `.gitignore`.
- "Can I delete `.run-project/` after Accept?" → Yes, but archive it first.
- "Can I delete `.skill-pack/`?" → Only if you no longer want agents to understand this repo. It regenerates on `/skillify`.
- "What if both exist and conflict?" → `.skill-pack/` wins on identity questions; `.run-project/` wins on pipeline state. They serve different purposes — conflicts are rare.
