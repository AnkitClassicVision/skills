# Execution-Phase Pitfalls

Pitfalls encountered during Phase 13 (Execute) and mid-slice implementation. Reference for QA subagent and future execution agents.

---

## 1. FastAPI TemplateResponse Signature

### Problem
```python
# WRONG — raises TypeError
return templates.TemplateResponse("index.html", {"request": request, "data": data})
```

### Correct Signature
```python
# RIGHT — Jinja2Templates.TemplateResponse(request, name, context)
return templates.TemplateResponse(request, "index.html", {"request": request, "data": data})
```

### Detection
- Error: `TypeError: TemplateResponse() takes 2 positional arguments but 3 were given`
- Or: template renders but `request` is undefined in template context

### Fix
Always pass `request` as the first positional argument, template name as second, context dict as third.

---

## 2. Deferring Tangential Questions Mid-Execution

### Scenario
User asks a side question while a slice is partially implemented (e.g., "can we create a universal method for X?").

### Wrong Response
Abandon current slice, answer the side question fully, start designing the new thing.

### Right Response
1. Acknowledge: "Good idea — capturing it."
2. Capture to OB or a todo item.
3. **Ask**: "Finish current slice first, or pause to discuss?"
4. If user says "finish first" or "not now" → return to execution immediately.
5. If user says "pause" → follow Pause/Resume guardrail (kill processes, write state, summarize).

### User Signals
- "Wait finish the project first"
- "not now"
- "later"
- "let's get back to..."
- "can we pause"

---

## 3. Clean Stopping Points

### Definition
A boundary where the code is in a consistent state: compiles, runs, and has no dangling partial implementations.

### Good Stopping Points
- After a slice's acceptance criteria are met
- After a successful QA loop (all evals pass)
- After writing a handoff document
- After a schema migration is applied and verified

### Bad Stopping Points
- Mid-file edit (uncommitted, untested)
- After adding a column but before updating queries
- After starting a server but before verifying it responds
- In the middle of a refactor that breaks imports

### Pause Protocol
1. Kill running processes (servers, background jobs)
2. Write `state.json` with: phase, slice, last completed action, next action
3. Verify the repo compiles / imports cleanly
4. Summarize: done vs. not done (5 bullets max)
5. Write resume instructions to local project notes or the task tracker
6. Comment on active task tracker entries: "Paused — do not continue until unblocked"

---

## 4. SQLAlchemy Session Lifecycle

See `skillify:references/sqlalchemy-session-patterns.md` for full coverage.

Quick reference:
- Extract values before `session.close()` — never return ORM objects from functions that close the session
- Use `try/finally` around session blocks
- For standalone scripts, add repo root to `sys.path` before importing `src.*`

---

## 5. Multi-Store Schema Propagation

When adding store awareness to an existing schema:
- Add `Store` table for locations
- Add `store_id` to EVERY table that has store-scoped data
- Update ALL queries to filter by `store_id` or support `combined=True`
- Update sync jobs to iterate stores
- Update ABC classification to support per-store + combined modes
- Update dashboard to show store selector

Failure mode: Partial propagation — some tables have `store_id`, others don't. Queries return wrong data. Recommendations cross store boundaries.

---

## 6. Background Process Hygiene

### Pattern
```python
# Start server
proc = terminal(background=True, command="uvicorn ...")

# Verify it responds
curl http://127.0.0.1:8000/

# When done or pausing
process(action="kill", session_id=proc.session_id)
```

### Pitfalls
- Leaving servers running across slices → port conflicts
- Not verifying after restart → serving stale code
- Background without `notify_on_complete` → silent failures

---

## 7. Import Path Issues in Standalone Scripts

Scripts in `scripts/` or `bin/` that import `src.*` modules fail with `ModuleNotFoundError: No module named 'src'`.

Fix: Add repo root to `sys.path` before imports.

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.db.schema import SessionLocal  # works now
```

See `skillify:references/sqlalchemy-session-patterns.md` for full explanation.
