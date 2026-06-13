---
name: scout
description: Use when a user asks whether a new external thing, idea, article, tool, repo, framework, competitor move, workflow, or opportunity is worth caring about now. Runs a memory-first triage, maps where the thing applies, and returns exactly one verdict: GO-now, PARK, or KILL.
---

# SCOUT

SCOUT is a triage skill for deciding whether a new thing should change what you do.

Use it when someone brings an outside signal and asks questions like:

- "Should I care about this?"
- "Is this useful for us?"
- "Where would this apply?"
- "Should we act on this now or save it for later?"
- "Does this change our current plan?"

SCOUT does not merely summarize. It decides whether the thing creates a decision delta.

## Core distinction

- **Research maps what the thing is.**
- **SCOUT decides whether the thing changes what you should do.**

## Verdicts

Return exactly one verdict.

- **GO-now:** There is a real apply edge to an active goal, project, workflow, product, or bottleneck, the first step is cheap enough, and acting now beats current alternatives.
- **PARK:** There is a real apply edge, but it is not worth acting on yet because timing, maturity, confidence, capacity, or priority is wrong. Include a clear revisit trigger.
- **KILL:** There is no meaningful apply edge, or the cost/risk outweighs the value. Include the disqualifier so the topic stays dead unless facts change.

## Operating principle: scan before researching

Before deep research, check whether enough context already exists.

Use whatever context sources are available in the current environment:

- current conversation
- project docs
- local files
- team knowledge base
- memory system
- notes database
- prior decisions
- issue tracker
- CRM or analytics summaries, only if the user authorized that context
- web search, only when current external facts are needed

If prior context already contains a recent, sound take, do not re-run a full investigation. Check only the fact that could flip the verdict.

## Branches

Choose one branch and say which branch you used.

### 1. Empty context → Full pass

Use when there is no useful prior context.

Steps:

1. Identify what the thing is.
2. Identify its mechanism: how it creates value or risk.
3. Identify evidence quality: proof, examples, maturity, adoption, caveats.
4. Project it onto active goals, projects, workflows, products, and bottlenecks.
5. Score value, cost, maturity, urgency, and current-load fit.
6. Return GO-now, PARK, or KILL.

### 2. Recent take exists → Surgical check

Use when a recent prior decision or analysis already exists.

Steps:

1. State the existing take.
2. Identify the one fact that could change the verdict.
3. Check only that fact.
4. Confirm or update the verdict.

### 3. Stale take exists → Stale refresh

Use when prior context exists but key facts may have changed.

Steps:

1. State the old take.
2. List the aged assumptions.
3. Refresh only the stale assumptions.
4. Confirm or update the verdict.

## Projection rule

Do not say "this could be useful" in the abstract.

For every meaningful target, mark one of:

- **APPLY:** The thing has a real edge to the target.
- **NOT-APPLY:** No real edge found.
- **UNKNOWN:** Not enough context to judge.

An APPLY edge must name:

1. the concept from the new thing
2. the target it affects
3. why the connection matters
4. confidence: Hunch, Reasoned, or Evidenced

Example:

```text
APPLY: "lightweight eval harness" → customer-support bot QA
Why: it gives a repeatable way to catch regressions before release.
Confidence: Reasoned.
```

## Scoring dimensions

Score briefly, not as theater.

- **Usefulness size:** How much changes if this works?
- **Adoption cost:** Time, complexity, risk, blast radius.
- **Maturity:** How proven is it?
- **Current-load fit:** Does it beat what is already in flight?
- **Decision delta:** What would be done differently if this verdict is accepted?

If the decision delta is small, say so and prefer PARK or KILL.

## Required output shape

Use this shape unless the user asks for another format:

```text
What I SCOUTed: <topic/link/artifact>
Frame: <what it is + what decision it bears on>
Context scan: empty / recent_take / stale_take
Branch used: Full pass / Surgical check / Stale refresh
Verdict: GO-now / PARK / KILL
ELI5: <one sentence>
Decision delta: <what changes, or "no material shift">

Applies:
- <target>: <APPLY edge + confidence>

Does not apply:
- <target>: <plain reason>

Why now / why not now:
- <1-3 bullets>

Smallest safe next move:
- <read-only or reversible step, or first execution step for GO>

Capture:
- <save / draft capture packet / skip, based on the user's memory policy and available tools>
```

## Capture rule

If the verdict is durable, offer to capture it in the user's chosen system of record. Do not assume a specific memory product or private database.

Capture only sanitized material:

- topic
- verdict
- apply edges
- decision delta
- revisit trigger for PARK
- disqualifier for KILL
- evidence links or filenames, if safe

Do not capture secrets, private identifiers, raw transcripts, customer records, health data, payment data, or confidential business details unless the user's environment and policy explicitly allow it.

If no capture tool is available, emit a short capture packet the user can paste elsewhere.

## Guardrails

- Do not investigate before the context scan.
- Do not re-argue a recent sound decision.
- Do not call something GO-now unless it beats current load.
- Do not mark APPLY without a real target and confidence level.
- Do not treat curiosity as priority.
- Do not let a GO verdict imply permission for risky action.
- External sends, production writes, deployments, purchases, ads, CRM/EHR/finance writes, and human-impacting labels still need explicit approval.

## Quick examples

### GO-now

```text
Verdict: GO-now
Decision delta: Add a 30-minute prototype to this week's plan because it directly reduces onboarding time for the active support workflow.
Smallest safe next move: Build a read-only mock using 5 anonymized examples.
```

### PARK

```text
Verdict: PARK
Decision delta: Useful for future reporting, but not worth interrupting the current launch.
Revisit trigger: Re-check when reporting setup takes more than 2 hours/week or after the launch is complete.
```

### KILL

```text
Verdict: KILL
Decision delta: None.
Disqualifier: No active project has a real APPLY edge, and adoption would add another tool without removing work.
```
