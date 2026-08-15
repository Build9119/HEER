#!/usr/bin/env python3
"""Tests for the Hermes Runtime Adapter seam (Phase 3.4.2) + EE integration.

Run from repo root:  python3 tests/hermes_adapter_test.py

Covers: build_request/map_result contract shapes, adapter invoke() with a
deterministic FakeTransport (success/failure/cancel/timeout/stall, lease
heartbeat, cancel propagation, crash recovery), install/uninstall runtime
seam (legacy tools.call_tool unchanged), real HermesRuntime integration
through the Phase 3.3 Execution Engine (fan-out, diamond ordering,
cooperative cancel, timeout+retry single-row CAS, stall + lease-sweep
recovery, retry re-dispatch).
"""
import json, os, sys, threading, time, unittest
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path: sys.path.insert(0, _BASE)
from agent import execution_engine as engine
from agent import mission_engine, task_graph, tools as tools_mod
from agent.runtime_contracts import (
    RuntimeCapabilities, RuntimeError, RuntimeErrorType, RuntimeHandle,
    RuntimeResult, RuntimeResultStatus, RuntimeTransportKind,
    RuntimeIsolation, new_handle_id,
)
from agent.hermes_adapter import RuntimeAdapter, build_request, map_result
from agent.hermes_runtime import HermesRuntime

_TERM = ("COMPLETED", "FAILED", "CANCELLED")
_LK, _TRACE, _CALLS, _ACTIVE, _PEAK = threading.Lock(), [], {}, [0], [0]
_GATE = threading.Event()
_GATE.set()
_SLOW = 0.3


def _reset():
    global _TRACE, _CALLS
    _GATE.set()
    with _LK:
        _TRACE, _CALLS = [], {}
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
            return {"ok": False, "error": f"{tag}: simulated failure"}
        if sim == "fail_once" and _CALLS[tag] == 1:
            return {"ok": False, "error": f"{tag}: first attempt failed"}
        if sim == "slow_once" and _CALLS[tag] == 1:
            time.sleep(_SLOW)
        elif sim == "gate":
            _GATE.wait()
        elif sim == "slow":
            time.sleep(_SLOW)
        else:
            time.sleep(delay)
        return {"ok": True, "result": {"tag": tag, "attempts": _CALLS[tag]}}
    finally:
        with _LK:
            _ACTIVE[0] -= 1
            _TRACE.append(("finish", tag, time.monotonic()))


_ORIG_CALL_TOOL = tools_mod.call_tool


def setUpModule():
    engine.configure(poll=0.05, backoff_base=0.05, backoff_cap=0.3, lease_ttl=1.0)
    tools_mod.call_tool = _fake_call_tool


def tearDownModule():
    engine.scheduler_stop()
    engine.uninstall_runtime()
    tools_mod.call_tool = _ORIG_CALL_TOOL


def mid(obj="Hermes adapter test"):
    r = mission_engine.create_mission(obj, priority="high", created_by="hermes_adapter_test")
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

# ---------------------------------------------------------------------------
# Deterministic transport double (Hermes-compatible public surface)
# ---------------------------------------------------------------------------

