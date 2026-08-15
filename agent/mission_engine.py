#!/usr/bin/env python3
"""mission_engine.py — HEER Mission Engine (Phase 3.1).

Business-level mission lifecycle: create, track, control, and complete
business missions. This is the foundational engine later phases build on.
It deliberately does NOT implement task graphs / DAGs / task execution /
parallel execution / agent orchestration — those belong to later phases.

Mission model (SQLite, stored in .heer/ like approvals/audit):
  mission_id, objective, status, priority, created_at, updated_at,
  created_by, context (json), constraints (json), result (json),
  error, metadata (json)

State machine (every transition is validated; invalid transitions are
rejected safely — no partial updates, no side effects):

  CREATED -> PLANNED -> READY -> RUNNING -> PAUSED -> COMPLETED
  RUNNING -> FAILED
  CREATED / PLANNED / READY / RUNNING / PAUSED -> CANCELLED

  Terminal states: COMPLETED, FAILED, CANCELLED (no further transitions).

Security:
  - all SQL is parameterized (no string interpolation of user input)
  - all inputs are validated (length, enums, JSON-serializable)
  - no code execution, no network, no filesystem access outside the
    mission SQLite state file
  - no secrets are ever logged or exposed

Run:  python3 -m agent.mission_engine --self-test
"""

import json
import os
import sqlite3
import time
import uuid

from . import audit
from . import data

# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

STATUS_CREATED = "CREATED"
STATUS_PLANNED = "PLANNED"
STATUS_READY = "READY"
STATUS_RUNNING = "RUNNING"
STATUS_PAUSED = "PAUSED"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"
STATUS_CANCELLED = "CANCELLED"

ACTIVE_STATUSES = (
    STATUS_CREATED, STATUS_PLANNED, STATUS_READY,
    STATUS_RUNNING, STATUS_PAUSED,
)
TERMINAL_STATUSES = (STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED)
VALID_STATUSES = ACTIVE_STATUSES + TERMINAL_STATUSES

VALID_PRIORITIES = ("low", "medium", "high", "critical")

# Allowed transitions. Terminal states have no outgoing edges.
VALID_TRANSITIONS = {
    STATUS_CREATED: frozenset({STATUS_PLANNED, STATUS_CANCELLED}),
    STATUS_PLANNED: frozenset({STATUS_READY, STATUS_CANCELLED}),
    STATUS_READY: frozenset({STATUS_RUNNING, STATUS_CANCELLED}),
    STATUS_RUNNING: frozenset({STATUS_PAUSED, STATUS_COMPLETED,
                               STATUS_FAILED, STATUS_CANCELLED}),
    STATUS_PAUSED: frozenset({STATUS_RUNNING, STATUS_CANCELLED}),
    STATUS_COMPLETED: frozenset(),
    STATUS_FAILED: frozenset(),
    STATUS_CANCELLED: frozenset(),
}

MAX_OBJECTIVE = 1000
MAX_ERROR = 2000
MAX_CREATED_BY = 100


def state_machine():
    """Public read-only view of the validated state machine."""
    return {
        state: sorted(targets)
        for state, targets in VALID_TRANSITIONS.items()
    }


def can_transition(current_status, target_status):
    """Validate a transition.

    Returns (allowed: bool, reason: str). Never raises.
    """
    if current_status not in VALID_STATUSES:
        return False, f"unknown current status '{current_status}'."
    if target_status not in VALID_STATUSES:
        return False, f"unknown target status '{target_status}'."
    if current_status in TERMINAL_STATUSES:
        return False, (f"mission is {current_status} (terminal); "
                       "no further transitions allowed.")
    if target_status not in VALID_TRANSITIONS[current_status]:
        return False, f"invalid transition {current_status} -> {target_status}."
    return True, ""


# ---------------------------------------------------------------------------
# SQLite state (same .heer/ state dir pattern as approvals.py / audit.py)
# ---------------------------------------------------------------------------


def _state_dir():
    root = data.data_root() or os.path.abspath(".")
    d = os.path.join(os.path.abspath(os.path.join(root, "..")), ".heer")
    os.makedirs(d, exist_ok=True)
    return d


def _db_path():
    return os.path.join(_state_dir(), "mission_engine.sqlite3")


