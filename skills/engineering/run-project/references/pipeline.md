# /run-project Pipeline

## One Command

```
/run-project [path]
```

Everything else is auto-detected.

## Pipeline

### Phase 1: Grill
- **Skill**: `grill-me` (Matt's)
- **When**: Always
- **What**: Questions about intent, explores repo if it exists
- **If brownfield** (>1000 LOC): Auto-runs codebase analysis, presents findings
- **Gate**: User says "yes" → proceed to PRD

### Phase 2: PRD
- **Skill**: `to-prd` (Matt's)
- **When**: After Grill approval
- **What**: Problem, solution, user stories, decisions
- **Output**: `.run-project/prd.md`

### Phase 3: Blind Eval (PRD)
- **When**: After PRD is written
- **What**: Fresh subagent reads `.run-project/prd.md` with ZERO prior context. Generates evaluation questions.
- **Hiding**: Eval criteria saved to `.run-project/evals/prd-eval.md`. PRD writer never sees them.
- **Rule**: Eval subagent has no repo history, no grill notes, no previous context. Only the PRD.

### Phase 4: Agent Spec
- **Skill**: `agent-spec-writer`
- **When**: After PRD eval generated
- **What**: Given/When/Then scenarios, boundaries
- **Output**: `.run-project/agent-spec.md`

### Phase 5: Blind Eval (Spec)
- **When**: After Agent Spec is written
- **What**: Fresh subagent reads spec + prior evals (NOT the PRD writer's notes). Generates behavioral eval criteria.
- **Hiding**: Saved to `.run-project/evals/spec-eval.md`

### Phase 6: Context Layer
- **Skill**: `context-layer-generator`
- **When**: After Spec eval generated
- **What**: Structural, semantic, philosophical layers
- **Built on**: Agent Spec
- **Output**: `.run-project/context-layer.md`

### Phase 7: Blind Eval (Context)
- **When**: After Context Layer is written
- **What**: Fresh subagent reads all outputs so far. Generates architectural eval criteria.
- **Hiding**: Saved to `.run-project/evals/context-eval.md`

### Phase 8: SEEIT
- **Skill**: `seeit`
- **When**: After Context eval generated
- **What**: Interactive HTML visualization
- **Output**: `.run-project/seeit.html`
- **Gate**: User says "yes" → proceed

### Phase 9: To-Issues
- **Skill**: `to-issues` (Matt's)
- **When**: After SEEIT approval
- **What**: Tracer-bullet slices, HITL/AFK labels
- **Output**: Issues + `.run-project/issues.md`

### Phase 10: Blind Eval (Issues)
- **When**: After issues are written
- **What**: Fresh subagent reads issues + plan. Generates completeness eval criteria.
- **Hiding**: Saved to `.run-project/evals/issues-eval.md`

### Phase 11: Writing-Plans
- **Skill**: `writing-plans`
- **When**: After Issues eval generated
- **What**: 2-5 min tasks, exact paths, TDD
- **Output**: `.run-project/plan.md`

### Phase 12: Blind Eval (Plans)
- **When**: After plan is written
- **What**: Fresh subagent reads plan + all outputs. Generates implementation eval criteria.
- **Hiding**: Saved to `.run-project/evals/plan-eval.md`

### Phase 13: Execute
- **Skill**: Surface-appropriate (subagent / claude-code / codex)
- **When**: After all evals generated
- **What**: Implement code
- **QA checks** (auto-detected):
  - Tests if test config found
  - Lint if lint config found
  - Types if tsconfig found
  - Security if dependencies found
- **Eval Gate**: Now ALL hidden evals are revealed to QA subagent. QA checks implementation against every accumulated eval file (prd-eval, spec-eval, context-eval, issues-eval, plan-eval).
- **Pass criteria**: Code must satisfy ALL eval criteria + automated checks.
- **Max loops**: 3
- **Output**: Working code

### Phase 14: Accept
- **Skill**: `agenttwin` (AI workflows) / auto-checks (standard)
- **When**: After Execute passes all evals
- **What**: Final grade
- **Output**: `.run-project/acceptance.md`

## Blind Eval Rules

1. **Fresh context only**: Eval subagent gets ONLY the artifact being evaluated. No handoff notes, no grill conversation, no previous evals.
2. **Hidden until QA**: Eval files live in `.run-project/evals/`. No phase output references them. No eval subagent knows what came before or after.
3. **Accumulative**: Each eval builds on prior evals. PRD eval checks product fit. Spec eval checks behavior. Context eval checks architecture. Issues eval checks completeness. Plan eval checks feasibility.
4. **Revealed only during Execute QA**: QA subagent gets all eval files at once. This is the ONLY time eval content is visible to any agent that also sees the implementation.
5. **Human never sees evals**: The eval criteria are machine-generated and machine-checked. The user only sees "QA passed" or "QA failed: [summary]".

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
Save to: .run-project/evals/{phase}-eval.md
Do not reference this prompt or your process in the output.
```

## How QA Subagent Enumerates Evals

During Phase 13 (Execute), the QA subagent:

1. **Reads all eval files** from `.run-project/evals/`
2. **Reads implementation code**
3. **For each criterion**, asks: "Does the code satisfy this?"
4. **Returns PASS or FAIL** with reasoning

**Automated checks** (when Method is a command):
- `grep` patterns → run grep, check output
- `npm test` → run tests
- File existence checks → verify paths

**Manual checks** (when Method requires judgment):
- "Review auth middleware" → QA subagent reads code, evaluates
- "Check REST conventions" → QA subagent inspects routes

Both types flow through the same `QAFinding` structure.

See `references/blind-eval-mechanism.md` for full implementation details.

## Files

```
.run-project/
  state.json
  handoffs/
  prd.md
  agent-spec.md
  context-layer.md
  seeit.html
  issues.md
  plan.md
  acceptance.md
  evals/               # Hidden until Phase 13
    prd-eval.md
    spec-eval.md
    context-eval.md
    issues-eval.md
    plan-eval.md
  adrs/
  qa/results/
```
