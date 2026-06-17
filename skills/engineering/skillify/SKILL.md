---
name: skillify
description: >
  Turn any repository into a structured, skill-like decomposition that stays
  alive for context at all times. Invoke during spec diagramming, brownfield
  exploration, or at any point in a repo's lifecycle. Auto-creates a skill-pack
  directory with PROJECT.md (repo-as-skill manifest), context layers, and
  ADRs. Consumed by /run-project phases automatically. Works on any language.
version: 2.0.0
author: Public Maintainer
category: software-development
surfaces: [agent-cli, coding-agent]
tags: [skillify, organize, context, brownfield, repo-manifest, agent-context, universal]
---

# /skillify — Universal Codebase Skillification

## One-line pitch

Point it at any repo. Get a `.skill-pack/` manifest that turns the repo into a consumable skill for agents. Three context layers, annotated interfaces, inferred ADRs — machine-readable, always fresh, never destructive. Works on Python, JS, Go, Rust, Markdown, monorepos.

## Invocation

```
/skillify [path]
```

- `path`: Repo path (defaults to `.`)
- **Zero flags.** All behavior auto-detected:
  - Scans the repo live (never reads stale `.run-project/`)
  - Determines analysis tier from size:
    - **Surface** (<100 LOC): file map + extension distribution
    - **Shallow** (100–2000 LOC): + semantic contracts + entry points
    - **Deep** (>2000 LOC): + import graph, circular deps, deep scores, hotspots
  - Writes `.skill-pack/` directory with timestamped snapshots
  - Never overwrites destructively — appends with timestamps

## When to use it

| Situation | Why |
|-----------|-----|
| Starting `/run-project` on brownfield | Give the pipeline a pre-built skill manifest |
| During spec diagramming | `.skill-pack/PROJECT.md` feeds into SEEIT |
| Post-refactor audit | Re-skillify to update context |
| Onboarding a new AI agent | Point it at `.skill-pack/PROJECT.md` first |
| Any repo that agents need to understand | Reusable context, always current |

## What it produces

```
.skill-pack/
  PROJECT.md              # Repo-as-skill manifest
  context/
    structural.json       # Module map, import graph, circular deps
    semantic.json         # Type signatures, contracts, entry points
    philosophical.json    # Deep scores, hotspots, recommendations
  interfaces/
    {module}.md           # Annotated public API per module
  adrs/
    adr-{NNN}.md          # Inferred architectural decisions
```

## Tiered analysis

| Tier | Trigger | What gets analyzed |
|------|---------|------------------|
| **Surface** | <100 LOC | File map, extensions, module names, basic metadata |
| **Shallow** | 100–2000 LOC | + AST parsing for Python, function/class signatures, entry points, basic contracts |
| **Deep** | >2000 LOC | + Full import graph, circular dependency detection, deep module scoring, hotspots, refactoring recommendations |

## PROJECT.md format

```yaml
---
name: inventory
type: service
tier: deep
generated: 2026-05-29T00:51:47Z
---

## Role
One-paragraph description auto-inferred from repo name + module names.

## Module Map
| Module | Deep Score | Type | Files |
|--------|-----------|------|-------|
| db     | 8.4       | Data layer | 3 files |
| engine | 12.1      | Business logic | 5 files |

## Entry Points
- `src/main.py` — CLI entry
- `src/api/app.py` — Web server

## Interfaces
- `db` — 4 classes, 2 functions
- `engine` — 7 functions

## Non-Goals
- No auto-write to external systems
- (Extracted from PRD.md if present)

## Boundaries
- Decision-support only
- (Extracted from AGENT_SPEC.md if present)

## Context Files
- `context/structural.json` — machine-readable module map + import graph
- `context/semantic.json` — contracts + entry points
- `context/philosophical.json` — deep scores + hotspots + recommendations

## ADRs
- `adr-001.md` — Language choice
- `adr-002.md` — Database choice
- `adr-003.md` — Web framework
- `adr-004.md` — UI approach
- `adr-005.md` — Plugin architecture (if detected)
- `adr-006.md` — Testing approach
```

## Pipeline integration

```
/run-project [path]
  ↓
Phase 1: Grill
  ↓ detects .skill-pack/ exists
Auto-loads PROJECT.md → module map, boundaries, ADRs
  ↓ skips redundant questions
Phase 3: Context Layer
  ↓ reads structural.json, semantic.json, philosophical.json
Feeds into Agent Spec
  ↓
SEEIT consumes .skill-pack/context/ and .skill-pack/interfaces/
```

## Why `.skill-pack/` instead of `.run-project/`

- `.run-project/` is **pipeline state** — phase tracker, evals, handoffs
- `.skill-pack/` is **repo identity** — the repo's skill manifest, versioned with repo
- `.run-project/` is ephemeral; `.skill-pack/` travels with the repo
- Both are gitignored; both are regenerated on demand

## Re-running for freshness

| Trigger | Action |
|---------|--------|
| `/run-project` starts and `.skill-pack/` is >7 days old | Auto-re-skillify |
| Major refactor completed | Re-run `/skillify` |
| 3+ new files or 1 new directory | Re-run |
| New dependencies introduced | Re-run |
| Agent says "I need more context" | Re-run |

## Cross-surface behavior

| Surface | How |
|---------|-----|
| **Agent CLI** | Runs `scripts/skillify.py` directly. Full AST plus git analysis when available. |
| **Coding agent** | Uses built-in analysis, falls back to `skillify.py` if available. |
| **All** | Output format identical. `.skill-pack/PROJECT.md` is universal entry point. |

## Pitfalls

- **Execution Focus Rule**: When user is mid-execution of a multi-slice project (especially Execute phase), complete the current slice before discussing skill evolution, framework design, or meta-tooling improvements. If the user asks a tangential question, acknowledge briefly, capture it, then **ask**: "Finish current slice first, or pause to discuss?" User signal to defer: "Wait finish the project first."
- **Does not refactor** — only surfaces structure. Reorganization is human+agent decision.
- **ADRs are inferred** — they may reflect pattern, not intent. Human review required.
- **Circular deps in tests** — not flagged as critical. Only production code cycles matter.
- **Orphaned files** — some are entry points, CLI scripts, config. Not always bad.
- **Interface annotations are best-effort** — dynamic languages may lack complete signatures.
- **Do not commit `.skill-pack/`** — add to `.gitignore`. It is generated context, not source.
- **Deep analysis requires >2000 LOC** — smaller repos get surface/shallow tiers.
- **Import graph is Python-only today** — JS/Go/Rust modules get surface tier.
- **Multi-store schema propagation**: When adding store awareness to an existing schema, include `store_id` in every table that has store-scoped data. Add Store table for locations. This affects downstream ABC classification, inventory snapshots, recommendations, and sync jobs.

## Version history

- v2.0.0 (2026-05-29): Tiered analysis (surface/shallow/deep). Live repo scanning (never stale). Universal language support. FastAPI/Flask/Django detection. HTMX/React/Vue detection. Timestamped snapshots. Deep module scoring with hotspot detection.
- v1.0.0 (2026-05-28): Initial universal repo skillification. PROJECT.md manifest. .skill-pack/ directory. Inferred ADRs. Interface annotation. Auto-integration with /run-project.

## References

- `references/dual-persistence-convention.md` — Full explanation of `.run-project/` vs `.skill-pack/` distinction, when to use each, when to re-run, migration notes from pre-2026-05-28 conventions.
