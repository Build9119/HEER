#!/usr/bin/env python3
"""task_graph.py — HEER Task Graph / DAG Engine (Phase 3.2).

Owns task graphs that belong to Phase 3.1 Mission Engine missions
(agent/mission_engine.py). A mission may contain multiple tasks with
dependencies; this engine validates the DAG, resolves readiness, and
tracks task states — WITHOUT executing tasks (that is a later phase).

Compatibility note:
  agent/mission.py is a pre-existing, self-contained legacy mission/DAG
  implementation (its own mission model, lowercase statuses) wired into
  the orchestrator mission path. It is left untouched. This module is the
  Phase 3.2 authoritative task graph layer for Phase 3.1 missions and
  reuses the same proven Kahn topological-sort algorithm pattern from
  mission.py. Two separate SQLite files keep the systems isolated.

Task model (SQLite in .heer/task_graph.sqlite3, same state dir pattern):
  task_id, mission_id, name, description, status, dependencies (json),
  priority, assigned_agent, input (json), output (json), error,
  metadata (json), created_at, updated_at

Task states (independent of Mission states):
  PENDING -> READY -> RUNNING -> COMPLETED
  RUNNING -> FAILED
  PENDING/READY/RUNNING/BLOCKED -> CANCELLED
  BLOCKED: dependencies failed/cancelled (unresolvable)

DAG validation (strict, deterministic):
  - referenced dependencies must exist in the same mission
  - no self-dependencies
  - no duplicate dependency references
  - no cycles (Kahn's algorithm)
  - mission ownership enforced (mission must exist in mission_engine)

Dependency resolution:
  - PENDING task whose dependencies are all COMPLETED -> READY
  - PENDING task with a FAILED/CANCELLED dependency -> BLOCKED

Audit (reuses audit.record — no duplicate audit system):
  - task creation             -> audit.record(intent="task_create")
  - task state transition     -> audit.record(intent="task_transition")
  - graph validation failure  -> audit.record(intent="graph_validate",
                                              success=False)
  - Mission state transitions are audited by mission_engine.transition()

Security:
  - parameterized SQL everywhere
  - strict input validation (lengths, enums, JSON-serializable)
  - mission/task ownership enforced on every operation
  - no code execution, no tool execution, no network, no filesystem
    access outside the existing .heer/ SQLite state
  - malformed graphs rejected safely (no partial writes)
  - no secrets logged

Run:  python3 -m agent.task_graph --self-test
"""

import json
import os
import sqlite3
import time
import uuid

from . import audit
from . import data
from . import mission_engine

# ---------------------------------------------------------------------------
# Task state machine (separate from Mission states)
# ---------------------------------------------------------------------------

TASK_PENDING = "PENDING"
TASK_READY = "READY"
TASK_RUNNING = "RUNNING"
TASK_BLOCKED = "BLOCKED"
TASK_COMPLETED = "COMPLETED"
TASK_FAILED = "FAILED"
TASK_CANCELLED = "CANCELLED"

ACTIVE_TASK_STATUSES = (TASK_PENDING, TASK_READY, TASK_RUNNING, TASK_BLOCKED)
TERMINAL_TASK_STATUSES = (TASK_COMPLETED, TASK_FAILED, TASK_CANCELLED)
VALID_TASK_STATUSES = ACTIVE_TASK_STATUSES + TERMINAL_TASK_STATUSES

VALID_PRIORITIES = ("low", "medium", "high", "critical")

TASK_TRANSITIONS = {
    TASK_PENDING: frozenset({TASK_READY, TASK_CANCELLED}),
    TASK_READY: frozenset({TASK_RUNNING, TASK_CANCELLED}),
    TASK_RUNNING: frozenset({TASK_COMPLETED, TASK_FAILED, TASK_CANCELLED}),
    TASK_BLOCKED: frozenset({TASK_CANCELLED}),
    TASK_COMPLETED: frozenset(),
    TASK_FAILED: frozenset(),
    TASK_CANCELLED: frozenset(),
}

MAX_NAME = 200
MAX_DESCRIPTION = 2000
MAX_ERROR = 2000
MAX_ASSIGNED_AGENT = 100


