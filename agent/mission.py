#!/usr/bin/env python3
"""mission.py — HEER Mission & Task-Graph Layer (Phase 3.1).

Missions decompose high-level goals into ordered task DAGs. The v1
executor runs tasks sequentially in topological order; the DAG shape is
stored so a parallel fan-out executor can be added later without changing
the data model.

SQLite tables (in .heer/, same state dir as approvals/audit):
  missions — id, name, goal, owner, status, created_at, started_at, finished_at
  tasks    — id, mission_id, agent_id, tool, args, depends_on (json),
             status, result (json), lat_ms, approval (json), created_at

Run:  python3 -m agent.mission [--self-test]
"""

import json
import os
import sqlite3
import time
import uuid

from . import data

MISSION_STATUSES = ("planned", "running", "completed", "failed", "blocked")
TASK_STATUSES = ("pending", "ready", "running", "completed", "failed",
                 "blocked", "pending_approval")


# ---------------------------------------------------------------------------
# SQLite state
# ---------------------------------------------------------------------------


def _state_dir():
    root = data.data_root() or os.path.abspath(".")
    d = os.path.join(os.path.abspath(os.path.join(root, "..")), ".heer")
    os.makedirs(d, exist_ok=True)
    return d


def _db_path():
    return os.path.join(_state_dir(), "missions.sqlite3")


def _conn():
    c = sqlite3.connect(_db_path())
    c.execute(
        """CREATE TABLE IF NOT EXISTS missions (
            id TEXT PRIMARY KEY,
            name TEXT,
            goal TEXT,
            owner TEXT,
            status TEXT DEFAULT 'planned',
            created_at REAL,
            started_at REAL,
            finished_at REAL
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            mission_id TEXT,
            agent_id TEXT,
            tool TEXT,
            args TEXT,
            depends_on TEXT,
            status TEXT DEFAULT 'pending',
            result TEXT,
            lat_ms INTEGER,
            approval TEXT,
            created_at REAL
        )"""
    )
    return c


def _loads(raw, fallback):
    try:
        return json.loads(raw or "")
    except (json.JSONDecodeError, TypeError):
        return fallback


# ---------------------------------------------------------------------------
# Mission CRUD
# ---------------------------------------------------------------------------


def create_mission(name, goal, owner="Pankaj"):
    """Create a new mission (status='planned'). Returns mission dict."""
    mid = "mis_" + str(uuid.uuid4())[:8]
    c = _conn()
    c.execute(
        "INSERT INTO missions (id, name, goal, owner, status, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (mid, name[:200], goal[:1000], owner, "planned", time.time()),
    )
    c.commit()
    c.close()
    return get_mission(mid)


def get_mission(mission_id):
    c = _conn()
    row = c.execute(
        "SELECT id, name, goal, owner, status, created_at, started_at, finished_at "
        "FROM missions WHERE id=?",
        (mission_id,),
    ).fetchone()
    c.close()
    if row is None:
        return None
    return {
        "id": row[0], "name": row[1], "goal": row[2], "owner": row[3],
        "status": row[4], "created_at": row[5],
        "started_at": row[6], "finished_at": row[7],
    }


def set_mission_status(mission_id, status):
    """Set mission status (timestamps auto-set on running/completed/…).

    Returns updated mission or None if mission/status invalid.
    """
    if status not in MISSION_STATUSES:
        return None
    ts = time.time()
    c = _conn()
    if status == "running":
        c.execute(
            "UPDATE missions SET status=?, started_at=COALESCE(started_at, ?) WHERE id=?",
            (status, ts, mission_id),
        )
    elif status in ("completed", "failed", "blocked"):
        c.execute(
            "UPDATE missions SET status=?, finished_at=COALESCE(finished_at, ?) WHERE id=?",
            (status, ts, mission_id),
        )
    else:
        c.execute("UPDATE missions SET status=? WHERE id=?", (status, mission_id))
    c.commit()
    c.close()
    return get_mission(mission_id)


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------