class FakeTransport:
    """Deterministic HermesRuntime-compatible transport for unit tests.

    lazy=True: submit() never creates a terminal result, so the adapter's
    poll loop keeps running until its hard-stop deadline (used to exercise
    cancel propagation, lease heartbeat, crash recovery, stall).
    """

    def __init__(self, *, lazy=False):
        self.lazy = lazy
        self._by_handle = {}
        self._results = {}
        self.submit_count = 0
        self.start_count = 0
        self.cancel_calls = []
        self.heartbeat_calls = []
        self.recover_calls = []
        self._caps = RuntimeCapabilities(
            transport=RuntimeTransportKind.INPROCESS,
            isolation=RuntimeIsolation.NONE,
            max_concurrency=8, supports_heartbeat=True, supports_hard_timeout=True)
        self._runtime_id = "fake-rt"

    def capabilities(self):
        return self._caps

    def submit(self, request):
        self.submit_count += 1
        j = request.job
        h = new_handle_id()
        self._by_handle[h] = j.execution_id
        if not self.lazy:
            a = dict(j.input or {})
            sim = a.get("sim") or "ok"
            status = RuntimeResultStatus.SUCCEEDED
            output, error = {"tag": a.get("tag") or j.task_id}, None
            if sim == "fail":
                status = RuntimeResultStatus.FAILED; output = None
                error = RuntimeError(error_type=RuntimeErrorType.UNKNOWN,
                                     message="simulated failure",
                                     correlation_id=j.correlation_id)
            elif sim == "cancel":
                status = RuntimeResultStatus.CANCELLED; output = None
            elif sim == "timeout":
                status = RuntimeResultStatus.TIMED_OUT; output = None
            self._results[j.execution_id] = RuntimeResult(
                execution_id=j.execution_id, job_id=j.job_id, status=status,
                output=output, error=error, correlation_id=j.correlation_id)
        return RuntimeHandle(handle_id=h, execution_id=j.execution_id,
                             runtime_id="fake-rt", worker_id=None,
                             submitted_at=time.time())

    def start(self, handle_id):
        self.start_count += 1
        return {"ok": True, "phase": "RUNNING"}

    def result(self, handle_id):
        eid = self._by_handle.get(handle_id)
        return self._results.get(eid) if eid is not None else None

    def cancel(self, handle_id):
        self.cancel_calls.append(handle_id)

    def heartbeat(self, handle_id):
        self.heartbeat_calls.append(handle_id)

    def recover(self):
        self.recover_calls.append(1)
        return {"ok": True, "checked": 0, "recovered": []}


def _adapter(ft, **kw):
    defaults = dict(hard_stop_grace=0.3, poll_interval=0.01,
                    stall_recover_interval=0.05, lease_heartbeat_interval=0.05)
    defaults.update(kw)
    return RuntimeAdapter(ft, **defaults)


# ---------------------------------------------------------------------------
# Unit: build_request
# ---------------------------------------------------------------------------

class TestBuildRequest(unittest.TestCase):

    def test_contract_shapes(self):
        rt = FakeTransport()
        req = build_request(runtime=rt, execution_id="exe_1", mission_id="mis_1",
                            task_id="t1", attempt_no=2, tool_name="fake_tool",
                            task_input={"tag": "x", "_business_id": "biz1"},
                            timeout_sec=12.5)
        self.assertEqual(req.job.job_id, "exe_1")
        self.assertEqual(req.job.execution_id, "exe_1")
        self.assertEqual(req.job.mission_id, "mis_1")
        self.assertEqual(req.job.task_id, "t1")
        self.assertEqual(req.job.attempt_no, 2)
        self.assertEqual(req.job.correlation_id, "exe_1")
        self.assertEqual(req.job.metadata["tool"], "fake_tool")
        self.assertEqual(req.idempotency_key, "exe_1")
        self.assertIs(req.capabilities_required, rt.capabilities())
        self.assertIs(req.job.capabilities, rt.capabilities())
        self.assertEqual(req.job.input["_business_id"], "biz1")

    def test_timeout_normalized(self):
        rt = FakeTransport()
        req = build_request(runtime=rt, execution_id="exe_2", mission_id="mis_2",
                            task_id="t2", attempt_no=1, tool_name="fake_tool",
                            task_input={}, timeout_sec=0.5)
        self.assertEqual(req.job.timeout_sec, 0.5)
        req0 = build_request(runtime=rt, execution_id="exe_3", mission_id="mis_3",
                             task_id="t3", attempt_no=1, tool_name="fake_tool",
                             task_input={}, timeout_sec=0)
        self.assertIsNone(req0.job.timeout_sec)
        reqN = build_request(runtime=rt, execution_id="exe_4", mission_id="mis_4",
                             task_id="t4", attempt_no=1, tool_name="fake_tool",
                             task_input={}, timeout_sec=None)
        self.assertIsNone(reqN.job.timeout_sec)