def task_state_machine():
    """Public read-only view of the task state machine."""
    return {
        state: sorted(targets)
        for state, targets in TASK_TRANSITIONS.items()
    }


def can_transition_task(current_status, target_status):
    """Validate a task transition.

    Returns (allowed: bool, reason: str). Never raises.
    """
    if current_status not in VALID_TASK_STATUSES:
        return False, f"unknown current task status '{current_status}'."
    if target_status not in VALID_TASK_STATUSES:
        return False, f"unknown target task status '{target_status}'."
    if current_status in TERMINAL_TASK_STATUSES:
        return False, (f"task is {current_status} (terminal); "
                       "no further transitions allowed.")
    if target_status not in TASK_TRANSITIONS[current_status]:
        return False, f"invalid task transition {current_status} -> {target_status}."
    return True, ""


# ---------------------------------------------------------------------------
# SQLite state
# ---------------------------------------------------------------------------


def _state_dir():
    root = data.data_root() or os.path.abspath(".")
    d = os.path.join(os.path.abspath(os.path.join(root, "..")), ".heer")
    os.makedirs(d, exist_ok=True)
    return d


def _db_path():
    return os.path.join(_state_dir(), "task_graph.sqlite3")


def _conn():
    c = sqlite3.connect(_db_path())
    c.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            mission_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'PENDING',
            dependencies TEXT,
            priority TEXT NOT NULL DEFAULT 'medium',
            assigned_agent TEXT NOT NULL DEFAULT '',
            input TEXT,
            output TEXT,
            error TEXT,
            metadata TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
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
# Audit hook (reuses audit.record — single audit system)
# ---------------------------------------------------------------------------


def _audit(intent, mission_id, task_id, success, detail=""):
    try:
        audit.record(
            request=f"{intent} mission={mission_id} task={task_id or ''} {detail[:200]}",
            intent=intent,
            agent_id="task_graph",
            tools=[intent],
            inputs={"mission_id": mission_id, "task_id": task_id,
                    "detail": detail[:500]},
            outputs={"success": success},
            approval={"blocked": False},
            success=success,
            lat_ms=0,
        )
    except Exception:  # never let audit failures break the engine
        pass


# ---------------------------------------------------------------------------
# Mission ownership
# ---------------------------------------------------------------------------


def _mission_exists(mission_id):
    """Phase 3.1 Mission Engine is authoritative for mission existence."""
    return mission_engine.get_mission(mission_id) is not None


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------


def create_task(mission_id, name, description="", priority="medium",
                assigned_agent="", dependencies=None, input=None, metadata=None):
    """Create a task belonging to an existing Phase 3.1 Mission.

    Dependencies must reference existing tasks in the SAME mission.
    Self-dependencies, duplicates, and unknown references are rejected.
    Initial status is resolved from the dependency completion state.

    Returns {"ok": True, "task": {...}} or {"ok": False, "error": "..."}.
    """
    if not mission_id or not _mission_exists(mission_id):
        return {"ok": False, "error": f"mission '{mission_id}' not found."}

    name = (name or "").strip()
    if not name:
        return {"ok": False, "error": "task name is required."}
    if len(name) > MAX_NAME:
        return {"ok": False, "error": f"name must be {MAX_NAME} characters or fewer."}

    description = (description or "").strip()[:MAX_DESCRIPTION]
    agent = (assigned_agent or "").strip()[:MAX_ASSIGNED_AGENT]

    pri = _clean_priority(priority)
    if pri is None:
        return {"ok": False, "error":
                "priority must be one of: low, medium, high, critical."}

    if dependencies is None:
        deps = []
    elif isinstance(dependencies, (list, tuple)):
        deps = [(d or "").strip() for d in dependencies]
    else:
        return {"ok": False, "error": "dependencies must be a list of task ids."}

    if len(set(deps)) != len(deps):
        return {"ok": False, "error": "duplicate dependency references are not allowed."}
    for d in deps:
        if not d:
            return {"ok": False, "error": "dependency ids must be non-empty strings."}

    for label, value in (("input", input), ("metadata", metadata)):
        err = _json_error(value)
        if err:
            return {"ok": False, "error": f"{label} {err}."}

    # Validate dependencies against existing tasks in this mission.
    existing = list_tasks(mission_id)["tasks"]
    existing_ids = {t["task_id"] for t in existing}
    for d in deps:
        if d not in existing_ids:
            return {"ok": False, "error": f"unknown dependency '{d}' "
                    "(dependency must exist in the same mission)."}

    now = time.time()
    tid = "tsk_" + uuid.uuid4().hex[:12]
    c = _conn()
    try:
        c.execute(
            "INSERT INTO tasks (task_id, mission_id, name, description, status, "
            "dependencies, priority, assigned_agent, input, output, error, "
            "metadata, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (tid, mission_id, name, description, TASK_PENDING,
             _dumps(deps), pri, agent, _dumps(input), None, None,
             _dumps(metadata), now, now),
        )
        c.commit()
    finally:
        c.close()

    # Initial status from dependency completion state.
    changed = _refresh_readiness(mission_id)
    task = get_task(mission_id, tid)
    _audit("task_create", mission_id, tid, True,
           f"status={task['status']} deps={len(deps)}")
    return {"ok": True, "task": task, "readiness_changed": changed}