def add_task(mission_id, agent_id, tool, args=None, depends_on=None):
    """Add a task to a mission. Returns task dict.

    depends_on: list of task ids (strings) within the same mission.
    """
    args = args or {}
    if isinstance(depends_on, str):
        depends_on = [depends_on]
    depends_on = list(depends_on or [])
    tid = "tsk_" + str(uuid.uuid4())[:8]
    c = _conn()
    c.execute(
        "INSERT INTO tasks (id, mission_id, agent_id, tool, args, depends_on, "
        "status, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (tid, mission_id, agent_id[:50], tool[:50], json.dumps(args, default=str),
         json.dumps(depends_on), "pending", time.time()),
    )
    c.commit()
    c.close()
    return get_task(tid)


def get_task(task_id):
    c = _conn()
    row = c.execute(
        "SELECT id, mission_id, agent_id, tool, args, depends_on, status, "
        "result, lat_ms, approval, created_at FROM tasks WHERE id=?",
        (task_id,),
    ).fetchone()
    c.close()
    if row is None:
        return None
    return {
        "id": row[0], "mission_id": row[1], "agent_id": row[2], "tool": row[3],
        "args": _loads(row[4], {}), "depends_on": _loads(row[5], []),
        "status": row[6], "result": _loads(row[7], None),
        "lat_ms": row[8], "approval": _loads(row[9], {}), "created_at": row[10],
    }


def set_task_status(task_id, status, result=None, lat_ms=None, approval=None):
    """Update a task's status/result. First write wins for result/approval.

    Returns updated task or None if task/status invalid.
    """
    if status not in TASK_STATUSES:
        return None
    c = _conn()
    c.execute(
        "UPDATE tasks SET status=?, result=COALESCE(?, result), "
        "lat_ms=COALESCE(?, lat_ms), approval=COALESCE(?, approval) WHERE id=?",
        (status,
         json.dumps(result, default=str)[:5000] if result is not None else None,
         lat_ms,
         json.dumps(approval, default=str) if approval is not None else None,
         task_id),
    )
    c.commit()
    c.close()
    return get_task(task_id)


def mission_tasks(mission_id):
    """All tasks for a mission, insertion-ordered (stable execution order)."""
    c = _conn()
    rows = c.execute(
        "SELECT id FROM tasks WHERE mission_id=? ORDER BY created_at ASC, rowid ASC",
        (mission_id,),
    ).fetchall()
    c.close()
    return [get_task(r[0]) for r in rows]


# ---------------------------------------------------------------------------
# DAG resolution (topological sort, Kahn's algorithm with cycle detection)
# ---------------------------------------------------------------------------


def resolve(mission_id):
    """Resolve a mission's task DAG into an execution plan.

    Returns {"order": [...], "blocked": [...], "missing": [...]}:
      - order:    task ids in a valid topological execution order
      - blocked:  task ids stuck in cycles (cannot execute)
      - missing:  dependency ids referenced but not present as tasks
    """
    tasks = mission_tasks(mission_id)
    by_id = {t["id"]: t for t in tasks}
    deps = {}
    dependents = {}
    for t in tasks:
        dlist = [d for d in t.get("depends_on", []) if d and d != t["id"]]
        deps[t["id"]] = dlist
        for d in dlist:
            dependents.setdefault(d, set()).add(t["id"])

    missing = set()
    for tid, dlist in deps.items():
        for d in dlist:
            if d not in by_id:
                missing.add(d)

    # In-degree = number of *present* unfilled deps
    indeg = {tid: sum(1 for d in deps[tid] if d in by_id) for tid in by_id}
    queue = sorted(tid for tid, d in indeg.items() if d == 0)
    order = []
    while queue:
        tid = queue.pop(0)
        order.append(tid)
        for dep in dependents.get(tid, ()):
            indeg[dep] -= 1
            if indeg[dep] == 0:
                queue.append(dep)
                queue.sort()

    processed = set(order)
    blocked = sorted(tid for tid in by_id if tid not in processed)
    return {"order": order, "blocked": blocked, "missing": sorted(missing)}


