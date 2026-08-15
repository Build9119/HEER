#!/usr/bin/env python3
"""Unit tests for the HEER Parallel Execution Engine (Phase 3.3).
Run from repo root:  python3 tests/execution_engine_test.py
"""
import json, os, sys, threading, time, unittest
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path: sys.path.insert(0, _BASE)
from agent import execution_engine as engine
from agent import mission_engine, task_graph, tools as tools_mod

_TERM = ("COMPLETED", "FAILED", "CANCELLED")
_LK, _TRACE, _CALLS, _ACTIVE, _PEAK, _FAILS = threading.Lock(), [], {}, [0], [0], {}
_GATE = threading.Event()
_GATE.set()
_SLOW = 0.3


def _reset():
    global _TRACE, _CALLS, _FAILS, _ACTIVE, _PEAK
    _GATE.set()   # re-open the gate by default
    with _LK:
        _TRACE, _CALLS, _FAILS = [], {}, {}
        _ACTIVE, _PEAK = [0], [0]


def _fake_call_tool(name, args=None, business_id=None):
    a = args or {}
    tag = a.get("tag") or name; sim = a.get("sim") or "ok"
    delay = a.get("delay") or 0.05
    with _LK:
        _CALLS[tag] = _CALLS.get(tag, 0) + 1
        _ACTIVE[0] += 1; _PEAK[0] = max(_PEAK[0], _ACTIVE[0])
        _TRACE.append(("start", tag, time.monotonic()))
    try:
        if sim == "fail":
            with _LK: _FAILS[tag] = _FAILS.get(tag, 0) + 1
            return {"ok": False, "error": f"{tag}: simulated failure"}
        if sim == "fail_once" and _CALLS[tag] == 1:
            with _LK: _FAILS[tag] = _FAILS.get(tag, 0) + 1
            return {"ok": False, "error": f"{tag}: first attempts"}
        if sim == "gate":
            _GATE.wait()   # deterministic block until the test releases it
        elif sim == "slow": time.sleep(_SLOW)
        else: time.sleep(delay)
        return {"ok": True, "result": {"tag": tag, "attempts": _CALLS[tag]}}
    finally:
        with _LK:
            _ACTIVE[0] -= 1
            _TRACE.append(("finish", tag, time.monotonic()))


def setUpModule():
    engine.configure(poll=0.05, backoff_base=0.05, backoff_cap=0.3)
    tools_mod.call_tool = _fake_call_tool


def tearDownModule():
    engine.scheduler_stop()
    tools_mod.call_tool = None


def mid(obj="Execution Engine test"):
    r = mission_engine.create_mission(obj, priority="high", created_by="execution_engine_test")
    assert r["ok"], r.get("error")
    return r["mission"]["mission_id"]


def mk(mi, name, deps=None, tag=None, sim="ok", idem=False, retry=None, timeout=None, delay=None):
    meta: dict = {"tool": "fake_tool"}
    if idem: meta["idempotent"] = True
    if retry is not None: meta["retry"] = retry
    if timeout is not None: meta["timeout_sec"] = timeout
    inp = {"tag": tag or name, "sim": sim}
    if delay is not None: inp["delay"] = delay
    r = task_graph.create_task(mi, name, description="", priority="high",
                               dependencies=deps or [], input=inp, metadata=meta)
    assert r["ok"], r.get("error")
    return r["task"]


def wait_for(pred, timeout=15.0, interval=0.05):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = pred()
        if v: return v
        time.sleep(interval)
    return None


def term(mi, timeout=15.0):
    assert wait_for(lambda: mission_engine.get_mission(mi)["status"] in _TERM, timeout=timeout), \
        f"mission {mi} never terminal"
    return mission_engine.get_mission(mi)


def win(tag):
    s = [ts for k, t, ts in _TRACE if k == "start" and t == tag]
    e = [ts for k, t, ts in _TRACE if k == "finish" and t == tag]
    assert s and e, f"no trace for {tag}"
    return min(s), max(e)