def get_task(mission_id, task_id):
    """Return a task dict, enforcing mission ownership.

    Returns None when the task doesn't exist or belongs to another mission.
    """
    if not mission_id or not task_id or not isinstance(mission_id, str) \
            or not isinstance(task_id, str):
        return None
    c = _conn()
    try:
        row = c.execute(
            "SELECT task_id, mission_id, name, description, status, dependencies, "
            "priority, assigned_agent, input, output, error, metadata, "
            "created_at, updated_at FROM tasks WHERE task_id=? AND mission_id=?",
            (task_id, mission_id),
        ).fetchone()
    finally:
        c.close()
    if row is None:
        return None
    return {
        "task_id": row[0],
        "mission_id": row[1],
        "name": row[2],
        "description": row[3],
        "status": row[4],
        "dependencies": _loads(row[5], []),
        "priority": row[6],
        "assigned_agent": row[7],
        "input": _loads(row[8]),
        "output": _loads(row[9]),
        "error": row[10],
        "metadata": _loads(row[11]),
        "created_at": row[12],
        "updated_at": row[13],
    }


def list_tasks(mission_id):
    """All tasks for a mission (insertion order). Enforces mission ownership.

    Returns {"ok": True, "mission_id": ..., "tasks": [...], "total": n}
    or {"ok": False, "error": "..."} when the mission doesn't exist.
    """
    if not mission_id or not _mission_exists(mission_id):
        return {"ok": False, "error": f"mission '{mission_id}' not found."}
    c = _conn()
    try:
        rows = c.execute(
            "SELECT task_id FROM tasks WHERE mission_id=? "
            "ORDER BY created_at ASC, rowid ASC",
            (mission_id,),
        ).fetchall()
    finally:
        c.close()
    tasks = [get_task(mission_id, r[0]) for r in rows if get_task(mission_id, r[0])]
    return {"ok": True, "mission_id": mission_id, "tasks": tasks, "total": len(tasks)}


def add_dependency(mission_id, task_id, dependency_id):
    """Add a dependency edge task -> dependency_id (task depends on dependency).

    Fully validated before commit: existence, ownership, self-dependency,
    duplicates, and cycle safety. The graph must remain a valid DAG.

    Returns {"ok": True, "task": {...}} or {"ok": False, "error": "..."}.
    """
    task = get_task(mission_id, task_id)
    if task is None:
        return {"ok": False, "error": f"task '{task_id}' not found in mission "
                f"'{mission_id}'."}
    dep = get_task(mission_id, dependency_id)
    if dep is None:
        return {"ok": False, "error": f"dependency task '{dependency_id}' not "
                "found in this mission."}
    if dependency_id == task_id:
        return {"ok": False, "error": "a task cannot depend on itself."}
    if dependency_id in task["dependencies"]:
        return {"ok": False, "error": "duplicate dependency reference."}

    # Simulate the edge and validate the whole graph in memory (cycle safety).
    # Validating against live rows avoids SQLite cross-connection isolation.
    simulated_task = dict(task)
    simulated_task["dependencies"] = list(task["dependencies"]) + [dependency_id]
    all_tasks = list_tasks(mission_id)["tasks"]
    for i, t in enumerate(all_tasks):
        if t["task_id"] == task_id:
            all_tasks[i] = simulated_task
            break
    validation = _validate_tasks(all_tasks)
    if not validation["valid"]:
        return {"ok": False, "error":
                "adding dependency would create an invalid graph: "
                + "; ".join(validation["errors"])}

    c = _conn()
    try:
        c.execute(
            "UPDATE tasks SET dependencies=?, updated_at=? "
            "WHERE task_id=? AND mission_id=?",
            (_dumps(simulated_task), time.time(), task_id, mission_id),
        )
        c.commit()
    finally:
        c.close()

    _refresh_readiness(mission_id)
    updated = get_task(mission_id, task_id)
    _audit("task_dependency_add", mission_id, task_id, True,
           f"dep={dependency_id}")
    return {"ok": True, "task": updated}