def _conn():
    c = sqlite3.connect(_db_path())
    c.execute(
        """CREATE TABLE IF NOT EXISTS missions (
            mission_id TEXT PRIMARY KEY,
            objective TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'CREATED',
            priority TEXT NOT NULL DEFAULT 'medium',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            created_by TEXT NOT NULL DEFAULT 'HEER',
            context TEXT,
            constraints TEXT,
            result TEXT,
            error TEXT,
            metadata TEXT
        )"""
    )
    return c


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _loads(raw, fallback=None):
    try:
        return json.loads(raw or "")
    except (json.JSONDecodeError, TypeError):
        return fallback


def _dumps(value):
    """Serialize a value to JSON text, or None when null / unserializable."""
    if value is None:
        return None
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return None


def _json_error(value):
    """Return an error string when value isn't JSON-serializable, else None."""
    if value is None:
        return None
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return "must be JSON-serializable"
    return None


def _clean_priority(priority):
    if priority is None:
        return "medium"
    p = str(priority).strip().lower()
    return p if p in VALID_PRIORITIES else None


# ---------------------------------------------------------------------------
# Audit hook (Phase 3.2 — reuses audit.record, single audit system)
# ---------------------------------------------------------------------------


def _audit(intent, mission_id, success, detail=""):
    """Record a mission engine event; never lets audit failure break the engine."""
    try:
        audit.record(
            request=f"{intent} mission={mission_id} {detail[:200]}",
            intent=intent,
            agent_id="mission_engine",
            tools=[intent],
            inputs={"mission_id": mission_id, "detail": detail[:500]},
            outputs={"success": success},
            approval={"blocked": False},
            success=success,
            lat_ms=0,
        )
    except Exception:  # noqa: BLE001 — audit is best-effort
        pass


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def create_mission(objective, priority="medium", created_by="HEER",
                   context=None, constraints=None, metadata=None):
    """Create a new mission in state CREATED.

    Returns {"ok": True, "mission": {...}} or {"ok": False, "error": "..."}.
    All inputs validated; no side effects on validation failure.
    """
    objective = (objective or "").strip()
    if not objective:
        return {"ok": False, "error": "objective is required."}
    if len(objective) > MAX_OBJECTIVE:
        return {"ok": False, "error":
                f"objective must be {MAX_OBJECTIVE} characters or fewer."}

    pri = _clean_priority(priority)
    if pri is None:
        return {"ok": False, "error":
                "priority must be one of: low, medium, high, critical."}

    created_by = ((created_by or "").strip()[:MAX_CREATED_BY] or "HEER")

    for label, value in (("context", context),
                         ("constraints", constraints),
                         ("metadata", metadata)):
        err = _json_error(value)
        if err:
            return {"ok": False, "error": f"{label} {err}."}

    now = time.time()
    mid = "mis_" + uuid.uuid4().hex[:12]
    c = _conn()
    try:
        c.execute(
            "INSERT INTO missions (mission_id, objective, status, priority, "
            "created_at, updated_at, created_by, context, constraints, "
            "result, error, metadata) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (mid, objective, STATUS_CREATED, pri, now, now, created_by,
             _dumps(context), _dumps(constraints), None, None, _dumps(metadata)),
        )
        c.commit()
    finally:
        c.close()
    _audit("mission_create", mid, True, f"status={STATUS_CREATED}")
    return {"ok": True, "mission": get_mission(mid)}


def get_mission(mission_id):
    """Return a mission dict, or None when not found / invalid id."""
    if not mission_id or not isinstance(mission_id, str):
        return None
    c = _conn()
    try:
        row = c.execute(
            "SELECT mission_id, objective, status, priority, created_at, "
            "updated_at, created_by, context, constraints, result, error, "
            "metadata FROM missions WHERE mission_id=?",
            (mission_id,),
        ).fetchone()
    finally:
        c.close()
    if row is None:
        return None
    return {
        "mission_id": row[0],
        "objective": row[1],
        "status": row[2],
        "priority": row[3],
        "created_at": row[4],
        "updated_at": row[5],
        "created_by": row[6],
        "context": _loads(row[7]),
        "constraints": _loads(row[8]),
        "result": _loads(row[9]),
        "error": row[10],
        "metadata": _loads(row[11]),
    }