# ---------------------------------------------------------------------------
# Unit: map_result
# ---------------------------------------------------------------------------

class TestMapResult(unittest.TestCase):

    def _res(self, status, **kw):
        return RuntimeResult(execution_id="exe_1", job_id="exe_1", status=status, **kw)

    def test_succeeded(self):
        r = map_result(self._res(RuntimeResultStatus.SUCCEEDED,
                                 output={"tag": "a", "n": 1}))
        self.assertTrue(r["ok"])
        self.assertEqual(r["result"], {"tag": "a", "n": 1})
        self.assertEqual(r["runtime_status"], "SUCCEEDED")

    def test_failed(self):
        r = map_result(self._res(RuntimeResultStatus.FAILED, error=RuntimeError(
            error_type=RuntimeErrorType.RUNTIME_ERROR if hasattr(RuntimeErrorType, "RUNTIME_ERROR")
            else RuntimeErrorType.UNKNOWN, message="boom")))
        self.assertFalse(r["ok"])
        self.assertIn("boom", r["error"])
        self.assertEqual(r["runtime_status"], "FAILED")

    def test_cancelled(self):
        r = map_result(self._res(RuntimeResultStatus.CANCELLED))
        self.assertFalse(r["ok"])
        self.assertTrue(r["cancelled"])
        self.assertEqual(r["runtime_status"], "CANCELLED")

    def test_timed_out(self):
        r = map_result(self._res(RuntimeResultStatus.TIMED_OUT))
        self.assertFalse(r["ok"])
        self.assertTrue(r["timed_out"])
        self.assertEqual(r["runtime_status"], "TIMED_OUT")

    def test_none(self):
        r = map_result(None)
        self.assertFalse(r["ok"])

    def test_non_runtime_result(self):
        r = map_result({"ok": True})
        self.assertFalse(r["ok"])



# ---------------------------------------------------------------------------
# Unit: adapter.invoke() against FakeTransport
# ---------------------------------------------------------------------------

