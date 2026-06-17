# Artifact Templates

Read this file before generating output. Produce all three artifacts, clearly separated.

## Artifact 1: MODULE_MANIFEST.md (Structural Context)

Place at the root of the module's directory.

```markdown
# Module Manifest: {MODULE_NAME}

> {One-line purpose}

**Context captured:** {YYYY-MM-DD} by {person/team}
**Last validated:** {YYYY-MM-DD}

## Dependencies (what this module depends on)

| Dependency | Type | Description |
|-----------|------|-------------|
| {name} | {sync API / async event / shared DB / message queue / library} | {what it uses and why} |

## Dependents (what depends on this module)

| Dependent | Type | Description |
|----------|------|-------------|
| {name} | {sync API / async event / shared DB / consumer} | {what it consumes and why} |

## Data Flows

| Direction | Source/Target | Data | Notes |
|-----------|--------------|------|-------|
| Reads | {source} | {what data} | {access pattern} |
| Writes | {target} | {what data} | {access pattern} |

## Shared Resources

| Resource | Shared With | Risk Notes |
|----------|------------|------------|
| {cache/DB/queue} | {other modules} | {contention, consistency concerns} |

> **DARK CODE HOTSPOT**: {If any shared resource has unclear consumers, flag it here with what is known and what is unknown.}

## Deployment Model

- **Type:** {own service / monolith module / serverless / etc.}
- **Runtime:** {language, framework, version}
- **Infrastructure:** {where it runs}

## Ownership

- **Team:** {team name}
- **On-call:** {rotation or contact}
```

## Artifact 2: BEHAVIORAL_CONTRACTS.md (Semantic Context)

Place alongside interface definitions or at the module root.

```markdown
# Behavioral Contracts: {MODULE_NAME}

**Context captured:** {YYYY-MM-DD} by {person/team}
**Last validated:** {YYYY-MM-DD}

---

## {Interface Name}

> {One-line purpose}

| Property | Value |
|----------|-------|
| **Idempotent** | {Yes / No / Conditional: explain} |
| **Failure behavior** | {What the caller sees on failure: error code, timeout, default value, silent drop} |
| **Performance envelope** | {Expected latency, throughput limits, degradation under load} |
| **Side effects** | {State changes, downstream triggers, cache invalidation} |
| **Retry guidance** | {Safe to retry: yes/no. Backoff: {recommendation}. Dangerous if: {condition}} |
| **Data classification** | {PII / credentials / financial / public / internal} |

### Failure Modes

| Failure | Caller Sees | Recovery |
|---------|------------|----------|
| {scenario} | {behavior} | {what to do} |

### Warnings

- {Any non-obvious behavioral quirks, edge cases, or "looks wrong but is intentional" notes}

---

{Repeat for each interface}
```

## Artifact 3: DECISION_LOG.md (Philosophical Context)

Place at the module root. Structured as a list of decisions.

```markdown
# Decision Log: {MODULE_NAME}

**Context captured:** {YYYY-MM-DD} by {person/team}
**Last validated:** {YYYY-MM-DD}

---

## DL-001: {Decision title — what was decided, one sentence}

- **Date:** {YYYY-MM-DD or approximate: "pre-2024", "Q3 2025"}
- **Context:** {What problem or constraint prompted this decision}
- **Alternatives considered:**
  - {Option A}: Rejected because {reason}
  - {Option B}: Rejected because {reason}
- **Consequences:**
  - Enables: {what this decision makes possible}
  - Constrains: {what this decision prevents or limits}
- **Warning: {What would break if this decision were reversed. Be specific. This is the most important field for preventing AI-induced regressions.}**

---

## DL-002: {Next decision}

{Repeat pattern}

---

## Unknown Decisions

{List any architectural choices where the reasoning is unknown. For each:}

### UD-001: {What the code does that seems intentional but has no known rationale}

- **Observed behavior:** {what the code does}
- **Hypothesis:** {best guess, if any}
- **Risk:** Treat as load-bearing. Do not modify without investigation.
- **Original author:** {departed / unknown / unreachable}
```

## Output Notes

- Number decisions sequentially (DL-001, DL-002...) and unknowns (UD-001, UD-002...) for easy reference.
- Bold all **Warning** fields — they are the highest-value content for preventing regressions.
- If the user couldn't answer a question, record the gap explicitly rather than omitting it.
- Keep language precise and technical. Avoid filler.