class LifecycleTests(unittest.TestCase):
    def setUp(self): _reset()

    def test_linear_dependency_ordering(self):
        mi = mid("linear")
        a = mk(mi, "A", tag="lA", delay=0.05)
        b = mk(mi, "B", deps=[a["task_id"]], tag="lB", delay=0.05)
        c = mk(mi, "C", deps=[b["task_id"]], tag="lC", delay=0.05)
        self.assertEqual(a["status"], task_graph.TASK_READY)
        self.assertEqual(b["status"], task_graph.TASK_PENDING)
        r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        sa, ea = win("lA"); sb, eb = win("lB"); sc, _ = win("lC")
        self.assertGreaterEqual(sb, ea - 0.001)
        self.assertGreaterEqual(sc, eb - 0.001)
        for t in (a, b, c):
            self.assertEqual(task_graph.get_task(mi, t["task_id"])["status"], task_graph.TASK_COMPLETED)
        self.assertEqual(mission_engine.get_mission(mi)["status"], mission_engine.STATUS_COMPLETED)

    def test_parallel_fan_out_and_join(self):
        mi = mid("diamond")
        a = mk(mi, "A", tag="dA", delay=0.05)
        b = mk(mi, "B", deps=[a["task_id"]], tag="dB", delay=0.12)
        c = mk(mi, "C", deps=[a["task_id"]], tag="dC", delay=0.12)
        d = mk(mi, "D", deps=[b["task_id"], c["task_id"]], tag="dD", delay=0.05)
        r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        _, ea = win("dA"); sb, eb = win("dB"); sc, ec = win("dC"); sd, _ = win("dD")
        self.assertLess(sb, ec - 0.005)          # B/C overlap
        self.assertLess(sc, eb - 0.005)
        self.assertGreaterEqual(sd, max(eb, ec) - 0.001)   # D joins both
        for t in (a, b, c, d):
            self.assertEqual(len(engine.list_executions(task_id=t["task_id"])["executions"]), 1)

    def test_duplicate_execution_prevention_double_start(self):
        mi = mid("dup")
        _GATE.clear()   # block all workers until we've done the double start
        for i in range(4):
            mk(mi, f"T{i}", tag=f"ds{i}", sim="gate")
        r1 = engine.start_mission(mi); self.assertTrue(r1["ok"], r1.get("error"))
        # While workers are gated the mission is still RUNNING; a second
        # start_mission must be accepted but must NOT duplicate anything.
        r2 = engine.start_mission(mi); self.assertTrue(r2["ok"], r2.get("error"))
        self.assertEqual(mission_engine.get_mission(mi)["status"], mission_engine.STATUS_RUNNING)
        _GATE.set()
        term(mi)
        for t in task_graph.list_tasks(mi)["tasks"]:
            exs = engine.list_executions(task_id=t["task_id"])["executions"]
            self.assertEqual(len(exs), 1, f"task {t['task_id']} executed >1x")
            self.assertEqual(exs[0]["status"], engine.COMPLETED)

    def test_duplicate_claim_rejected(self):
        engine.configure(max_concurrent=0)
        try:
            mi = mid("dupclaim"); t = mk(mi, "T", tag="dc1")
            e1 = engine._claim(t["task_id"], mi); self.assertIsNotNone(e1)
            self.assertIsNone(engine._claim(t["task_id"], mi))
            self.assertEqual(len(engine.list_executions(task_id=t["task_id"])["executions"]), 1)
            engine._mark_abandoned(e1, "cleanup")
            task_graph.transition_task(mi, t["task_id"], task_graph.TASK_CANCELLED, error="cleanup")
            task_graph._refresh_readiness(mi)
        finally:
            engine.configure(max_concurrent=4)


