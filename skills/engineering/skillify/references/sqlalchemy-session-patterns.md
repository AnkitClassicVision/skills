# SQLAlchemy Session Detach Patterns

## Problem

When SQLAlchemy objects are returned from a function that closes the session, accessing
any lazily-loaded attribute raises:

```
sqlalchemy.orm.exc.DetachedInstanceError:
  Instance <Frame> is not bound to a Session
```

## Root Cause

SQLAlchemy ORM objects hold a reference to their parent session. When `session.close()`
is called, the object becomes "detached." Accessing any attribute triggers a lazy load
attempt that fails because there is no active session.

## Solutions (in order of preference)

### 1. Extract values before closing the session (BEST — for data access)

```python
def generate_recommendations():
    session = SessionLocal()
    recommendations = []
    # ... create ORM objects ...
    session.commit()

    # Extract plain values BEFORE session.close()
    result = []
    for r in recommendations:
        result.append({
            "type": r.type,          # ✅ read while session is open
            "frame_id": r.frame_id,
            "qty": r.qty,
            "reason": r.reason,
            "confidence": r.confidence,
        })
    session.close()                  # ✅ session closed after extraction
    return result                    # ✅ returns dicts, not ORM objects
```

### 2. Return IDs instead of objects

```python
def create_frame(data):
    session = SessionLocal()
    frame = Frame(**data)
    session.add(frame)
    session.commit()
    frame_id = frame.id        # ✅ extract scalar before close
    session.close()
    return frame_id            # ✅ int, fully detached-safe
```

### 3. Use session context manager (safer but not always feasible)

```python
from contextlib import contextmanager

@contextmanager
def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

### 4. Set `expire_on_commit=False` (AVOID — masks the problem)

```python
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
```

This prevents expiration but hides the architectural issue. Prefer explicit extraction.

## When You Will Hit This

- Returning ORM objects from repository/service functions
- Printing ORM objects after `session.close()` (e.g., in `__main__` blocks)
- Serializing ORM objects to JSON without a `schema`/`dict` conversion
- Background threads that access ORM objects created in a different session

## Running Standalone Scripts

When a script outside the package root imports `src.` modules, it may fail with `ModuleNotFoundError: No module named 'src'`. This happens when the script's directory is not on `sys.path`.

**Fix**: Add the repo root to `sys.path` before imports.

```python
import sys, os
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from src.db.schema import SessionLocal, Store  # ✅ works now
```

**When you need this**: Scripts in `scripts/` or `bin/` directories, database seeders, migration helpers, or any standalone Python file that imports package modules but is not invoked via `python -m` from the package root.

## Detection

Look for this pattern in code reviews:

```python
session.commit()
session.close()
return orm_object        # ⚠️ DANGER: will DetachedInstanceError on access
```

## Test Coverage

Every repository function that returns ORM objects should have a test that accesses
the returned value outside the function scope.

```python
def test_recommender_returns_detached_safe():
    recs = generate_recommendations()
    assert len(recs) > 0
    # This will raise DetachedInstanceError if not extracted properly
    assert "type" in recs[0]
    assert recs[0]["confidence"] > 0
```
