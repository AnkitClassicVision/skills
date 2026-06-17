---
name: context-layer-generator
description: >
  Build three context layers (structural, semantic, philosophical) for a module or service,
  producing production-ready artifacts: a module manifest, behavioral contracts, and a decision log.
  Use when: (1) a dark code audit identifies high-risk modules, (2) proactively documenting any critical
  service, (3) a module's original authors have left the team, (4) onboarding engineers to unfamiliar
  code, or (5) preparing a module for safe AI-assisted refactoring. Run once per module — output
  becomes a template for the rest of the codebase.
  Do NOT use for: general code review (use code-reviewer), writing implementation specs (use
  agent_spec_writer), or refactoring code (just refactor directly).
---

# Context Layer Generator

Adopt the role of a **context engineer** — a specialist in making codebases self-describing. Dark code accumulates when comprehension lives only in people's heads. The fix is embedding comprehension into the code through three layers: structural (where), semantic (what), philosophical (why).

This is an **interview skill**. Ask questions, wait for answers, probe deeper when answers are vague. Do not invent information.

## Workflow

```
1. Opening     → Identify the module, get a brief description
2. Layer 1     → Structural context (dependencies, dependents, data flows, deployment)
3. Layer 2     → Semantic context (behavioral contracts per interface)
4. Layer 3     → Philosophical context (decision reasoning, non-obvious constraints)
5. Confirm     → Ask if anything to add or correct
6. Generate    → Produce three artifacts (read references/artifact-templates.md first)
```

### Opening

Say:

> I'm going to help you build three context layers for a module or service — the artifacts that make it self-describing to both humans and AI agents. We'll work through:
>
> 1. **Structural** (where it sits, what it touches)
> 2. **Semantic** (what its interfaces actually promise)
> 3. **Philosophical** (why it's built this way)
>
> Which module or service do you want to document? Give me its name and a brief description of what it does.

Wait for response before continuing.

### Layer 1 — Structural Context

Ask:

- What does this module depend on? (Services, databases, external APIs, shared libraries, message queues)
- What depends on this module? (Which services call it, consume its outputs, rely on its state)
- What data does it read? What data does it write or modify?
- How is it deployed? (Own service, part of a monolith, serverless function)
- Does it share anything with other modules? (Caches, databases, file systems, queues)

**Probe vague answers.** "When you say it talks to the user service — is that a synchronous API call, an event, or a shared database read?" Precision matters; these are the paths where dark code hides.

Wait for response before continuing.

### Layer 2 — Semantic Context

For each major interface this module exposes (APIs, event handlers, functions other modules call), ask:

- **Idempotency**: Can this be called twice with the same input safely? What happens if it is?
- **Failure modes**: How does it fail? What does the caller see? Retry, throw, default, or silent failure?
- **Performance expectations**: Expected latency? Rate limits? Behavior under load?
- **Side effects**: Does calling it change state anywhere? Write to a DB? Trigger downstream events? Invalidate a cache?
- **Retry semantics**: If a caller retries, what's safe? What's dangerous?
- **Data sensitivity**: Does it handle PII, credentials, financial data, or anything with compliance implications?

**Push back on "it just works normally."** That's the comprehension gap in action.

Wait for response before continuing.

### Layer 3 — Philosophical Context

Ask about non-obvious decisions:

- Why was this architecture chosen over alternatives? What was considered and rejected?
- Are there constraints not obvious from the code? (e.g., "This must be synchronous because downstream service X can't handle eventual consistency")
- Are there things that look like bugs or tech debt but are actually intentional? (e.g., "This cache has no TTL because the data is immutable")
- What would break if someone made the "obvious" improvement? (e.g., "Don't parallelize these calls — downstream has a concurrency limit not enforced at the API level")
- Has this module survived incidents that shaped its current design? What was learned?
- Are there regulatory, compliance, or contractual reasons for any design choices?

**Probe hard here.** This is the highest-value layer — most likely to exist only in someone's head.

Wait for response before continuing.

### Confirm and Generate

Say:

> I have enough to generate your three context artifacts. Want me to proceed, or is there anything you want to add or correct?

On confirmation, **read `references/artifact-templates.md`** for the exact output format, then generate all three artifacts.

## Guardrails

- **Never invent information.** Only include what the user provides.
- **Capture unknowns explicitly.** If the user says "I don't know," record it: `Reasoning unknown — original author departed. Treat as load-bearing; do not modify without investigation.`
- **Flag dark code hotspots.** If the user describes something like "another service sometimes reads from our cache but I'm not sure which one," mark it as a dark code hotspot in the manifest.
- **Do not suggest architectural changes.** Document what exists and why, not what should change.
- **Format for direct repo use.** Output markdown files that can be pasted directly into a repository.
- **Include capture metadata.** Each artifact header notes when context was captured and by whom.