class RetryTests(unittest.TestCase):
    def setUp(self): _reset()

    def test_retry_success_second_attempt(self):
        mi = mid("retry ok")
        t = mk(mi, "T", tag="rt", sim="fail_once", idem=True, retry={"max_attempts": 2})
        r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        self.assertEqual(task_graph.get_task(mi, t["task_id"])["status"], task_graph.TASK_COMPLETED)
        exs = engine.list_executions(task_id=t["task_id"])["executions"]
        self.assertEqual(len(exs), 2)
        self.assertEqual({e["attempt_no"] for e in exs}, {1, 2})
        self.assertEqual(len({e["execution_id"] for e in exs}), 2)
        self.assertEqual({e["status"] for e in exs}, {engine.FAILED, engine.COMPLETED})

    def test_retry_exhaustion_fails_and_blocks(self):
        mi = mid("retry exhausted")
        x = mk(mi, "X", tag="rx", sim="fail", idem=True, retry={"max_attempts": 2})
        y = mk(mi, "Y", deps=[x["task_id"]], tag="ry")
        r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
        m = term(mi)
        self.assertEqual(task_graph.get_task(mi, x["task_id"])["status"], task_graph.TASK_FAILED)
        self.assertEqual(task_graph.get_task(mi, y["task_id"])["status"], task_graph.TASK_BLOCKED)
        self.assertEqual(m["status"], mission_engine.STATUS_FAILED)

    def test_non_idempotent_never_retried(self):
        mi = mid("no retry")
        t = mk(mi, "T", tag="nr", sim="fail", idem=False, retry={"max_attempts": 5})
        r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        exs = engine.list_executions(task_id=t["task_id"])["executions"]
        self.assertEqual(len(exs), 1)
        self.assertEqual(exs[0]["status"], engine.FAILED)
        self.assertEqual(_CALLS["nr"], 1)


class CancelTests(unittest.TestCase):
    def setUp(self): _reset()

    def test_pre_run_cancel(self):
        mi = mid("pre cancel")
        _GATE.clear()   # block A so B stays PENDING deterministically
        a = mk(mi, "A", tag="cpA", sim="gate")
        b = mk(mi, "B", deps=[a["task_id"]], tag="cpB")
        r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
        assert wait_for(lambda: task_graph.get_task(mi, a["task_id"])["status"] == task_graph.TASK_RUNNING)
        r = engine.cancel_task(mi, b["task_id"]); self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["mode"], "pre_run")
        _GATE.set()
        term(mi)
        self.assertEqual(task_graph.get_task(mi, b["task_id"])["status"], task_graph.TASK_CANCELLED)

    def test_cooperative_cancel_running(self):
        mi = mid("coop cancel")
        _GATE.clear()
        t = mk(mi, "T", tag="cc", sim="gate")
        r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
        assert wait_for(lambda: task_graph.get_task(mi, t["task_id"])["status"] == task_graph.TASK_RUNNING)
        r = engine.cancel_task(mi, t["task_id"]); self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["mode"], "cooperative")
        self.assertIsNotNone(r["execution_id"])
        _GATE.set()   # worker returns; post-tool cancel check fires
        term(mi)
        self.assertEqual(task_graph.get_task(mi, t["task_id"])["status"], task_graph.TASK_CANCELLED)
        self.assertEqual(mission_engine.get_mission(mi)["status"], mission_engine.STATUS_CANCELLED)

    def test_stop_mission(self):
        mi = mid("stop")
        _GATE.clear()
        mk(mi, "A", tag="smA", sim="gate")
        mk(mi, "B", tag="smB", delay=0.02)
        r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
        assert wait_for(lambda: any(t["status"] == task_graph.TASK_RUNNING
                                    for t in task_graph.list_tasks(mi)["tasks"]))
        r = engine.stop_mission(mi); self.assertTrue(r["ok"], r.get("error"))
        _GATE.set()
        term(mi)
        self.assertEqual(mission_engine.get_mission(mi)["status"], mission_engine.STATUS_CANCELLED)


