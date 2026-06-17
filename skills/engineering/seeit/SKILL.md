---
name: seeit
description: >-
  Comprehension instrument for AI-mediated work. Triggers when the user says "seeit", "show me the shape", "make this visible", or asks to see/understand/visualize a project, codebase, agent workflow, spec, or AI build at a structural level. Use this skill whenever the user wants to understand the SHAPE of something the AI is building or has built — code, agent workflows, agent runs, multi-step AI processes, spec compliance, or anything beyond plain chat. Use even when the user asks indirectly: "what did Codex just build", "is this spec doing what it says", "can you map out this agent", "I can't see what this does". The skill gathers from all available sources, maps the project structure, picks the right visual treatment for its actual shape, verifies adversarially, and produces an interactive HTML file the user opens to comprehend the build in 60 seconds.
---

# seeit

A comprehension instrument for AI-mediated work. Used when the AI is building, has built, or is running something against a spec, and the human needs to see what is actually there before approving, redirecting, or trusting it. Sibling system to Make Sense Protocol.

## When to activate

Triggers: "seeit" / "show me the shape" / "make this visible" / asks to visualize/map/understand an AI artifact / expresses comprehension gap on AI-built work. When unsure, default to triggering.

## Identity and purpose

Close the comprehension gap between humans and AI-mediated work. Produce a structured, visual, interactive picture readable in 60 seconds. Output answers: shape, state, drift, risk, openness.

## The five pillars (run every time, in order)

1. GATHER — pull from input, repo, available connectors such as project docs, cloud inventory, CRM, issue tracker, or prior handoffs, web search if blocked, past chats. Ask ≤2 multiple-choice clarifying questions only if truly blocked. State which sources were unavailable.

2. MAP — extract structured project model with these fields: project (name, type, intent, natural_shape), nodes (id, label, kind, state, ai_generated, confidence, owner, badges, notes), edges (from, to, strength, carries, tested), boundaries, drift (node/edge, spec_says, reality_is, severity), open_questions, assumptions, external_touchpoints (system, via, baa_covered, purpose). Every node must have state, kind, and owner or notes. Every edge must have strength. drift/open_questions/assumptions arrays are never empty if a spec exists.

3. SHAPE — pick visual treatment matching project's natural_shape: pipeline (horizontal flow), mesh (force-directed), tree (hierarchical), hub_spoke (radial), state_machine, cycle (loop), layered (stack), constellation (spatial), custom. Color is reserved for STATE only. Line weight = connection strength. Line style = coupling type. Badges = overlays.

4. VERIFY — adversarial second pass. Check: hidden decisions, hallucination surface, optimism bias, missing failure modes, spec drift (both directions), black-box opacity, PHI path coverage, single point of failure, self-description vs reality. Anything found gets added to drift/open_questions/badges. Never silently pass — always state outcome.

5. CAPTURE — save HTML. Then: quick look = no OB capture; committed project = offer OB canonical thought; drift event = WIP thought; repeat picture = update existing thought, don't duplicate.

## Locked visual vocabulary v0.1

Node shapes: rectangle (component) | rounded rectangle (AI-mediated) | cylinder (data store) | hexagon (external system) | diamond (decision)

Edges: thick solid arrow (strong/required) | thin solid arrow (working but fragile) | dashed arrow (conditional) | wavy arrow (human-mediated)

State colors: green (verified) | yellow (active) | red (drifted/failing) | grey (not started) | blue (AI-generated needs review)

Badges: red dot (failure mode) | yellow ? (open question) | shield (PHI) | $ (cost-significant) | BAA (BAA-covered vendor) | lock (auth checkpoint)

Boundaries: dashed enclosing box (scope/trust/compliance/team)

Annotations: side-by-side "spec: X / reality: Y" (drift) | footer assumption list

## Output format

Single-file interactive HTML, self-contained (all CSS/JS inline, no external CDN deps). Must include: title with project name + type + timestamp; the picture in chosen visual treatment; click-to-expand on every node showing notes/owner/confidence/badges; overlay toggle buttons (PHI, cost, drift, ownership); collapsible drift panel with spec/reality side-by-side; collapsible open-questions panel; assumptions footer (every assumption labeled); always-visible legend; mobile-readable layout.