class TestAdapterInvoke(unittest.TestCase):

    def _invoke(self, ft=None, sim="ok", **kw):
        ft = ft or FakeTransport()
        ad = _adapter(ft)
        res = ad.invoke(execution_id="exe_5", mission_id="mis_5", task_id="t5",
                        attempt_no=1, tool_name="fake_tool",
                        task_input={"tag": "t5", "sim": sim}, **kw)
        return ft, res

    def test_succeeded(self):
        ft, res = self._invoke(sim="ok")
        self.assertTrue(res["ok"])
        self.assertEqual(res["result"], {"tag": "t5"})
        self.assertEqual(ft.submit_count, 1)
        self.assertEqual(ft.start_count, 1)
        with _LK:
            self.assertIn("t5", json.dumps(res))

    def test_failed(self):
        _, res = self._invoke(sim="fail")
        self.assertFalse(res["ok"])
        self.assertIn("simulated failure", res["error"])

    def test_cancelled_result(self):
        _, res = self._invoke(sim="cancel")
        self.assertFalse(res["ok"])
        self.assertTrue(res["cancelled"])

    def test_timed_out_result(self):
        _, res = self._invoke(sim="timeout")
        self.assertFalse(res["ok"])
        self.assertTrue(res["timed_out"])
        self.assertEqual(res["runtime_status"], "TIMED_OUT")

    def test_stalled_transport_returns_runtime_stalled(self):
        ft = FakeTransport(lazy=True)
        _, res = self._invoke(ft, sim="ok")
        self.assertFalse(res["ok"])
        self.assertTrue(res["runtime_stalled"])

    def test_cancel_check_propagates_to_transport(self):
        ft = FakeTransport(lazy=True)
        ad = _adapter(ft)
        res = ad.invoke(execution_id="exe_6", mission_id="mis_6", task_id="t6",
                        attempt_no=1, tool_name="fake_tool", task_input={},
                        cancel_check=lambda: True)
        self.assertTrue(res["runtime_stalled"])
        self.assertGreater(len(ft.cancel_calls), 0)
        self.assertEqual(len(ft.cancel_calls), 1)   # cooperative: idempotent single call

    def test_engine_heartbeat_throttled_during_poll(self):
        ft = FakeTransport(lazy=True)
        beats = []
        ad = _adapter(ft)
        res = ad.invoke(execution_id="exe_7", mission_id="mis_7", task_id="t7",
                        attempt_no=1, tool_name="fake_tool", task_input={},
                        engine_heartbeat=lambda: beats.append(1))
        self.assertTrue(res["runtime_stalled"])
        self.assertGreater(len(beats), 0)

    def test_recover_called_during_stall(self):
        ft = FakeTransport(lazy=True)
        _, res = self._invoke(ft, sim="ok")
        self.assertTrue(res["runtime_stalled"])
        self.assertGreater(len(ft.recover_calls), 0)

    def test_submit_rejection(self):
        class NoSubmit:
            def capabilities(self):
                return None
            def start(self, handle_id):
                return {"ok": True}
            def result(self, handle_id):
                return None
        ad = _adapter(NoSubmit())
        res = ad.invoke(execution_id="exe_8", mission_id="mis_8", task_id="t8",
                        attempt_no=1, tool_name="fake_tool", task_input={})
        self.assertFalse(res["ok"])
        self.assertIn("submit", res["error"])


# ---------------------------------------------------------------------------
# Unit: install_runtime seam
# ---------------------------------------------------------------------------

class TestRuntimeSeam(unittest.TestCase):

    def tearDown(self):
        engine.uninstall_runtime()

    def test_install_validates_surface(self):
        class NotARuntime:
            pass
        r = engine.install_runtime(NotARuntime())
        self.assertFalse(r["ok"])
        self.assertIn("submit", r["error"])

    def test_install_and_status(self):
        rt = FakeTransport()
        r = engine.install_runtime(rt)
        self.assertTrue(r["ok"] and r["installed"])
        st = engine.runtime_status()
        self.assertTrue(st["installed"])
        self.assertEqual(st["runtime_id"], "fake-rt")

    def test_uninstall_restores_legacy(self):
        rt = FakeTransport()
        engine.install_runtime(rt)
        self.assertTrue(engine.runtime_status()["installed"])
        engine.uninstall_runtime()
        st = engine.runtime_status()
        self.assertFalse(st["installed"])
        self.assertIsNone(st["runtime_id"])
        self.assertIsNone(engine._current_runtime())

    def test_install_none_restores_legacy(self):
        engine.install_runtime(FakeTransport())
        r = engine.install_runtime(None)
        self.assertTrue(r["ok"])
        self.assertFalse(r["installed"])
        self.assertIsNone(engine._current_runtime())


# ---------------------------------------------------------------------------
# Integration: real HermesRuntime through the Execution Engine
# ---------------------------------------------------------------------------