class TimeoutTests(unittest.TestCase):
    def test_task_timeout(self):
        _reset()
        mi = mid("task timeout")
        t = mk(mi, "T", tag="tt", sim="slow", timeout=0.2)
        r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
        m = term(mi)
        self.assertEqual(task_graph.get_task(mi, t["task_id"])["status"], task_graph.TASK_FAILED)
        self.assertEqual(task_graph.get_task(mi, t["task_id"])["error"], "task timeout")
        exs = engine.list_executions(task_id=t["task_id"])["executions"]
        self.assertEqual(exs[0]["status"], engine.FAILED)
        self.assertTrue(engine.list_events(mission_id=mi, event_type="TIMEOUT")["events"])
        self.assertEqual(m["status"], mission_engine.STATUS_FAILED)

    def test_mission_timeout(self):
        _reset()
        _GATE.clear()   # keep the task blocked so the sweep can time it out
        engine.configure(mission_timeout=0.2)
        try:
            mi = mid("mission timeout")
            mk(mi, "T", tag="mto", sim="gate")
            r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
            assert wait_for(lambda: any(t["status"] == task_graph.TASK_RUNNING
                                        for t in task_graph.list_tasks(mi)["tasks"]))
            m = term(mi)
            self.assertEqual(m["status"], mission_engine.STATUS_FAILED)
            self.assertEqual(m["error"], "mission timeout")
        finally:
            _GATE.set()
            engine.configure(mission_timeout=0)


class RecoveryTests(unittest.TestCase):
    def setUp(self): _reset()

    def _expire(self, eid):
        c = engine._conn()
        try:
            c.execute("UPDATE executions SET lease_expires_at=? WHERE execution_id=?", (time.time() - 1, eid))
            c.commit()
        finally:
            c.close()

    def test_worker_crash_recovery(self):
        engine.configure(max_concurrent=0)
        try:
            mi = mid("crash")
            for s in (mission_engine.STATUS_PLANNED, mission_engine.STATUS_READY, mission_engine.STATUS_RUNNING):
                r = mission_engine.transition(mi, s); self.assertTrue(r["ok"], r.get("error"))
            t = mk(mi, "X", tag="crash")
            ready = task_graph.ready_tasks(mi)
            eid = engine._claim(ready["ready"][0]["task_id"], mi); self.assertIsNotNone(eid)
            self._expire(eid)
            engine.recover()
            ex = engine.list_executions(execution_id=eid)["executions"][0]
            self.assertEqual(ex["status"], engine.LEASE_EXPIRED)
            self.assertEqual(task_graph.get_task(mi, t["task_id"])["status"], task_graph.TASK_FAILED)
            self.assertIn("execution lost", task_graph.get_task(mi, t["task_id"])["error"])
        finally:
            engine.configure(max_concurrent=4)

    def test_restart_redispatch(self):
        mi = mid("restart")
        for s in (mission_engine.STATUS_PLANNED, mission_engine.STATUS_READY, mission_engine.STATUS_RUNNING):
            r = mission_engine.transition(mi, s); self.assertTrue(r["ok"], r.get("error"))
        engine.configure(max_concurrent=0)
        try:
            a = mk(mi, "A", tag="rsA", delay=0.02)
            b = mk(mi, "B", tag="rsB", delay=0.02)
            ready = task_graph.ready_tasks(mi)
            eidA = engine._claim(ready["ready"][0]["task_id"], mi)
            self._expire(eidA)
        finally:
            engine.configure(max_concurrent=4)
        engine.scheduler_start()
        term(mi)
        self.assertEqual(task_graph.get_task(mi, a["task_id"])["status"], task_graph.TASK_FAILED)
        self.assertEqual(task_graph.get_task(mi, b["task_id"])["status"], task_graph.TASK_COMPLETED)


