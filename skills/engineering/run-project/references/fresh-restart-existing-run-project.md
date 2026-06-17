# Fresh Restart Over Existing `.run-project/`

Use this when the user asks to run a fresh `/run-project` on a repo that already contains prior `.run-project/` state, especially for agentic workflow repos.

## Pattern

1. **Inspect without destructive cleanup**
   - Confirm repo path and remote.
   - Check whether `.run-project/` exists.
   - Check git status, but do not reset, clean, or delete uncommitted work unless the user explicitly asks.

2. **Archive old run state outside the repo**
   - Copy `.run-project/` to `~/.agent/artifacts/<repo>-run-project-archive-<UTC>/`.
   - Preserve prior state even if it looks obsolete. It may contain accepted work, evals, or handoffs.

3. **Baseline before fresh artifacts**
   - Run the repo's detected test suite if available.
   - Record exact result, e.g. `81 passed`.
   - If checks fail, continue only if the failure is understood and the run target is discovery/spec, not implementation.

4. **Write fresh Phase 1 state**
   - `.run-project/organizer-report.json`
   - `.run-project/state.json`
   - `.run-project/handoffs/grill.md`
   - Include archive path, verification result, current phase/gate, and recommended Gate 1 direction.

5. **AAC rule for agentic repos**
   - If the repo involves agents, bots, AI workflows, paid-ads automation, or autonomous decisioning, AAC must trigger before readiness/acceptance claims.
   - It is safe to say: `AAC triggered; no production-readiness claim made.`

## Example: paid-ads agent workflow repo

A good Phase 1 framing for an agentic paid-ads repo is often not `prove one client live end-to-end first`.

For organization-style paid-ads agents, prefer a reusable target like:

> the organization Paid Ads Readiness + Proof Packet Agent v1

Use a client such as example tenant as source evidence and an example tenant packet, not as the entire product scope. This keeps the system reusable, lower risk, easier to maintain, and expandable across future clients.

## Pitfall

Do not treat `.run-project/state.json` as disposable if a prior run exists. Archive first, then overwrite intentionally.