class TestHermesIntegration(unittest.TestCase):

    def setUp(self):
        _reset()
        self.rt = None

    def tearDown(self):
        _GATE.set()
        engine.uninstall_runtime()
        if self.rt is not None:
            try: self.rt.terminate()
            except Exception: pass

    def _install(self, rt=None, **kw):
        rt = rt or HermesRuntime(transport=RuntimeTransportKind.INPROCESS,
                                 isolation=RuntimeIsolation.NONE, max_concurrency=8)
        self.rt = rt
        # Heartbeat below the 1.0s lease TTL so the lease sweep never reclaims
        # a live worker during real-Hermes integration tests.
        defaults = dict(lease_heartbeat_interval=0.25, stall_recover_interval=0.25)
        defaults.update(kw)
        engine.install_runtime(rt, **defaults)
        return rt

    def test_mission_through_hermes_completes(self):
        rt = self._install()
        mi = mid()
        mk(mi, "a", tag="a", sim="ok", delay=0.03)
        engine.start_mission(mi)
        m = term(mi)
        self.assertEqual(m["status"], "COMPLETED")
        self.assertTrue(engine.runtime_status()["installed"])
        ev = rt.events()
        self.assertGreater(len(ev), 0)   # Hermes actually dispatched the tool

    def test_mission_with_runtime_uses_hermes(self):
        rt = self._install()
        mi = mid()
        mk(mi, "b", tag="b", sim="ok", delay=0.03)
        base_calls = len(rt.events())
        engine.start_mission(mi)
        self.assertEqual(term(mi)["status"], "COMPLETED")
        self.assertGreater(len(rt.events()), base_calls)
        exs = engine.list_executions(mission_id=mi)["executions"]
        self.assertTrue(any(x["status"] == "COMPLETED" for x in exs))

    def test_parallel_fanout_respects_concurrency(self):
        self._install()
        mi = mid()
        for i in range(4):
            mk(mi, f"p{i}", tag=f"p{i}", sim="slow")
        engine.start_mission(mi, max_concurrent=2)
        self.assertEqual(term(mi)["status"], "COMPLETED")
        self.assertLessEqual(_PEAK[0], 2)
        for i in range(4):
            with _LK:
                self.assertIn(f"p{i}", _CALLS)

    def test_diamond_dag_ordering(self):
        self._install()
        mi = mid()
        tA = mk(mi, "A", tag="A", sim="ok", delay=0.02)
        tB = mk(mi, "B", deps=[tA["task_id"]], tag="B", sim="ok", delay=0.02)
        tC = mk(mi, "C", deps=[tA["task_id"]], tag="C", sim="ok", delay=0.02)
        mk(mi, "D", deps=[tB["task_id"], tC["task_id"]], tag="D", sim="ok", delay=0.02)
        engine.start_mission(mi)
        self.assertEqual(term(mi)["status"], "COMPLETED")
        _, ae = win("A")
        bs, _ = win("B"); cs, _ = win("C")
        ds, _ = win("D")
        self.assertGreaterEqual(bs, ae)
        self.assertGreaterEqual(cs, ae)
        self.assertGreaterEqual(ds, max(bs, cs))

    def test_retry_fail_once_through_hermes(self):
        self._install()
        mi = mid()
        t = mk(mi, "r1", tag="r1", sim="fail_once", idem=True, retry={"max_attempts": 3})
        engine.start_mission(mi)
        self.assertEqual(term(mi)["status"], "COMPLETED")
        exs = engine.list_executions(task_id=t["task_id"])["executions"]
        self.assertGreaterEqual(len(exs), 2)          # attempt 1 + retry
        by_attempt = {x["attempt_no"]: x["status"] for x in exs}
        self.assertEqual(by_attempt.get(1), "FAILED")
        self.assertEqual(by_attempt.get(2), "COMPLETED")
        with _LK:
            self.assertEqual(_CALLS["r1"], 2)         # exactly 2 tool calls, no dupes

    def test_timeout_retry_single_row(self):
        self._install()
        mi = mid()
        t = mk(mi, "to", tag="to", sim="slow_once", idem=True,
               retry={"max_attempts": 2}, timeout=0.15)
        engine.start_mission(mi)
        self.assertEqual(term(mi)["status"], "COMPLETED")
        exs = engine.list_executions(task_id=t["task_id"])["executions"]
        by_attempt = {x["attempt_no"]: x["status"] for x in exs}
        self.assertEqual(len(exs), 2)                 # exactly ONE retry row
        self.assertEqual(by_attempt.get(1), "FAILED")
        self.assertEqual(by_attempt.get(2), "COMPLETED")

    def test_timeout_exhausts_to_failed(self):
        self._install()
        mi = mid()
        mk(mi, "to2", tag="to2", sim="slow", idem=True,
            retry={"max_attempts": 2}, timeout=0.15)
        engine.start_mission(mi)
        self.assertEqual(term(mi)["status"], "FAILED")
        tasks = task_graph.list_tasks(mi)["tasks"]
        self.assertEqual(tasks[0]["status"], task_graph.TASK_FAILED)

    def test_cancel_running_task_through_hermes(self):
        self._install()
        mi = mid()
        t = mk(mi, "c1", tag="c1", sim="gate")
        _GATE.clear()   # block the tool so we can cancel while RUNNING
        engine.start_mission(mi)
        wait_for(lambda: any(
            tt["status"] == task_graph.TASK_RUNNING
            for tt in task_graph.list_tasks(mi)["tasks"]), timeout=5)
        r = engine.cancel_task(mi, t["task_id"])
        self.assertTrue(r["ok"])
        self.assertEqual(r["mode"], "cooperative")
        _GATE.set()   # release the tool so Hermes can finalize CANCELLED
        wait_for(lambda: task_graph.get_task(mi, t["task_id"])["status"] == task_graph.TASK_CANCELLED,
                 timeout=5)
        self.assertEqual(task_graph.get_task(mi, t["task_id"])["status"], task_graph.TASK_CANCELLED)


