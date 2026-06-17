# Blind Eval Mechanism

## How Evals Are Generated

After each artifact phase, a fresh subagent with ZERO context generates eval criteria.

**Process:**
1. Subagent reads ONLY the artifact (e.g., `.run-project/prd.md`)
2. No handoff notes, no grill conversation, no process history
3. Generates 5-10 specific, testable pass/fail criteria
4. Saves to `.run-project/evals/{phase}-eval.md`
5. No upstream agent ever sees this file

**Prompt template:**
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

## Eval File Format

```markdown
# PRD Eval Criteria

## E1: User authentication required
- Check: All API endpoints except /health require a valid JWT
- Method: Review auth middleware in src/middleware/
- Pass if: No endpoint allows unauthenticated access

## E2: Rate limiting
- Check: Requests are throttled per user
- Method: Check src/rate-limiter.js
- Pass if: 429 returned after limit exceeded

## E3: Password hashing
- Check: Passwords never stored plaintext
- Method: grep -r "password" src/ --exclude test
- Pass if: Only bcrypt/argon2 references found
```

Each eval item has:
- **Check**: What to verify
- **Method**: How to verify (can be automated command or manual review)
- **Pass if**: Clear pass condition

## How QA Subagent Enumerates Evals

During Execute phase, the QA subagent:

1. **Reads all eval files** from `.run-project/evals/`
2. **Reads implementation code**
3. **Parses each eval item** via regex: `## (E\d+): Title\nBody`
4. **Extracts fields** from markdown: `**Method**:` and `**Pass if**:`
5. **Runs automated checks** when Method is a known command:
   - `grep` → runs grep, checks `Pass if` for "found" vs "no matches"
   - `file exists` → verifies path exists on disk
   - `cmd:` → runs arbitrary shell command, checks exit code
6. **Flags for AI review** when no automated Method exists
7. **Returns PASS or FAIL** per criterion

**Automated check types supported:**

| Method prefix | Example | Behavior |
|---------------|---------|----------|
| `grep` | `grep -r "bcrypt" src/` | Runs grep. Pass if matches found (or not found, per Pass if) |
| `file exists` | `file exists src/auth.js` | Checks path exists |
| `cmd:` | `cmd: npm run test:auth` | Runs command, checks exit code == 0 |
| (none) | `Check: Auth uses JWT` | Flags as `warning` for AI QA subagent |

**Pass if logic for grep:**
- "found / exists / present / match" → expects grep to find matches
- "no / not / absent / missing / no matches" → expects grep to find nothing
- Missing Pass if → falls back to AI review flag

## QA Loop Integration

```python
def run_blind_evals(repo_path: str) -> List[QAFinding]:
    evals_dir = Path(repo_path) / '.run-project' / 'evals'
    eval_files = sorted(evals_dir.glob('*-eval.md'))

    for eval_file in eval_files:
        phase = eval_file.stem.replace('-eval', '')
        content = eval_file.read_text()

        # Parse eval items (## E1, ## E2, etc.)
        eval_items = re.findall(r'## (E\d+): (.+?)\n(.*?)(?=## E\d+:|$)', content, re.DOTALL)

        for eval_id, eval_title, eval_body in eval_items:
            finding = evaluate_criterion(repo_path, phase, eval_id, eval_title, eval_body)
            if finding:
                findings.append(finding)

    return findings
```

**In the QA loop:**
```python
def run_qa_loop(repo_path: str, max_iterations: int = 3):
    for iteration in range(1, max_iterations + 1):
        findings = []

        # Automated checks
        findings.extend(run_tests(repo_path))
        findings.extend(run_linter(repo_path))
        findings.extend(run_type_checker(repo_path))
        findings.extend(run_security_scan(repo_path))

        # BLIND EVALS — REVEALED HERE ONLY
        findings.extend(run_blind_evals(repo_path))

        report = generate_qa_report(iteration, findings)

        if report.passed:
            return {'status': 'passed'}

        # Send findings back to implementation agent
        send_to_implementation_agent(findings)
```

## Information Barrier

| Agent | Sees Evals? | Sees Implementation? | Notes |
|-------|------------|---------------------|-------|
| PRD writer | No | No | Creates PRD |
| PRD eval subagent | No (writes them) | No | Only reads PRD |
| Spec writer | No | No | Only reads PRD + handoff |
| Spec eval subagent | No (writes them) | No | Only reads spec + prior evals |
| Context generator | No | No | Only reads spec |
| Context eval subagent | No (writes them) | No | Only reads context + prior evals |
| Issues writer | No | No | Only reads context + SEEIT |
| Issues eval subagent | No (writes them) | No | Only reads issues |
| Plan writer | No | No | Only reads issues |
| Plan eval subagent | No (writes them) | No | Only reads plan + prior evals |
| **QA subagent** | **YES** | **YES** | **First agent to see both** |
| Implementation agent | No (until QA feedback) | Yes | Fixes based on QA findings |

## Accumulation Pattern

Each eval builds on prior evals:

- **PRD eval**: Product fit criteria (what must the product do?)
- **Spec eval**: Behavioral criteria (how must it behave?)
- **Context eval**: Architectural criteria (how must it be structured?)
- **Issues eval**: Completeness criteria (are all requirements covered?)
- **Plan eval**: Implementation criteria (can this plan actually be built?)

At Execute QA, all 5 eval files are read together. The implementation must satisfy ALL accumulated criteria.

## User Visibility

- User NEVER sees eval files directly
- User sees: "QA passed" or "QA failed: [summary]"
- If QA fails, user sees the finding messages (not the eval criteria themselves)
- Human gates remain at Grill and SEEIT only
