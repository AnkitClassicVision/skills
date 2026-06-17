# Go-live / release-gate gap-closure plans

Use this reference when a user asks for Superpowers-style plan mode to close go-live, release, launch, or readiness blockers, especially in a no-send/no-write or human-review lane.

## Pattern

1. **Reproduce the current readiness verdict first.** Record the exact blocker labels, artifact paths, test command, and level-specific state before proposing fixes.
2. **Separate readiness levels.** Do not collapse internal review, human-review draft candidate mode, and external send/write mode into one “go live” answer. A plan can target Level 3 while explicitly keeping Level 4 false.
3. **Map each blocker to tasks.** Include a gap-to-task map near the top so the user can see every blocker is covered.
4. **Preserve fail-closed gates.** If a gate blocks go-live, plan to satisfy the gate with real source/context/QA evidence. Do not plan to weaken or bypass it unless the user explicitly authorizes a different lane.
5. **Use TDD where code changes are needed.** For diagnostics, approval artifacts, and external-action boundaries, write a failing test, implement the smallest code, run the narrow test, then commit specific files.
6. **Run the review-hardening loop before final readiness.** After the code slices pass, run a local code-review pass focused on authorization, scan coverage, inconsistent payloads, and level-boundary regressions. Fix Important findings that affect fail-closed behavior before running final live/source checks; do not treat review findings as “future work” when they could change the readiness verdict.
7. **Treat external actions as a separate lane.** Human approval artifacts may make a draft reviewable, but they must not imply the agent can send, create external drafts, write CRM, deploy, merge, or push.
8. **Verify the plan file itself.** Count tasks, check that every named gap appears, verify the target readiness fields are present, run `git diff --check`, then commit only the plan doc if the user asked for write-plan mode.

## Recommended plan sections

- Current verified baseline: artifact paths, tests, exact verdict fields.
- Current blockers: numbered list of safe labels.
- Target acceptance JSON: explicit expected booleans and blocker list.
- Non-negotiable boundaries: no sends/writes/deploys/merges/pushes unless separately authorized.
- Gap-to-task map.
- Bite-sized tasks with: Objective, Files, failing test or command, expected result, implementation step, verification, commit command.
- Final verification checklist.
- Final decision language: e.g. “Level 3 yes / Level 4 no” or “No; remaining blockers are …”.

## Pitfalls

- Do not let “go live” mean “external send/write” by default. Ask the code/artifacts what level is ready.
- Do not plan around manually forcing a green status; derive readiness from the canonical run card/source health artifact.
- Do not hide unresolved context as “draft-ready.” Incomplete context remains retrieve-context/context-blocked.
- Do not commit unrelated generated artifacts or dirty worktree changes while saving a plan.