# ---------------------------------------------------------------------------
# DAG validation (deterministic Kahn's topological sort + cycle detection)
# ---------------------------------------------------------------------------


def validate_graph(mission_id, audit_failure=False):
    """Validate a mission's task graph.

    Returns {"ok": True, "valid": bool, "errors": [...], "order": [...],
             "blocked": [...], "task_count": n, "edge_count": n}.

    Rejections (self-dependencies, unknown deps, duplicate refs, cycles)
    are returned as errors. Deterministic: sorted inputs, sorted output.

    When audit_failure=True and the graph is invalid, an
    intent="graph_validate" audit record is appended.
    """
    if not mission_id or not _mission_exists(mission_id):
        return {"ok": False, "valid": False,
                "errors": [f"mission '{mission_id}' not found."],
                "order": [], "blocked": [], "task_count": 0, "edge_count": 0}

    result = list_tasks(mission_id)
    tasks = result["tasks"]
    payload = _validate_tasks(tasks)
    payload["ok"] = True
    if audit_failure and not payload["valid"]:
        _audit("graph_validate", mission_id, "", False,
               "; ".join(payload["errors"])[:500])
    return payload


def _validate_tasks(tasks):
    """Pure in-memory DAG validation over task dicts (no DB access).

    Shared by validate_graph() and add_dependency() so simulated edges are
    validated against the exact graph they would create — without SQLite
    cross-connection visibility issues.
    """
    by_id = {t["task_id"]: t for t in tasks}
    errors = []

    # Duplicate task ids (cannot normally occur due to PK, but enforced).
    seen = set()
    for t in tasks:
        if t["task_id"] in seen:
            errors.append(f"duplicate task id '{t['task_id']}'.")
        seen.add(t["task_id"])

    # Edge validation.
    edge_count = 0
    for t in tasks:
        deps = t["dependencies"] or []
        if not isinstance(deps, list):
            errors.append(f"task '{t['task_id']}' has malformed dependencies.")
            continue
        if len(set(deps)) != len(deps):
            errors.append(f"task '{t['task_id']}' has duplicate dependency references.")
        for d in deps:
            if d == t["task_id"]:
                errors.append(f"task '{t['task_id']}' cannot depend on itself.")
            elif d not in by_id:
                errors.append(f"task '{t['task_id']}' references unknown dependency '{d}'.")
            else:
                edge_count += 1

    # Kahn's topological sort (deterministic: sorted queue).
    indeg = {
        tid: sum(1 for d in t["dependencies"] if d in by_id)
        for tid, t in by_id.items()
    }
    dependents = {}
    for tid, t in by_id.items():
        for d in t["dependencies"]:
            if d in by_id:
                dependents.setdefault(d, []).append(tid)

    queue = sorted(tid for tid, deg in indeg.items() if deg == 0)
    order = []
    while queue:
        tid = queue.pop(0)
        order.append(tid)
        for child in sorted(dependents.get(tid, [])):
            indeg[child] -= 1
            if indeg[child] == 0:
                queue.append(child)
                queue.sort()

    if len(order) != len(by_id):
        errors.append("cycle detected in task graph.")

    blocked = sorted(tid for tid in by_id if tid not in order)
    valid = not errors
    return {
        "valid": valid,
        "errors": errors,
        "order": order,
        "blocked": blocked,
        "task_count": len(by_id),
        "edge_count": edge_count,
    }