class ConcurrencyTests(unittest.TestCase):
    def setUp(self): _reset()

    def test_global_cap(self):
        engine.configure(max_concurrent=2)
        try:
            mi = mid("global cap")
            for i in range(4): mk(mi, f"T{i}", tag=f"gc{i}", sim="slow")
            r = engine.start_mission(mi); self.assertTrue(r["ok"], r.get("error"))
            term(mi)
            self.assertLessEqual(_PEAK[0], 2)
            self.assertGreaterEqual(_PEAK[0], 1)
        finally:
            engine.configure(max_concurrent=4)

    def test_per_mission_cap(self):
        engine.configure(max_concurrent=4, per_mission=1)
        try:
            mi1, mi2 = mid("per1"), mid("per2")
            for i in range(2):
                mk(mi1, f"T{i}", tag=f"p1_{i}", sim="slow")
                mk(mi2, f"T{i}", tag=f"p2_{i}", sim="slow")
            r = engine.start_mission(mi1); self.assertTrue(r["ok"], r.get("error"))
            r = engine.start_mission(mi2); self.assertTrue(r["ok"], r.get("error"))
            term(mi1); term(mi2)
            self.assertLessEqual(_PEAK[0], 2)
        finally:
            engine.configure(max_concurrent=4, per_mission=0)


class ApiTests(unittest.TestCase):
    def setUp(self):
        import agent.main as mm
        class F:
            def __init__(self): self.buf = b""
            def write(self, d): self.buf += d
        class H(mm.Handler):
            def __init__(self, method, path, body=None):
                self.command, self.path = method, path
                self.rfile = type("R", (), {"read": lambda s, n=-1: body or b""})()
                self.headers = type("H", (), {"get": lambda s, k, d=None: "application/json" if k == "Content-Type" else d})()
                self.wfile, self.server, self.request = F(), None, None
                self.client_address = ("127.0.0.1", 0)
            def send_response(self, code, message=None): self._st = code
            def send_header(self, *a, **k): pass
            def end_headers(self): pass
        self.H = H; self.mm = mm

    def req(self, method, path, body=None):
        h = self.H(method, path, None if body is None else json.dumps(body).encode())
        getattr(self.mm.Handler, f"do_{method}")(h)
        return getattr(h, "_st", 200), json.loads(h.wfile.buf.decode()) if h.wfile.buf else None

    def test_routes(self):
        st, p = self.req("GET", "/api/execution/scheduler"); self.assertEqual(st, 200); self.assertTrue(p["ok"])
        st, p = self.req("GET", "/api/execution/metrics"); self.assertEqual(st, 200); self.assertTrue(p["ok"])
        st, p = self.req("POST", "/api/execution/config", {"max_concurrent": 2, "poll": 0.05})
        self.assertEqual(st, 200); self.assertTrue(p["ok"])
        engine.configure(max_concurrent=4, poll=0.05)
        _reset()
        mi = mid("api start")
        mk(mi, "T", tag="apistart", delay=0.02)
        st, p = self.req("POST", f"/api/execution/missions/{mi}/start", {})
        self.assertEqual(st, 200); self.assertTrue(p["ok"])
        term(mi)
        st, p = self.req("GET", f"/api/execution/executions?mission_id={mi}")
        self.assertEqual(p["count"], 1)
        st, p = self.req("GET", f"/api/execution/events?mission_id={mi}")
        self.assertGreaterEqual(p["count"], 1)


