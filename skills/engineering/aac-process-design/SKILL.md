---
name: aac-process-design
description: "Design or audit an agentic AI workflow with process-first guardrails: deterministic spine, evidence, gates, monitoring, and recovery before autonomy. Use when a user is designing an AI workflow, agent flow, workflow automation, vendor AI deliverable, or autonomy review."
---

# AAC Process Design, public version

Use this skill to design or audit agentic AI workflows. The default stance is process before autonomy: define the deterministic workflow, evidence chain, gates, and recovery loop before assigning judgment or write authority to agents.

This public copy intentionally omits any private rubric, private examples, customer names, internal memory references, and organization-specific operating rules.

## Workflow

1. Frame the workflow boundary
   - What event starts the workflow?
   - What outcome proves value?
   - Which actions are read-only, draft-only, human-approved, or autonomous?
   - What consequence class applies if the workflow is wrong?

2. Split deterministic spine from agent layer
   - Deterministic spine: APIs, state machines, event ingestion, validation, matching, dedupe, audit logs, retries, replay, proof artifacts.
   - Agent layer: summarization, anomaly detection, prioritization, drafting, decision packets, and escalation suggestions.
   - Do not use agents where a typed state machine or deterministic gate is safer.

3. Define gates and residue
   - Allowed actions, refused actions, human approvals, rollback path, escalation owner, suppression or eligibility checks, and audit trail.
   - Name the residue: what the system still cannot know, validate, or safely decide.

4. Design evaluation and monitoring
   - Test fixtures, edge cases, holdout examples, live shadow period, false-positive and false-negative review, operator feedback loop.
   - Include source-health checks and failure or recovery paths before live writes.

5. Produce the artifact
   - For design: architecture split, permission matrix, state diagram, source-owner question sheet, acceptance checklist.
   - For audit: pass or fail by section, missing evidence, kill or hold gates, and next safest action.

## Readiness rule

Do not call a workflow ready, production-ready, acceptable, or good to ship unless:

- The workflow boundary is graphable.
- Inputs and outputs are typed or explicitly constrained.
- Evidence sources are named and health-checked.
- Write actions are gated or explicitly approved.
- Failures produce alerts, logs, and a recovery path.
- A human owner can stop, override, or replay the workflow.

## Output style

Be concise and decision-oriented. Prefer:

- deterministic spine vs agent layer
- human-reviewed vs autonomous
- kill or hold gates
- next artifacts
- questions for the source owner

Avoid generic automation enthusiasm. Challenge weak autonomy claims directly.