def mark_ready_tasks(mission_id):
    """Move pending tasks whose deps are all completed to 'ready'.

    Returns the number of tasks newly marked ready.
    """
    tasks = mission_tasks(mission_id)
    completed = {t["id"] for t in tasks if t["status"] == "completed"}
    c = _conn()
    n = 0
    for t in tasks:
        if t["status"] == "pending" and all(d in completed for d in t.get("depends_on", [])):
            c.execute("UPDATE tasks SET status='ready' WHERE id=?", (t["id"],))
            n += 1
    c.commit()
    c.close()
    return n


# ---------------------------------------------------------------------------
# Mission building (templates + compact defs)
# ---------------------------------------------------------------------------


def build_mission(name, goal, task_defs, owner="Pankaj"):
    """Create a mission from a compact task list.

    task_defs: list of dicts {"agent_id", "tool", "args", "depends_on"}.
      depends_on entries may be prior task indices (ints) or task ids (strs).
    Returns the full mission payload (mission + tasks).
    """
    m = create_mission(name, goal, owner=owner)
    ids = {}
    for i, td in enumerate(task_defs):
        deps = td.get("depends_on") or []
        resolved = []
        for d in deps:
            if isinstance(d, int):
                child = ids.get(d)
                if child is None:
                    raise ValueError(f"task_def {i} references missing index {d}")
                resolved.append(child)
            else:
                resolved.append(d)
        t = add_task(m["id"], td["agent_id"], td["tool"],
                     td.get("args") or {}, resolved)
        ids[i] = t["id"]
    return mission_payload(m["id"])


# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------


def mission_payload(mission_id):
    """Full mission object with its tasks."""
    m = get_mission(mission_id)
    if m is None:
        return None
    m["tasks"] = mission_tasks(mission_id)
    return m


