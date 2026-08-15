#!/usr/bin/env python3
"""Phase 3.2 FINAL ACCEPTANCE verification script (Route A).

Runs against the live server (default http://localhost:8000) and prints
PASS/FAIL for each acceptance criterion of the Phase 3.2 Task Graph / DAG
engine, plus legacy HEER endpoint regression checks.

Run:  python3 scripts/acceptance_phase32.py [base_url]
"""

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
MISSION = "mis_0d4839cde232"  # Route A Phase 3.2 acceptance mission (existing RUNNING)


def api(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def main():
    results = []

    # ---- C1: no dangling dependency edges in acceptance mission diamond DAG ----
    status, payload = api(f"/api/mission-engine/missions/{MISSION}/tasks")
    ok = status == 200 and payload.get("ok") is True and payload.get("total", 0) >= 4
    all_ids = {t["task_id"] for t in payload.get("tasks", [])}
    dangling = []
    for t in payload.get("tasks", []):
        for d in t.get("dependencies", []):
            if d not in all_ids:
                dangling.append((t["task_id"], d))
    ok = ok and not dangling
    edge_count = sum(len(t.get("dependencies", [])) for t in payload.get("tasks", []))
    results.append(
        ("C1: no dangling dependency edges "
         f"(mission {MISSION}, {payload.get('total', 0)} tasks, {edge_count} edges)",
         ok, f"dangling={dangling}")
    )

    # ---- C2: graph/validate returns valid DAG + deterministic topological order ----
    status, v = api(f"/api/mission-engine/missions/{MISSION}/graph/validate")
    order1 = v.get("order", [])
    status2, v2 = api(f"/api/mission-engine/missions/{MISSION}/graph/validate")
    ok = (status == 200 and v.get("valid") is True and not v.get("errors")
          and v.get("task_count") == 4 and v.get("edge_count") == 4
          and order1 == v2.get("order", []))  # deterministic
    results.append(
        ("C2: graph/validate valid DAG, deterministic topo order "
         f"({order1})", ok,
         f"validate={json.dumps(v)}")
    )

    # ---- C3: unknown / duplicate / self dependencies rejected ----
    status, r = api("/api/mission-engine/missions", "POST",
                    {"objective": "ACCEPTANCE invalid edge test",
                     "priority": "high", "created_by": "acceptance"})
    assert r["ok"], r
    mid2 = r["mission"]["mission_id"]

    status, bad = api(f"/api/mission-engine/missions/{mid2}/tasks", "POST",
                      {"name": "BadDep", "dependencies": ["tsk_nonexistent"]})
    ok1 = status == 400 and not bad.get("ok") and "unknown dependency" in bad.get("error", "")
    results.append(("C3a: unknown dependency rejected via POST /tasks "
                    f"(HTTP {status})", ok1, json.dumps(bad)))

    status, a = api(f"/api/mission-engine/missions/{mid2}/tasks", "POST", {"name": "A"})
    assert a["ok"], a
    tid_a = a["task"]["task_id"]
    status, bad = api(f"/api/mission-engine/missions/{mid2}/tasks", "POST",
                      {"name": "Dup", "dependencies": [tid_a, tid_a]})
    ok2 = status == 400 and not bad.get("ok") and "duplicate dependency" in bad.get("error", "")
    results.append(("C3b: duplicate dependency rejected via POST /tasks "
                    f"(HTTP {status})", ok2, json.dumps(bad)))

    # ---- C4: cycle rejected safely via engine add_dependency (graph unchanged) ----
    import sys as _sys
    _sys.path.insert(0, ".")
    from agent import mission_engine as _me  # noqa: E402
    from agent import task_graph as _tg  # noqa: E402

    status, b = api(f"/api/mission-engine/missions/{mid2}/tasks", "POST",
                    {"name": "B", "dependencies": [tid_a]})
    assert b["ok"], b
    tid_b = b["task"]["task_id"]
    status, c = api(f"/api/mission-engine/missions/{mid2}/tasks", "POST",
                    {"name": "C", "dependencies": [tid_a, tid_b]})
    assert c["ok"], c
    # Graph is now: A (root) -> B, A -> C, B -> C  (valid DAG, 3 tasks / 3 edges)
    status, vlegit = api(f"/api/mission-engine/missions/{mid2}/graph/validate")
    ok = status == 200 and vlegit.get("valid") is True and vlegit.get("task_count") == 3
    results.append(("C4a: legit multi-dep chain remains a valid DAG "
                    f"(order={vlegit.get('order')})", ok, json.dumps(vlegit)))

    # Attempt to add edge A -> B (would create cycle A->B and B->A) via engine.
    before = _tg.validate_graph(mid2)
    cycle = _tg.add_dependency(mid2, tid_a, tid_b)
    after = _tg.validate_graph(mid2)
    ok = (cycle["ok"] is False and "cycle" in cycle["error"].lower()
          and after["valid"] is True and after["order"] == before["order"])
    results.append(("C4b: cycle-creating add_dependency rejected, graph unchanged "
                    f"({cycle.get('error')})", ok,
                    f"before={before['order']} after={after['order']}"))

    # ---- C5: legacy HEER endpoints still respond 200 ----
    legacy = ["/api/status", "/api/system", "/api/briefing", "/api/agents",
              "/api/skills", "/api/learning", "/api/opportunities",
              "/api/activity", "/api/clients", "/api/projects", "/api/business",
              "/api/automations", "/api/network", "/api/registry",
              "/api/approvals", "/api/executions", "/api/missions",
              "/api/tools", "/api/graph", "/api/hubs", "/api/businesses"]
    missing = []
    for ep in legacy:
        try:
            st, _ = api(ep)
            if st != 200:
                missing.append(f"{ep}->{st}")
        except Exception as ex:
            missing.append(f"{ep}->{ex}")
    results.append((f"C5: all {len(legacy)} legacy GET endpoints respond 200",
                    not missing, f"missing={missing}"))

    # ---- C6: legacy /api/chat (handle pipeline) still responds ----
    try:
        status, r = api("/api/chat", "POST", {"message": "what can you do?"})
        ok = status == 200 and isinstance(r, dict) and ("response" in r or "reply" in r or "text" in r)
        extra = json.dumps(r)[:200]
    except Exception as ex:
        ok = False
        extra = str(ex)
    results.append(("C6: legacy /api/chat handle() pipeline still responds "
                    f"(HTTP {status if 'status' in dir() else '?'})", ok, extra))

    # ---- C7: task state machine + transitions via live API ----
    # Use a fresh mission so the check is repeatable (doesn't depend on prior
    # runs having already completed tasks in the acceptance mission).
    status, r = api("/api/mission-engine/missions", "POST",
                    {"objective": "ACCEPTANCE task lifecycle test",
                     "priority": "high", "created_by": "acceptance"})
    assert r["ok"], r
    mid3 = r["mission"]["mission_id"]
    status, ra = api(f"/api/mission-engine/missions/{mid3}/tasks", "POST", {"name": "A"})
    assert ra["ok"], ra
    tid3a = ra["task"]["task_id"]
    status, rb = api(f"/api/mission-engine/missions/{mid3}/tasks", "POST",
                     {"name": "B", "dependencies": [tid3a]})
    assert rb["ok"], rb
    # READY -> RUNNING
    status, rr = api(f"/api/mission-engine/missions/{mid3}/tasks/{tid3a}/transition",
                     "POST", {"status": "RUNNING"})
    ok = status == 200 and rr.get("ok") is True
    results.append(("C7a: task transition READY -> RUNNING (live POST)",
                    ok, json.dumps(rr)[:200]))
    # RUNNING -> COMPLETED with output
    status, rr = api(f"/api/mission-engine/missions/{mid3}/tasks/{tid3a}/transition",
                     "POST", {"status": "COMPLETED", "output": {"accepted": True}})
    ok = status == 200 and rr.get("ok") is True and rr.get("task", {}).get("output") == {"accepted": True}
    results.append(("C7b: task transition RUNNING -> COMPLETED with output",
                    ok, json.dumps(rr)[:300]))
    # Fan-out: completing A promotes dependency child B to READY
    status, ready = api(f"/api/mission-engine/missions/{mid3}/graph/ready")
    ready_names = {t["name"] for t in ready.get("ready", [])}
    ok = status == 200 and ready.get("total") == 1 and ready_names == {"B"}
    results.append(("C7c: fan-out — completing A promotes B to READY "
                    f"({sorted(ready_names)})", ok, json.dumps(ready)[:300]))
    # Invalid transition rejected: READY B -> COMPLETED (must go RUNNING first)
    tid3b = rb["task"]["task_id"]
    status, bad = api(f"/api/mission-engine/missions/{mid3}/tasks/{tid3b}/transition",
                      "POST", {"status": "COMPLETED"})
    ok = status == 409 and not bad.get("ok")
    results.append(("C7d: invalid task transition READY -> COMPLETED rejected "
                    f"(HTTP {status})", ok, json.dumps(bad)[:200]))

    # ---- C8: legacy mission (Phase 3.0 /api/missions) still intact ----
    status, mp = api("/api/missions")
    ok = status == 200 and isinstance(mp, dict)
    results.append(("C8: legacy /api/missions payload still responds", ok,
                    json.dumps(mp)[:200]))

    # ---- Summary ----
    print("=" * 72)
    print("HEER Phase 3.2 — Task Graph / DAG FINAL ACCEPTANCE")
    print(f"Base: {BASE}")
    print("=" * 72)
    ok_all = True
    for label, ok, extra in results:
        ok_all = ok_all and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        if not ok:
            print(f"       {extra}")
    print("=" * 72)
    print(f"OVERALL: {'ALL PASS' if ok_all else 'FAILURES'}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())