# ---------------------------------------------------------------------------
# Dependency resolution (READY / BLOCKED)
# ---------------------------------------------------------------------------


def _refresh_readiness(mission_id):
    """Recompute PENDING tasks based on dependency completion state.

    - PENDING task with all dependencies COMPLETED -> READY
    - PENDING task with a FAILED/CANCELLED dependency -> BLOCKED

    Returns the number of tasks whose status changed.
    """
    result = list_tasks(mission_id)
    if not result["ok"]:
        return 0
    tasks = result["tasks"]
    completed = {t["task_id"] for t in tasks if t["status"] == TASK_COMPLETED}
    dead = {t["task_id"] for t in tasks
            if t["status"] in (TASK_FAILED, TASK_CANCELLED)}

    changed = 0
    c = _conn()
    try:
        for t in tasks:
            if t["status"] != TASK_PENDING:
                continue
            deps = t["dependencies"] or []
            if deps and any(d in dead for d in deps):
                target = TASK_BLOCKED
            elif all(d in completed for d in deps):
                target = TASK_READY
            else:
                continue
            c.execute(
                "UPDATE tasks SET status=?, updated_at=? WHERE task_id=? AND mission_id=?",
                (target, time.time(), t["task_id"], mission_id),
            )
            changed += 1
        c.commit()
    finally:
        c.close()
    for t in tasks:
        if t["status"] == TASK_PENDING and _task_status(t["task_id"]) in (
                TASK_READY, TASK_BLOCKED):
            _audit("task_transition", mission_id, t["task_id"], True,
                   f"auto {TASK_PENDING} -> {_task_status(t['task_id'])}")
    return changed