def missions_payload(limit=50):
    """List missions (newest first) with task status rollups."""
    c = _conn()
    rows = c.execute(
        "SELECT id FROM missions ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    c.close()
    missions = []
    for (mid,) in rows:
        m = get_mission(mid)
        tasks = mission_tasks(mid)
        statuses = {}
        for t in tasks:
            statuses[t["status"]] = statuses.get(t["status"], 0) + 1
        m["task_count"] = len(tasks)
        m["task_statuses"] = statuses
        missions.append(m)
    return {"missions": missions, "total": len(missions)}


def tasks_payload(limit=100):
    """Flat task feed (newest first)."""
    c = _conn()
    rows = c.execute(
        "SELECT id FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    c.close()
    return {"tasks": [get_task(r[0]) for r in rows]}


# ---------------------------------------------------------------------------
# Tool registry (Phase 3.8 wiring)
# ---------------------------------------------------------------------------


def _mission_create(name, args, business_id=None):
    goal = args.get("goal") or args.get("name") or ""
    task_defs = args.get("tasks") or []
    if not goal:
        return {"ok": False, "error": "mission_create needs 'goal'."}
    m = build_mission(name or goal[:60], goal, task_defs)
    return {"ok": True, "mission": m}


def _mission_list(name, args, business_id=None):
    return {"ok": True, **missions_payload(limit=int(args.get("limit", 50)))}


def _mission_get(name, args, business_id=None):
    mid = args.get("mission_id") or args.get("id") or ""
    m = mission_payload(mid)
    if m is None:
        return {"ok": False, "error": f"No mission '{mid}'."}
    return {"ok": True, "mission": m}


MISSION_TOOLS = {
    "create": {
        "desc": "Create a mission from a goal + task list (task DAG).",
        "params": {
            "name": "string (optional)",
            "goal": "string — mission objective",
            "tasks": "list of {agent_id, tool, args, depends_on}",
        },
        "fn": _mission_create,
    },
    "list": {
        "desc": "List missions with task status rollups.",
        "params": {"limit": "int (optional, default 50)"},
        "fn": _mission_list,
    },
    "get": {
        "desc": "Get a mission with its tasks.",
        "params": {"mission_id": "string"},
        "fn": _mission_get,
    },
}


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------

_CANNED_LINEAR = [
    {"agent_id": "developer", "tool": "code_read", "args": {"path": "README.md"}},
    {"agent_id": "developer", "tool": "code_read",
     "args": {"path": "docs/architecture.md"}, "depends_on": [0]},
    {"agent_id": "ceo", "tool": "briefing", "depends_on": [1]},
]

_CANNED_DIAMOND = [
    {"agent_id": "developer", "tool": "code_read", "args": {"path": "agent/core.py"}},
    {"agent_id": "github", "tool": "github_read",
     "args": {"repo": "demo/repo"}, "depends_on": [0]},
    {"agent_id": "automation", "tool": "n8n",
     "args": {"workflow": "ci_sync"}, "depends_on": [0]},
    {"agent_id": "ceo", "tool": "briefing", "depends_on": [1, 2]},
]


def _self_test():
    print("HEER Mission & Task-Graph self-test\n" + "-" * 40)
    results = []

    # Scenario 1: linear chain — strict sequential order, nothing blocked
    m1 = build_mission("Linear mission", "Read project docs and summarize.",
                       _CANNED_LINEAR)
    plan1 = resolve(m1["id"])
    tids1 = [t["id"] for t in m1["tasks"]]
    ok1 = (plan1["order"] == tids1 and not plan1["blocked"] and not plan1["missing"])
    results.append(("Linear mission resolves in dependency order", ok1))

    # Scenario 2: diamond DAG — fan-out then join (parallel-capable shape)
    m2 = build_mission("Diamond mission", "Fan-out demo with join.",
                       _CANNED_DIAMOND)
    plan2 = resolve(m2["id"])
    a, b, c_task, e = [t["id"] for t in m2["tasks"]]
    ok2 = (len(plan2["order"]) == 4 and plan2["order"][0] == a
           and plan2["order"][-1] == e and not plan2["blocked"]
           and set(plan2["order"][1:3]) == {b, c_task}
           and not plan2["missing"])
    results.append(("Diamond DAG resolves (fan-out then join)", ok2))

    # Scenario 3: cycle — all three tasks blocked, empty order
    m3 = create_mission("Cycle mission", "Should detect a cycle.")
    p = add_task(m3["id"], "developer", "code_write", {"path": "p.py"})
    q = add_task(m3["id"], "developer", "code_write",
                 {"path": "q.py"}, depends_on=[p["id"]])
    r = add_task(m3["id"], "developer", "code_write",
                 {"path": "r.py"}, depends_on=[q["id"]])
    # Introduce cycle: p depends on r
    c = _conn()
    c.execute("UPDATE tasks SET depends_on=? WHERE id=?",
              (json.dumps([r["id"]]), p["id"]))
    c.commit()
    c.close()
    plan3 = resolve(m3["id"])
    ok3 = (plan3["order"] == [] and len(plan3["blocked"]) == 3
           and not plan3["missing"])
    results.append(("Cycle detected (3 tasks blocked)", ok3))

    # Status transitions
    m4 = build_mission("Status mission", "Validate status flow.",
                       [{"agent_id": "developer", "tool": "code_read",
                         "args": {"path": "README.md"}}])
    t4 = m4["tasks"][0]
    set_mission_status(m4["id"], "running")
    set_task_status(t4["id"], "ready")
    set_task_status(t4["id"], "completed", result={"ok": True},
                    lat_ms=12, approval={"approved": True})
    m4b = get_mission(m4["id"])
    t4b = get_task(t4["id"])
    ok4 = (m4b["status"] == "running" and m4b["started_at"] is not None
           and t4b["status"] == "completed"
           and t4b["result"] == {"ok": True} and t4b["lat_ms"] == 12
           and t4b["approval"] == {"approved": True})
    set_mission_status(m4["id"], "completed")
    results.append(("Status transitions (mission+task) persist", ok4))

    for label, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    print("-" * 40)
    print(f"Result: {'ALL PASS' if all(ok for _, ok in results) else 'FAILURES'}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())