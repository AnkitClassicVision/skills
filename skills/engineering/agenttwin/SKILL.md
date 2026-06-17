---
name: agenttwin
description: "Diagnose, score, map, visualize, or accept an AI agent or workflow using a public closed-loop readiness report. Use for agent specs, automation workflows, vendor proposals, and agentic builds."
version: 1.0.0-public
license: MIT
---

# AgentTwin, public version

AgentTwin is a lightweight diagnostic instrument for AI agent workflows. It produces a plain-English wellness report plus an operator-grade process map.

This public copy intentionally omits private rubrics, private examples, internal customer references, and organization-specific capture rules.

## When to use

Use when the user is doing any of these on an AI agent, automation, or agentic workflow:

- Designing a new agent or automation
- Evaluating an existing agent or vendor proposal
- Modifying prompts, models, gates, or workflow components
- Diagnosing drift, hallucination, cost spike, missed escalation, or silent failure
- Accepting a build as ready for broader use
- Onboarding an engineer or operator to an agentic workflow

Do not use for generic AI questions, personal drafting, or pure code bugs unrelated to agent/workflow behavior.

## Report shape

Produce a self-contained markdown or HTML report with two views:

1. Summary view
   - Overall grade: A, B, C, D, or F
   - Five property cards in plain English:
     - Stays in lane
     - Checks facts
     - Checks before doing
     - Nothing is hidden
     - Has a stop button
   - Current vs ideal flow
   - Three-item action plan

2. Process map view
   - Nodes with runtime type, owner, input, output, status, and failure mode
   - Edges with trigger, contract, latency expectation, retry behavior, and audit trail
   - Cross-cutting state, memory, observability, and override model
   - Ranked recommendations by severity

## Five closed-loop properties

- Bounded: the workflow has a clear box, allowed actions, refused actions, and stop condition.
- Grounded: important claims and decisions cite source evidence that can be rechecked.
- Gated: risky writes, sends, labels, money movement, compliance actions, and human-impacting outputs require approval or deterministic checks.
- Observed: runs leave useful traces, metrics, alerts, and replayable proof.
- Governed: an owner can pause, override, audit, improve, and retire the workflow.

## Grading

- A: all five properties healthy.
- B: four healthy, one needs work, no broken property.
- C: at least one broken property or two needs-work properties.
- D: two or more broken properties.
- F: three or more broken properties, or any workflow can perform high-impact writes with no gate and no audit.

When uncertain between adjacent grades, downgrade.

## Verification before delivery

Before delivering the report:

- Confirm the workflow boundary and topology are explicit.
- Mark unknowns rather than inventing facts.
- Scan the report for raw emails, phones, tokens, credentials, message bodies, raw rows, or unnecessary personal data.
- State whether any external side effects were performed. Default should be none.