class TestHermesRecovery(unittest.TestCase):

    def setUp(self):
        _reset()
        self.rt = None

    def tearDown(self):
        _GATE.set()
        engine.uninstall_runtime()
        if self.rt is not None:
            try: self.rt.terminate()
            except Exception: pass

    def test_runtime_stall_lease_sweep_recovers(self):
        self.rt = HermesRuntime(transport=RuntimeTransportKind.INPROCESS,
                                isolation=RuntimeIsolation.NONE, max_concurrency=8)
        engine.install_runtime(self.rt, hard_stop_grace=0.5,
                               stall_recover_interval=0.2,
                               lease_heartbeat_interval=0.2, poll_interval=0.05)
        mi = mid()
        t = mk(mi, "stall", tag="stall", sim="gate")   # blocks forever on the gate
        _GATE.clear()
        engine.start_mission(mi)
        # Worker enters adapter.invoke() poll → stalls past hard_stop_grace → returns
        # without touching EE state → lease (ttl=1.0) expires → sweep recovers.
        m = term(mi, timeout=15)
        self.assertEqual(m["status"], "FAILED")
        exs = engine.list_executions(task_id=t["task_id"])["executions"]
        self.assertEqual(len(exs), 1)
        self.assertIn(exs[0]["status"], ("FAILED", "LEASE_EXPIRED"))

    def test_worker_candidate_metadata_propagation(self):
        from agent.dispatch_contracts import WorkerCandidate
        from agent.worker_contracts import WorkerIdentity, WorkerLivenessState
        identity = WorkerIdentity(
            worker_id="test_worker",
            worker_instance_id="inst_1",
            worker_epoch=42
        )
        candidate = WorkerCandidate(
            identity=identity,
            state=WorkerLivenessState.LIVE,
            registered_at=time.time()
        )
        req = build_request(
            runtime=None,
            execution_id="exe_123",
            mission_id="mis_123",
            task_id="tsk_123",
            attempt_no=1,
            tool_name="fake_tool",
            task_input={},
            worker_candidate=candidate
        )
        self.assertEqual(req.job.metadata.get("worker_id"), "test_worker")
        self.assertEqual(req.job.metadata.get("worker_instance_id"), "inst_1")
        self.assertEqual(req.job.metadata.get("worker_epoch"), 42)


if __name__ == "__main__":
    unittest.main(verbosity=2)