class DispatchIntegrationTests(unittest.TestCase):
    """Phase 3.6.3 — Worker Dispatch Integration tests.

    Verifies the matcher seam inside _worker():
      - backward compat when no registry is installed
      - DISPATCH_SELECTED event when an eligible worker is found
      - NO_ELIGIBLE_WORKER failure when no worker matches
      - TENANT_REJECTED failure when workers exist but are tenant-scoped out
    """

    def setUp(self):
        _reset()
        # Import the contracts/registry machinery
        from agent.worker_contracts import WorkerIdentity, WorkerCapabilities
        from agent.worker_registry import WorkerRegistry
        from agent.runtime_contracts import RuntimeIsolation
        self.WorkerIdentity = WorkerIdentity
        self.WorkerCapabilities = WorkerCapabilities
        self.WorkerRegistry = WorkerRegistry
        self.RuntimeIsolation = RuntimeIsolation

    def tearDown(self):
        # Always uninstall the registry so other test classes are unaffected
        engine.install_registry(None)

    def _make_registry_with_worker(self, *, worker_id="w-dispatch-1",
                                   instance_id="inst-d1", epoch=1,
                                   tenant_scope=(), tool_classes=("fake_tool",),
                                   make_live=True):
        """Create a WorkerRegistry with one registered (optionally LIVE) worker."""
        caps = self.WorkerCapabilities(tool_classes=tool_classes)
        identity = self.WorkerIdentity(
            worker_id=worker_id,
            worker_instance_id=instance_id,
            worker_epoch=epoch,
            tenant_scope=tenant_scope,
            capabilities=caps,
        )
        reg = self.WorkerRegistry()
        r = reg.register(identity)
        assert r["ok"], r.get("error")
        if make_live:
            import time
            r = reg.heartbeat(
                worker_id=worker_id,
                worker_instance_id=instance_id,
                worker_epoch=epoch,
                heartbeat_seq=1,
                reported_at=time.time(),
            )
            assert r["ok"], r.get("error")
        return reg

    def _events_of_type(self, mission_id, event_type):
        """Return events of a given type for a mission."""
        return engine.list_events(
            mission_id=mission_id, event_type=event_type
        )["events"]

    # ---- backward compat: no registry installed ---------------------------

    def test_no_registry_backward_compat(self):
        """Without a registry installed, tasks complete normally (no dispatch)."""
        engine.install_registry(None)
        mi = mid("dispatch compat")
        mk(mi, "T", tag="compat1", delay=0.02)
        r = engine.start_mission(mi)
        self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        self.assertEqual(mission_engine.get_mission(mi)["status"],
                         mission_engine.STATUS_COMPLETED)
        # No DISPATCH_* events should exist
        sel = self._events_of_type(mi, "DISPATCH_SELECTED")
        noelig = self._events_of_type(mi, "DISPATCH_NO_ELIGIBLE")
        self.assertEqual(len(sel), 0)
        self.assertEqual(len(noelig), 0)

    # ---- DISPATCH_SELECTED ------------------------------------------------

    def test_dispatch_selected_eligible_worker(self):
        """Registry with an eligible LIVE worker → DISPATCH_SELECTED event,
        task completes normally."""
        reg = self._make_registry_with_worker(tool_classes=("fake_tool",))
        engine.install_registry(reg)
        mi = mid("dispatch selected")
        mk(mi, "T", tag="dsel1", delay=0.02)
        r = engine.start_mission(mi)
        self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        self.assertEqual(mission_engine.get_mission(mi)["status"],
                         mission_engine.STATUS_COMPLETED)
        # Verify DISPATCH_SELECTED event was logged
        sel = self._events_of_type(mi, "DISPATCH_SELECTED")
        self.assertEqual(len(sel), 1)
        payload = sel[0]["payload"]
        self.assertEqual(payload["worker_id"], "w-dispatch-1")
        self.assertEqual(payload["worker_instance_id"], "inst-d1")
        self.assertEqual(payload["worker_epoch"], 1)

    # ---- NO_ELIGIBLE_WORKER (empty registry) ------------------------------

    def test_dispatch_no_eligible_empty_registry(self):
        """Registry installed but empty → DISPATCH_NO_ELIGIBLE, task fails
        via _handle_failure with NO_ELIGIBLE_WORKER."""
        reg = self.WorkerRegistry()
        engine.install_registry(reg)
        mi = mid("dispatch no eligible")
        mk(mi, "T", tag="noelig1", delay=0.02)
        r = engine.start_mission(mi)
        self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        m = mission_engine.get_mission(mi)
        self.assertEqual(m["status"], mission_engine.STATUS_FAILED)
        # Verify DISPATCH_NO_ELIGIBLE event
        evts = self._events_of_type(mi, "DISPATCH_NO_ELIGIBLE")
        self.assertGreaterEqual(len(evts), 1)

    # ---- NO_ELIGIBLE_WORKER (worker exists but not LIVE) ------------------

    def test_dispatch_no_eligible_registered_only(self):
        """Worker registered but not LIVE → NO_ELIGIBLE (require_live=True
        default), task fails."""
        reg = self._make_registry_with_worker(
            tool_classes=("fake_tool",), make_live=False
        )
        engine.install_registry(reg)
        mi = mid("dispatch registered only")
        mk(mi, "T", tag="regonly1", delay=0.02)
        r = engine.start_mission(mi)
        self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        m = mission_engine.get_mission(mi)
        self.assertEqual(m["status"], mission_engine.STATUS_FAILED)
        evts = self._events_of_type(mi, "DISPATCH_NO_ELIGIBLE")
        self.assertGreaterEqual(len(evts), 1)

    # ---- NO_ELIGIBLE_WORKER (tool class mismatch) -------------------------

    def test_dispatch_no_eligible_tool_mismatch(self):
        """Worker LIVE but doesn't advertise the required tool class → NO_ELIGIBLE."""
        reg = self._make_registry_with_worker(
            tool_classes=("other_tool",)  # task needs "fake_tool"
        )
        engine.install_registry(reg)
        mi = mid("dispatch tool mismatch")
        mk(mi, "T", tag="toolmis1", delay=0.02)
        r = engine.start_mission(mi)
        self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        m = mission_engine.get_mission(mi)
        self.assertEqual(m["status"], mission_engine.STATUS_FAILED)
        evts = self._events_of_type(mi, "DISPATCH_NO_ELIGIBLE")
        self.assertGreaterEqual(len(evts), 1)

    # ---- TENANT_REJECTED --------------------------------------------------

    def test_dispatch_tenant_rejected(self):
        """Worker exists with tenant_scope=('tenant-A',) but task requests
        tenant-B → DISPATCH_TENANT_REJECTED (or NO_ELIGIBLE), task fails."""
        reg = self._make_registry_with_worker(
            tenant_scope=("tenant-A",),
            tool_classes=("fake_tool",),
        )
        engine.install_registry(reg)
        mi = mid("dispatch tenant reject")
        # Task input carries _tenant_id=tenant-B so the matcher scopes to tenant-B
        t = task_graph.create_task(mi, "T", description="", priority="high",
                                   dependencies=[],
                                   input={"tag": "tenrej1", "sim": "ok",
                                          "delay": 0.02,
                                          "_tenant_id": "tenant-B"},
                                   metadata={"tool": "fake_tool"})
        assert t["ok"], t.get("error")
        r = engine.start_mission(mi)
        self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        m = mission_engine.get_mission(mi)
        self.assertEqual(m["status"], mission_engine.STATUS_FAILED)
        # Either TENANT_REJECTED or NO_ELIGIBLE is acceptable
        rej = self._events_of_type(mi, "DISPATCH_TENANT_REJECTED")
        noelig = self._events_of_type(mi, "DISPATCH_NO_ELIGIBLE")
        self.assertGreaterEqual(len(rej) + len(noelig), 1)

    # ---- Multiple tasks with dispatch ------------------------------------

    def test_dispatch_multiple_tasks_all_selected(self):
        """Multiple independent tasks, all matched to the same eligible
        worker — each emits its own DISPATCH_SELECTED event."""
        reg = self._make_registry_with_worker(tool_classes=("fake_tool",))
        engine.install_registry(reg)
        mi = mid("dispatch multi")
        mk(mi, "A", tag="dmA", delay=0.02)
        mk(mi, "B", tag="dmB", delay=0.02)
        mk(mi, "C", tag="dmC", delay=0.02)
        r = engine.start_mission(mi)
        self.assertTrue(r["ok"], r.get("error"))
        term(mi)
        self.assertEqual(mission_engine.get_mission(mi)["status"],
                         mission_engine.STATUS_COMPLETED)
        sel = self._events_of_type(mi, "DISPATCH_SELECTED")
        self.assertEqual(len(sel), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)