def list_missions(status=None, limit=50):
    """List missions (newest first) with status counts.

    Returns {"ok": True, "missions": [...], "total": n, "counts": {...}}.
    An invalid status filter returns {"ok": False, "error": "..."}.
    """
    try:
        limit = max(0, min(int(limit), 200))
    except (TypeError, ValueError):
        limit = 50

    c = _conn()
    try:
        if status:
            status = status.strip().upper()
            if status not in VALID_STATUSES:
                return {"ok": False, "error": f"invalid status '{status}'."}
            rows = c.execute(
                "SELECT mission_id FROM missions WHERE status=? "
                "ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT mission_id FROM missions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    finally:
        c.close()

    missions = [get_mission(r[0]) for r in rows]
    counts = {s: 0 for s in VALID_STATUSES}
    for m in missions:
        counts[m["status"]] += 1
    return {
        "ok": True,
        "missions": missions,
        "total": len(missions),
        "counts": counts,
    }


# ---------------------------------------------------------------------------
# State transitions (validated)
# ---------------------------------------------------------------------------


def transition(mission_id, target_status, result=None, error=None):
    """Apply a validated state transition.

    Returns {"ok": True, "mission": {...}} or {"ok": False, "error": "..."}.
    Invalid transitions are rejected safely — the mission row is untouched.
    """
    mission = get_mission(mission_id)
    if mission is None:
        return {"ok": False, "error": f"mission '{mission_id}' not found."}

    target_status = (target_status or "").strip().upper()
    allowed, reason = can_transition(mission["status"], target_status)
    if not allowed:
        return {"ok": False, "error": reason}

    # Semantic requirements per target state.
    if target_status == STATUS_FAILED:
        error = (error or "").strip()
        if not error:
            return {"ok": False, "error":
                    "failing a mission requires a non-empty 'error'."}
        if len(error) > MAX_ERROR:
            error = error[:MAX_ERROR]
    if target_status == STATUS_COMPLETED:
        err = _json_error(result)
        if err:
            return {"ok": False, "error": f"result {err}."}

    now = time.time()
    c = _conn()
    try:
        if target_status == STATUS_COMPLETED:
            c.execute(
                "UPDATE missions SET status=?, result=?, error=NULL, "
                "updated_at=? WHERE mission_id=?",
                (target_status, _dumps(result), now, mission_id),
            )
        elif target_status == STATUS_FAILED:
            c.execute(
                "UPDATE missions SET status=?, error=?, result=NULL, "
                "updated_at=? WHERE mission_id=?",
                (target_status, error, now, mission_id),
            )
        else:
            c.execute(
                "UPDATE missions SET status=?, updated_at=? WHERE mission_id=?",
                (target_status, now, mission_id),
            )
        c.commit()
    finally:
        c.close()
    _audit("mission_transition", mission_id, True,
           f"{mission['status']} -> {target_status}")
    return {"ok": True, "mission": get_mission(mission_id)}


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------


def plan_mission(mission_id):
    return transition(mission_id, STATUS_PLANNED)


def ready_mission(mission_id):
    return transition(mission_id, STATUS_READY)


def start_mission(mission_id):
    return transition(mission_id, STATUS_RUNNING)


def pause_mission(mission_id):
    return transition(mission_id, STATUS_PAUSED)


def resume_mission(mission_id):
    return transition(mission_id, STATUS_RUNNING)


def cancel_mission(mission_id):
    return transition(mission_id, STATUS_CANCELLED)


def complete_mission(mission_id, result=None):
    return transition(mission_id, STATUS_COMPLETED, result=result)


def fail_mission(mission_id, error):
    return transition(mission_id, STATUS_FAILED, error=error)


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------


def _self_test():
    print("HEER Mission Engine self-test (Phase 3.1)\n" + "-" * 46)
    results = []

    # 1. Create with fields
    r = create_mission(
        "Launch the AI Agency website",
        priority="high",
        created_by="Pankaj",
        context={"client": "AI Agency"},
        constraints=["budget capped at 20k"],
        metadata={"track": "growth"},
    )
    ok = (r["ok"] and r["mission"]["status"] == STATUS_CREATED
          and r["mission"]["priority"] == "high"
          and r["mission"]["created_by"] == "Pankaj"
          and r["mission"]["context"] == {"client": "AI Agency"}
          and r["mission"]["constraints"] == ["budget capped at 20k"]
          and r["mission"]["metadata"] == {"track": "growth"}
          and r["mission"]["updated_at"] >= r["mission"]["created_at"])
    results.append(("create mission (CREATED + fields persisted)", ok))
    mid = r["mission"]["mission_id"]

    # 2. Input validation
    ok = (create_mission("")["ok"] is False
          and create_mission("x", priority="urgent")["ok"] is False
          and create_mission("x", metadata=object())["ok"] is False)
    results.append(("input validation (objective/priority/json)", ok))

    # 3. Happy-path lifecycle CREATED -> PLANNED -> READY -> RUNNING -> COMPLETED
    ok = plan_mission(mid)["ok"]
    ok = ok and ready_mission(mid)["ok"]
    r = start_mission(mid)
    ok = ok and r["ok"] and r["mission"]["status"] == STATUS_RUNNING
    r = complete_mission(mid, result={"url": "https://example.com"})
    ok = (ok and r["ok"] and r["mission"]["status"] == STATUS_COMPLETED
          and r["mission"]["result"] == {"url": "https://example.com"}
          and r["mission"]["updated_at"] >= r["mission"]["created_at"])
    results.append(("happy path CREATED->...->COMPLETED with result", ok))

    # 4. Failed completion from terminal state is rejected
    r = cancel_mission(mid)
    ok = (r["ok"] is False and "terminal" in r["error"].lower())
    results.append(("terminal states reject further transitions", ok))

    # 5. Pause / resume
    r = create_mission("Pause/resume demo")
    mid2 = r["mission"]["mission_id"]
    ok = plan_mission(mid2)["ok"]
    r = ready_mission(mid2)
    ok = ok and r["ok"]
    r = start_mission(mid2)
    ok = ok and r["ok"] and r["mission"]["status"] == STATUS_RUNNING
    r = pause_mission(mid2)
    ok = ok and r["ok"] and r["mission"]["status"] == STATUS_PAUSED
    r = resume_mission(mid2)
    ok = ok and r["ok"] and r["mission"]["status"] == STATUS_RUNNING
    r = complete_mission(mid2, result={"ok": True})
    ok = ok and r["ok"] and r["mission"]["status"] == STATUS_COMPLETED
    results.append(("pause/resume RUNNING<->PAUSED", ok))

    # 6. Fail requires error; then FAILED persists it
    r = create_mission("Fail demo")
    mid3 = r["mission"]["mission_id"]
    plan_mission(mid3)
    ready_mission(mid3)
    start_mission(mid3)
    r = fail_mission(mid3, "")
    ok = r["ok"] is False
    r = fail_mission(mid3, "missing API credentials")
    ok = (ok and r["ok"] and r["mission"]["status"] == STATUS_FAILED
          and r["mission"]["error"] == "missing API credentials")
    results.append(("fail path RUNNING->FAILED validates error", ok))

    # 7. Cancel allowed from every active state
    cancel_ok = True
    for state in (STATUS_CREATED, STATUS_PLANNED, STATUS_READY,
                  STATUS_RUNNING, STATUS_PAUSED):
        r = create_mission(f"Cancel from {state}")
        m = r["mission"]["mission_id"]
        if state in (STATUS_PLANNED, STATUS_READY, STATUS_RUNNING, STATUS_PAUSED):
            plan_mission(m)
        if state in (STATUS_READY, STATUS_RUNNING, STATUS_PAUSED):
            ready_mission(m)
        if state in (STATUS_RUNNING, STATUS_PAUSED):
            start_mission(m)
        if state == STATUS_PAUSED:
            pause_mission(m)
        r = cancel_mission(m)
        if not (r["ok"] and r["mission"]["status"] == STATUS_CANCELLED):
            cancel_ok = False
            break
    results.append(("cancel allowed from CREATED/PLANNED/READY/RUNNING/PAUSED",
                    cancel_ok))

    # 8. Invalid transitions rejected
    r = create_mission("Invalid transition demo")
    mid4 = r["mission"]["mission_id"]
    ok = (transition(mid4, STATUS_RUNNING)["ok"] is False      # CREATED->RUNNING
          and transition(mid4, STATUS_COMPLETED)["ok"] is False
          and transition(mid4, "BOGUS")["ok"] is False
          and transition("mis_does_not_exist", STATUS_PLANNED)["ok"] is False)
    results.append(("invalid transitions rejected safely", ok))

    # 9. List with status filter + sql-injection-safe objective
    r = create_mission("x'; DROP TABLE missions; --")
    ok = r["ok"]
    lst = list_missions(status=STATUS_COMPLETED)
    ok = ok and lst["ok"] and lst["total"] >= 1 and all(
        m["status"] == STATUS_COMPLETED for m in lst["missions"])
    ok = ok and get_mission(r["mission"]["mission_id"]) is not None
    results.append(("list filter + sql-injection-safe objective", ok))

    for label, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    print("-" * 46)
    print(f"Result: {'ALL PASS' if all(ok for _, ok in results) else 'FAILURES'}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())