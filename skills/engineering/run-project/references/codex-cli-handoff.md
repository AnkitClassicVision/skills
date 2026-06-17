# Run-project Codex handoff

Use when a `/run-project` effort is being handed from Hermes into an interactive Codex CLI session.

## Handoff file

Create or update:

`.run-project/handoffs/codex-cli-resume-context.md`

## Required contents

- Repo path
- Current `/run-project` phase
- Current human gate status
- Target and work object
- Completed phases and verification evidence
- Trusted anchor artifacts
- Stale artifacts to distrust or regenerate
- Allowed local surfaces
- Forbidden external-write surfaces
- Data-safety boundaries: no raw PHI, PII, transcripts, email bodies, phone numbers, IDs, or secrets
- Governance: AAC if the project is agentic, and no production-readiness claim unless the AAC pass has actually happened
- Exact next phase only if the human gate is approved

## First Codex instruction

Use a read-only instruction first:

```text
Read .run-project/handoffs/codex-cli-resume-context.md as the starting context for this session. Do not modify files yet. Summarize where we are in 5 bullets, confirm the current gate/decision needed, and then wait for the user's next instruction.
```

## Verification

Before telling the user the handoff is ready, poll/log Codex until it confirms the context is loaded and it is waiting. Report:

- process/session id
- repo path
- handoff file path
- pending gate or next phase
