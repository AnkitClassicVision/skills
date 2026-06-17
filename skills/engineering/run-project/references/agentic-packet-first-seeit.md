# Agentic packet-first Context + SEEIT pattern

Use this when `/run-project` reaches Context Layer and SEEIT for an agentic workflow, especially paid-ads, growth automation, or any workflow with possible external writes.

## Core lesson

For agentic paid-growth systems, the right SEEIT shape is often **packet-first, not agent-first**. The visual and context layer should follow the work object and evidence gates before showing bots or implementation modules.

Reusable spine:

```text
source-room -> allowlist -> readiness -> opportunity event spine -> proof packet -> autonomy gate -> approval packet
```

## How to apply

1. **Start from the work object**
   - Name the durable object moving through the system, e.g. `qualified paid-acquisition opportunity`.
   - Do not center the map on campaigns, ad accounts, or bot names unless the source-room proves that is the real work object.

2. **Make evidence/source health visible**
   - Show which source inputs are curated versus candidate/noisy.
   - Preserve missing transcript/doc/connector access as visible source-health gaps.
   - Do not infer readiness from recap emails, stale source packets, or broad search hits.

3. **Separate modules from live permissions**
   - Repo modules can support dry-run reporting, planning, and proof packets while live ad writes remain out of scope.
   - Context Layer should call out stale vocabulary drift, e.g. old campaign/booking/client-specific language that no longer matches the current PRD/spec.

4. **Use the autonomy gate as the visual boundary**
   - For paid ads, keep campaign/budget/bid/creative/tracking/conversion mutation behind an explicit AAC/human approval gate.
   - Label v1 outputs as static local proof packets or operator-review artifacts unless live-read and live-write gates have passed.

5. **Gate 2 handoff**
   - End SEEIT with a clean human question: `Does this shape look right enough to proceed to To-Issues?`
   - Update `.run-project/state.json` with exact artifacts, tests, visual QA, open decisions, and `next_phase: to_issues_after_human_gate_2`.

## Verification checklist

- [ ] Context Layer names the packet-first spine.
- [ ] SEEIT shows source-room, allowlist/readiness, proof packet, autonomy gate, and approval packet.
- [ ] Live writes are visually and textually outside v1.
- [ ] Stale source/repo vocabulary is called out rather than silently inherited.
- [ ] Tests and browser/visual QA are recorded in state.
- [ ] No production-readiness claim is made without AAC coverage.