Output flow: write HTML via file-creation tool → call present_files → brief chat summary (≤6 sentences: project type, dominant shape, top 3 findings, drift count, suggested next look). If no file creation: emit HTML in fenced code block with save-as-.html instruction.

## Mode-specific guidance

agent_cockpit / operator_dashboard → When visualizing an agent workflow that operators must use, add a visible interpretation layer before or beside the map: how to use it, what colors mean, what shapes mean, what lines mean, and where execution authority stops. For operator-facing cockpits, explicitly include path clarity, state clarity, boundary clarity, and proof clarity. Keep live-write boundaries visible.

relational_agent_cockpit → When the user asks to see agents relationally, do not stop at an agent stack. Add a relational node graph where each agent has its own card with role/authority lane, reads/checks/tests, important variables, output, stop rule, and status chips. Encode relationship lines by meaning: evidence/source flow, challenge/review loop, approval/gate flow, and blocked/refusal path. Run browser visual QA on the exact relational section and fix overlap/clipping before reporting completion.

packet_first_agent_cockpit → When the user prefers a cleaner operator cockpit, especially do not make agents the primary visual object. Make the deliverable/action packet primary, then offer synchronized lenses for directed process graph and agent-to-agent collaboration map. Default to Hybrid when both process path and collaboration need to be visible; use Graph for runbook/AAC/process debugging and Agents for prompt/handoff/delegation debugging. Run browser visual QA for selector readability, diagram clipping, and proof-text obstruction before reporting completion.

code_build → GATHER repo/README/manifests/commits/tests. SHAPE pipeline or layered. VERIFY hallucinated functions, missing error handling, untested paths, hidden side effects.

spec → GATHER doc + referenced docs + prior versions. SHAPE tree or mesh. VERIFY undefined terms, contradictions, ambiguous acceptance criteria, missing failure modes, unstated assumptions.

agent_workflow → GATHER workflow def, prompts, tool configs, system prompts. SHAPE state_machine or cycle. VERIFY exit conditions undefined, missing human override paths, prompt-injection surfaces, runaway loops.

agent_run → GATHER transcripts/logs/outputs/errors. SHAPE pipeline with state per step. VERIFY silent failures, retries masking errors, drift from intent.

multi_ai → GATHER all involved AI prompts, handoff format, coordination logic. SHAPE mesh or hub_spoke. VERIFY information loss between agents, conflicting outputs, authority confusion.

mixed → run both modes; drift comparison is the primary view.

## Clarification rules

Intent clear → proceed. One dominant interpretation → proceed, flag in assumptions. Truly blocking → one multiple-choice question. Still blocked → one more, max 2 total. Beyond 2 → produce partial picture with gaps marked, stop asking. Questions are always multiple-choice with 2-4 labeled options.

## Graceful degradation

File creation + present_files → full flow. File creation only → write file, give path. No file creation → fenced code block + save instruction. Connectors available → use in GATHER. No connectors → pasted input plus repo only, note limitation. Web search available → use for external docs. Always state at top which sources were used/unavailable.

## The 60-second comprehension test

Internal quality bar: could a colleague unfamiliar with this project look at the picture for 60 seconds and correctly explain (a) what it does, (b) where it is right now, (c) what could break, (d) what's still unresolved? If no, picture is not done. Adjust visual, simplify, regroup. Never ship a failing picture.

## What seeit does NOT do

Does not replace code review or testing. Does not generate/fix/modify the artifact. Does not visualize pure human projects (hiring, ops, strategy). Does not produce decorative diagrams — every element encodes information. Does not output static images — HTML must be interactive.

## Operating principle

The picture is the contract. If reality and picture disagree, the question is which to update. Never silently let the picture drift from reality. Better a smaller, accurate picture than a larger, optimistic one.

## Version

v0.1 — initial portable skill. v1.0 after first three real tests pass (data-entry v1 agent, Drafter+Reviewer workflow, live agent run static).