def _task_status(task_id):
    c = _conn()
    try:
        row = c.execute("SELECT status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    finally:
        c.close()
    return row[0] if row else None


def ready_tasks(mission_id):
    """Tasks currently READY (run in deterministic insertion order)."""
    _refresh_readiness(mission_id)
    result = list_tasks(mission_id)
    if not result["ok"]:
        return {"ok": False, "error": result["error"], "ready": [], "total": 0}
    ready = [t for t in result["tasks"] if t["status"] == TASK_READY]
    return {"ok": True, "ready": ready, "total": len(ready)}


def blocked_tasks(mission_id):
    """Tasks currently BLOCKED (dependencies failed/cancelled)."""
    _refresh_readiness(mission_id)
    result = list_tasks(mission_id)
    if not result["ok"]:
        return {"ok": False, "error": result["error"], "blocked": [], "total": 0}
    blocked = [t for t in result["tasks"] if t["status"] == TASK_BLOCKED]
    return {"ok": True, "blocked": blocked, "total": len(blocked)}


# ---------------------------------------------------------------------------
# State transitions (validated)
# ---------------------------------------------------------------------------


def transition_task(mission_id, task_id, target_status, output=None, error=None):
    """Apply a validated task state transition.

    - FAILED requires a non-empty error.
    - COMPLETED validates output is JSON-serializable.
    - After a COMPLETED/FAILED/CANCELLED transition, pending tasks are
      re-resolved (READY / BLOCKED).

    Returns {"ok": True, "task": {...}, "ready_tasks": [...]}
    or {"ok": False, "error": "..."}. Invalid transitions are rejected
    safely — the task row is untouched.
    """
    task = get_task(mission_id, task_id)
    if task is None:
        return {"ok": False, "error": f"task '{task_id}' not found in mission "
                f"'{mission_id}'."}

    target = (target_status or "").strip().upper()
    allowed, reason = can_transition_task(task["status"], target)
    if not allowed:
        return {"ok": False, "error": reason}

    if target == TASK_FAILED:
        error = (error or "").strip()
        if not error:
            return {"ok": False, "error":
                    "failing a task requires a non-empty 'error'."}
        if len(error) > MAX_ERROR:
            error = error[:MAX_ERROR]
    if target == TASK_COMPLETED:
        err = _json_error(output)
        if err:
            return {"ok": False, "error": f"output {err}."}

    now = time.time()
    c = _conn()
    try:
        if target == TASK_COMPLETED:
            c.execute(
                "UPDATE tasks SET status=?, output=?, error=NULL, updated_at=? "
                "WHERE task_id=? AND mission_id=?",
                (target, _dumps(output), now, task_id, mission_id),
            )
        elif target == TASK_FAILED:
            c.execute(
                "UPDATE tasks SET status=?, error=?, output=NULL, updated_at=? "
                "WHERE task_id=? AND mission_id=?",
                (target, error, now, task_id, mission_id),
            )
        else:
            c.execute(
                "UPDATE tasks SET status=?, updated_at=? "
                "WHERE task_id=? AND mission_id=?",
                (target, now, task_id, mission_id),
            )
        c.commit()
    finally:
        c.close()

    _audit("task_transition", mission_id, task_id, True,
           f"{task['status']} -> {target}")

    changed = 0
    if target in (TASK_COMPLETED, TASK_FAILED, TASK_CANCELLED):
        changed = _refresh_readiness(mission_id)

    ready = ready_tasks(mission_id)
    return {
        "ok": True,
        "task": get_task(mission_id, task_id),
        "readiness_changed": changed,
        "ready_tasks": ready["ready"],
    }


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------


def _fresh_mission(objective="Task Graph self-test mission"):
    r = mission_engine.create_mission(objective, priority="high",
                                      created_by="task_graph")
    if not r["ok"]:
        raise RuntimeError(r["error"])
    return r["mission"]["mission_id"]


def _self_test():
    print("HEER Task Graph / DAG self-test (Phase 3.2)\n" + "-" * 50)
    results = []

    # 1. Create mission + diamond DAG -> valid, deterministic order
    mid = _fresh_mission("Diamond DAG")
    a = create_task(mid, "Research", priority="high")
    b = create_task(mid, "Prospect Discovery", dependencies=[a["task"]["task_id"]])
    c = create_task(mid, "Market Analysis", dependencies=[a["task"]["task_id"]])
    e = create_task(mid, "Qualification",
                    dependencies=[b["task"]["task_id"], c["task"]["task_id"]])
    ok = (a["ok"] and b["ok"] and c["ok"] and e["ok"]
          and a["task"]["status"] == "READY"  # no deps -> ready
          and b["task"]["status"] == "PENDING")
    v = validate_graph(mid)
    ok = ok and v["valid"] and v["task_count"] == 4 and v["edge_count"] == 4
    ok = ok and v["order"][0] == a["task"]["task_id"]
    ok = ok and v["order"][-1] == e["task"]["task_id"]
    ok = ok and set(v["order"][1:3]) == {b["task"]["task_id"], c["task"]["task_id"]}
    results.append(("valid diamond DAG (fan-out then join, deterministic order)", ok))

    # 2. READY resolution: completing 'Research' promotes both children
    r = ready_tasks(mid)
    ok = r["ok"] and r["total"] == 1 and r["ready"][0]["task_id"] == a["task"]["task_id"]
    results.append(("ready_tasks lists only the dependency-free task", ok))

    # 3. Self-dependency rejected
    bad = create_task(mid, "Bad", dependencies=[a["task"]["task_id"], a["task"]["task_id"]])
    ok = bad["ok"] is False and "duplicate dependency" in bad["error"]
    results.append(("duplicate dependency reference rejected", ok))

    # 4. Unknown dependency rejected
    bad = create_task(mid, "Bad2", dependencies=["tsk_nonexistent"])
    ok = bad["ok"] is False and "unknown dependency" in bad["error"]
    results.append(("unknown dependency rejected", ok))

    # 5. Self-dependency via add_dependency rejected
    bad = add_dependency(mid, b["task"]["task_id"], b["task"]["task_id"])
    ok = bad["ok"] is False and "itself" in bad["error"]
    results.append(("self-dependency rejected", ok))

    # 6. Cycle detected + rejected safely (DAG remains valid)
    d = create_task(mid, "Report", dependencies=[e["task"]["task_id"]])
    before = validate_graph(mid)
    cycle = add_dependency(mid, a["task"]["task_id"], d["task"]["task_id"])  # a<-d<-...<-a
    after = validate_graph(mid)
    ok = (cycle["ok"] is False and "cycle" in cycle["error"].lower()
          and after["valid"] and after["order"] == before["order"])
    results.append(("cycle rejected safely (graph unchanged after rejection)", ok))

    # 7. Dependency resolution: complete a -> b,c READY; complete b,c -> e READY
    transition_task(mid, a["task"]["task_id"], "RUNNING")
    transition_task(mid, a["task"]["task_id"], "COMPLETED", output={"n": 10})
    rb = ready_tasks(mid)
    ok = rb["ok"] and rb["total"] == 2
    results.append(("READY resolution: PENDING -> READY when deps complete", ok))
    transition_task(mid, b["task"]["task_id"], "RUNNING")
    transition_task(mid, b["task"]["task_id"], "COMPLETED", output={"ok": True})
    transition_task(mid, c["task"]["task_id"], "RUNNING")
    transition_task(mid, c["task"]["task_id"], "COMPLETED", output={"ok": True})
    re_ = ready_tasks(mid)
    ok = re_["ok"] and re_["total"] == 1 and re_["ready"][0]["task_id"] == e["task"]["task_id"]
    results.append(("join: fan-in task becomes READY only when ALL deps complete",
                    ok))

    # 8. BLOCKED resolution: failed dep blocks downstream
    mid2 = _fresh_mission("Blocked DAG")
    x = create_task(mid2, "Research X")
    y = create_task(mid2, "Prospect Y", dependencies=[x["task"]["task_id"]])
    transition_task(mid2, x["task"]["task_id"], "RUNNING")
    f = transition_task(mid2, x["task"]["task_id"], "FAILED", error="no data")
    ok = f["ok"] and f["task"]["status"] == "FAILED"
    blk = blocked_tasks(mid2)
    ok = ok and blk["ok"] and blk["total"] == 1 \
        and blk["blocked"][0]["task_id"] == y["task"]["task_id"]
    y_after = get_task(mid2, y["task"]["task_id"])
    ok = ok and y_after["status"] == "BLOCKED"
    results.append(("BLOCKED resolution on failed dependency", ok))

    # 9. Invalid + terminal task transitions rejected
    t = e["task"]  # currently READY (or runnable)
    bad = transition_task(mid, t["task_id"], "COMPLETED")  # READY->COMPLETED invalid
    ok = bad["ok"] is False
    bad = transition_task(mid, t["task_id"], "BOGUS")
    ok = ok and bad["ok"] is False
    r = transition_task(mid, t["task_id"], "RUNNING")
    ok = ok and r["ok"]
    r = transition_task(mid, t["task_id"], "COMPLETED", output={"report": "done"})
    ok = ok and r["ok"] and r["task"]["output"] == {"report": "done"}
    bad = transition_task(mid, t["task_id"], "CANCELLED")  # terminal -> reject
    ok = ok and bad["ok"] is False and "terminal" in bad["error"]
    results.append(("task state machine + terminal states enforced", ok))

    # 10. Mission ownership enforced
    ghost = create_task("mis_missing", "Ghost")
    ok = ghost["ok"] is False and "not found" in ghost["error"]
    ok = ok and list_tasks("mis_missing")["ok"] is False
    ok = ok and get_task("mis_missing", t["task_id"]) is None
    ok = ok and transition_task("mis_missing", t["task_id"], "READY")["ok"] is False
    results.append(("mission ownership enforced (unknown mission rejected)", ok))

    # 11. SQL-injection-safe
    inj = create_task(mid, "x'; DROP TABLE tasks; --")
    ok = inj["ok"] and get_task(mid, inj["task"]["task_id"])["name"] \
        == "x'; DROP TABLE tasks; --"
    ok = ok and get_task(mid, inj["task"]["task_id"]) is not None
    v2 = validate_graph(mid)
    ok = ok and v2["valid"]
    results.append(("sql-injection-safe task names + graph intact", ok))

    for label, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    print("-" * 50)
    print(f"Result: {'ALL PASS' if all(ok for _, ok in results) else 'FAILURES'}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())