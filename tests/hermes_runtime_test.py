#!/usr/bin/env python3
"""Unit tests for the Hermes Runtime Transport (Phase 3.4.2).

Run from repo root:  python3 -m unittest tests.hermes_runtime_test
No subprocess / shell / eval / network / containers. The only real-time waits
are short poll loops (<= ~3s) for timeout/cooperative-cancellation coverage.
The governed tool boundary (tools.call_tool) is the only side-effect surface.
"""
import json
import os
import sys
import time
import unittest

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from agent import tools
from agent.hermes_runtime import HermesRuntime
from agent.runtime_contracts import (
    RuntimeCapabilities, RuntimeCapability, RuntimeErrorType, RuntimeHandle,
    RuntimeIsolation, RuntimeJob, RuntimeRequest, RuntimeResult,
    RuntimeResultStatus, RuntimeTransportKind,
)

CAPS = RuntimeCapabilities(
    transport=RuntimeTransportKind.INPROCESS, isolation=RuntimeIsolation.NONE,
    max_concurrency=8, supports_heartbeat=True, supports_hard_timeout=True,
    features=frozenset({RuntimeCapability.CANCELLATION,
                        RuntimeCapability.HEARTBEAT, RuntimeCapability.TIMEOUT}))

REQ_CAPS = RuntimeCapabilities(
    transport=RuntimeTransportKind.INPROCESS, isolation=RuntimeIsolation.NONE,
    max_concurrency=1, features=frozenset({RuntimeCapability.CANCELLATION}))


def _make_request(exec_id="exe_test_1", tool="echo", attempt=1,
                  timeout_sec=None, input_data=None, metadata_extra=None,
                  mission="mission_x", task="task_x", corr="corr_x",
                  idempotency_key=None):
    meta = {"tool": tool}
    if metadata_extra:
        meta.update(metadata_extra)
    job = RuntimeJob(job_id=exec_id, execution_id=exec_id, mission_id=mission,
                     task_id=task, attempt_no=attempt,
                     input=input_data if input_data is not None else {"text": "hello"},
                     metadata=meta, timeout_sec=timeout_sec,
                     correlation_id=corr, capabilities=CAPS)
    return RuntimeRequest(job=job, requested_at=1.0, requested_by="test",
                          capabilities_required=REQ_CAPS,
                          idempotency_key=idempotency_key)


class _FakeDeadThread:
    """White-box worker-thread stand-in whose is_alive() is always False."""
    name = "fake-dead-thread"

    def is_alive(self):
        return False


def _boom_check(req):  # governance hook that raises (fail-closed path)
    raise RuntimeError("boom")


def _wait_until(fn, timeout=3.0, interval=0.02):
    end = time.time() + timeout
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(interval)
    raise AssertionError("condition not met within %.1fs" % timeout)


def _result(rt, handle):
    """Access a terminal RuntimeResult, asserting it is not None (typed)."""
    r = rt.result(handle.handle_id)
    if r is None:
        raise AssertionError("expected a terminal RuntimeResult")
    return r


class HermesRuntimeTest(unittest.TestCase):

    def setUp(self):
        self._runtimes = []
        self._orig_call_tool = tools.call_tool

    def tearDown(self):
        for rt in list(self._runtimes):
            try:
                rt.terminate()
            except Exception:
                pass
        self._runtimes.clear()
        tools.call_tool = self._orig_call_tool

    def _rt(self, **kw):
        rt = HermesRuntime(**kw)
        self._runtimes.append(rt)
        return rt

    # ------------------------------------------------------------------
    # 1. Capability reporting (capability only — NEVER authorization)
    # ------------------------------------------------------------------

    def test_01_capability_reporting(self):
        rt = self._rt()
        c = rt.capabilities()
        self.assertEqual(c.transport, RuntimeTransportKind.INPROCESS)
        self.assertEqual(c.isolation, RuntimeIsolation.NONE)
        self.assertEqual(c.max_concurrency, 8)
        self.assertTrue(c.supports_heartbeat)
        self.assertTrue(c.supports_hard_timeout)
        self.assertIn(RuntimeCapability.CANCELLATION, c.features)
        self.assertIn(RuntimeCapability.TIMEOUT, c.features)
        self.assertNotIn(RuntimeCapability.SANDBOXING, c.features)

    # ------------------------------------------------------------------
    # 2/3. Submission + RuntimeHandle creation
    # ------------------------------------------------------------------

    def test_02_submission_creates_handle(self):
        rt = self._rt()
        h = rt.submit(_make_request())
        self.assertIsInstance(h, RuntimeHandle)
        self.assertTrue(h.handle_id.startswith("hrm_"))
        self.assertEqual(h.execution_id, "exe_test_1")
        self.assertIsNotNone(h.runtime_id)
        self.assertEqual(h.worker_id, None)
        self.assertIsNotNone(h.submitted_at)
        st = rt.status(h.handle_id)
        self.assertTrue(st["ok"])
        self.assertEqual(st["phase"], "QUEUED")

    # ------------------------------------------------------------------
    # 4. Successful tool execution (governed boundary: tools.call_tool)
    # ------------------------------------------------------------------

    def test_03_successful_tool_execution(self):
        rt = self._rt(auto_start=False)
        h = rt.submit(_make_request(tool="echo", input_data={"text": "ping"}))
        rt.start(h.handle_id)
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        r = _result(rt, h)
        self.assertEqual(r.status, RuntimeResultStatus.SUCCEEDED)
        self.assertEqual(r.output["echo"], "ping")
        self.assertEqual(r.execution_id, "exe_test_1")
        self.assertEqual(r.job_id, "exe_test_1")
        self.assertEqual(rt.status(h.handle_id)["phase"], "TERMINAL")

    # ------------------------------------------------------------------
    # 4b. Failed tool execution (approved taxonomy, descriptive retryable)
    # ------------------------------------------------------------------

    def test_04_failed_tool_execution(self):
        rt = self._rt(auto_start=False)
        h = rt.submit(_make_request(tool="no_such_tool_xyz"))
        rt.start(h.handle_id)
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        r = _result(rt, h)
        self.assertEqual(r.status, RuntimeResultStatus.FAILED)
        # call_tool returns {"ok": False}; Hermes reports descriptive retryable=True
        self.assertIsNotNone(r.error)
        self.assertEqual(r.error.error_type, RuntimeErrorType.UNKNOWN)
        self.assertTrue(r.error.retryable)
        self.assertIn("no_such_tool_xyz", r.error.message)

    # ------------------------------------------------------------------
    # 5. Duplicate submission / idempotency — never two runtime jobs
    # ------------------------------------------------------------------

    def test_05_duplicate_submission_idempotent(self):
        rt = self._rt()
        req = _make_request()
        h1 = rt.submit(req)
        h2 = rt.submit(req)
        self.assertIs(h1, h2)                       # same handle
        self.assertEqual(h1.handle_id, h2.handle_id)
        st = rt.status(h1.handle_id)
        self.assertEqual(st["duplicate_submissions"], 2)   # counted, not duplicated
        # Same execution via an explicit idempotency_key must also dedup
        h3 = rt.submit(_make_request(idempotency_key="exe_test_1"))
        self.assertIs(h1, h3)
        # submitted + 2 duplicate events, but only ONE runtime job exists
        self.assertEqual(len([e for e in rt.events()
                              if e["event_type"] == "TRANSPORT_SUBMITTED"]), 1)
        self.assertEqual(len([e for e in rt.events()
                              if e["event_type"] == "TRANSPORT_DUPLICATE_SUBMIT"]), 2)

    def test_06_conflicting_identity_rejected(self):
        rt = self._rt()
        rt.submit(_make_request(exec_id="exe_A", idempotency_key="shared_key"))
        with self.assertRaises(ValueError):
            rt.submit(_make_request(exec_id="exe_B", idempotency_key="shared_key"))

    # ------------------------------------------------------------------
    # 6. Invalid execution identity (job_id == execution_id invariant)
    # ------------------------------------------------------------------

    def test_07_invalid_execution_identity(self):
        with self.assertRaises(ValueError):
            RuntimeJob(job_id="job_A", execution_id="job_B", mission_id="m",
                       task_id="t", attempt_no=1, input={}, metadata={},
                       timeout_sec=None, correlation_id="c")
        rt = self._rt()
        with self.assertRaises(ValueError):
            rt.submit("not a RuntimeRequest")

    # ------------------------------------------------------------------
    # 7. Cancellation — queued (immediate) and running (cooperative)
    # ------------------------------------------------------------------

    def test_08_cancellation_queued(self):
        rt = self._rt(auto_start=False)
        h = rt.submit(_make_request())
        resp = rt.cancel(h.handle_id)
        self.assertTrue(resp["ok"])
        self.assertTrue(resp["cooperative"])
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        r = _result(rt, h)
        self.assertEqual(r.status, RuntimeResultStatus.CANCELLED)
        # Idempotent
        again = rt.cancel(h.handle_id)
        self.assertTrue(again["ok"])
        self.assertTrue(again["already_terminal"])

    def test_09_cancellation_running_cooperative(self):
        def slow_call_tool(name, args, business_id=None):
            time.sleep(0.5)
            return {"tool": name, "ok": True, "echo": "late"}

        tools.call_tool = slow_call_tool
        rt = self._rt(auto_start=True)
        h = rt.submit(_make_request())
        _wait_until(lambda: rt.heartbeat(h.handle_id)["alive"])
        rt.cancel(h.handle_id)
        _wait_until(lambda: rt.result(h.handle_id) is not None, timeout=3.0)
        r = _result(rt, h)
        self.assertEqual(r.status, RuntimeResultStatus.CANCELLED)
        self.assertIn("cancelled", r.error.message)

    # ------------------------------------------------------------------
    # 8. Timeout observation (reports TIMED_OUT; EE decides the rest)
    # ------------------------------------------------------------------

    def test_10_timeout_reporting(self):
        def slow_call_tool(name, args, business_id=None):
            time.sleep(2.0)
            return {"tool": name, "ok": True, "echo": "too_late"}

        tools.call_tool = slow_call_tool
        rt = self._rt(auto_start=True)
        h = rt.submit(_make_request(timeout_sec=0.15))
        _wait_until(lambda: rt.result(h.handle_id) is not None, timeout=3.0)
        r = _result(rt, h)
        self.assertEqual(r.status, RuntimeResultStatus.TIMED_OUT)
        self.assertEqual(r.error.error_type, RuntimeErrorType.TIMEOUT)
        self.assertIn("exceeded timeout", r.error.message)

    # ------------------------------------------------------------------
    # 9. Heartbeat (liveness transport ping — never a lease)
    # ------------------------------------------------------------------

    def test_11_heartbeat(self):
        def slow_call_tool(name, args, business_id=None):
            time.sleep(0.4)
            return {"tool": name, "ok": True, "echo": "hb"}

        tools.call_tool = slow_call_tool
        rt = self._rt(auto_start=True)
        h = rt.submit(_make_request())
        _wait_until(lambda: rt.heartbeat(h.handle_id)["alive"])
        hb = rt.heartbeat(h.handle_id)
        self.assertTrue(hb["ok"])
        self.assertEqual(hb["phase"], "RUNNING")
        self.assertTrue(hb["alive"])
        self.assertEqual(hb["execution_id"], "exe_test_1")
        self.assertIsNotNone(hb["runtime_id"])
        self.assertIsNotNone(hb["worker_id"])
        # After terminal, heartbeat reports not alive
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        self.assertFalse(rt.heartbeat(h.handle_id)["alive"])

    # ------------------------------------------------------------------
    # 10. Status phases
    # ------------------------------------------------------------------

    def test_12_status_phases(self):
        def slow_call_tool(name, args, business_id=None):
            time.sleep(0.3)
            return {"tool": name, "ok": True, "echo": "st"}

        tools.call_tool = slow_call_tool
        rt = self._rt(auto_start=True)
        h = rt.submit(_make_request())
        st = rt.status(h.handle_id)
        self.assertIn(st["phase"], ("QUEUED", "RUNNING"))
        _wait_until(lambda: rt.status(h.handle_id)["phase"] == "RUNNING")
        self.assertIsNone(rt.status(h.handle_id)["status"])
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        end = rt.status(h.handle_id)
        self.assertEqual(end["phase"], "TERMINAL")
        self.assertEqual(end["status"], "SUCCEEDED")

    # ------------------------------------------------------------------
    # 11. Result retrieval
    # ------------------------------------------------------------------

    def test_13_result_retrieval(self):
        rt = self._rt(auto_start=False)
        h = rt.submit(_make_request(tool="echo", input_data={"text": "res"}))
        self.assertIsNone(rt.result(h.handle_id))
        rt.start(h.handle_id)
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        r = _result(rt, h)
        self.assertIsInstance(r, RuntimeResult)
        self.assertEqual(r.output["echo"], "res")

    # ------------------------------------------------------------------
    # 12. Terminate
    # ------------------------------------------------------------------

    def test_14_terminate(self):
        rt = self._rt(auto_start=False)
        h = rt.submit(_make_request())
        t1 = rt.terminate()
        self.assertTrue(t1["ok"])
        self.assertTrue(t1["terminated"])
        self.assertEqual(t1["live"], 0)
        r = _result(rt, h)
        self.assertEqual(r.status, RuntimeResultStatus.CANCELLED)
        t2 = rt.terminate()
        self.assertTrue(t2["already_terminated"])
        with self.assertRaises(ValueError):
            rt.submit(_make_request(exec_id="exe_z"))

    # ------------------------------------------------------------------
    # 13. Recovery — bounded, idempotent, runtime handles only
    # ------------------------------------------------------------------

    def test_15_recovery_crash(self):
        rt = self._rt(auto_start=False)
        h = rt.submit(_make_request())
        entry = rt._jobs[h.execution_id]
        entry["phase"] = "RUNNING"           # simulate started-but-lost worker
        entry["thread"] = _FakeDeadThread()
        res = rt.recover()
        self.assertEqual(res["ok"], True)
        self.assertEqual(res["checked"], 1)
        self.assertEqual(res["recovered"], [h.execution_id])
        r = _result(rt, h)
        self.assertEqual(r.status, RuntimeResultStatus.FAILED)
        self.assertEqual(r.error.error_type, RuntimeErrorType.CRASH)
        self.assertTrue(r.error.retryable)
        # Idempotent — second recover finds nothing new
        res2 = rt.recover()
        self.assertEqual(res2["recovered"], [])

    # ------------------------------------------------------------------
    # 14. Invalid result handling (INVALID_RESULT taxonomy)
    # ------------------------------------------------------------------

    def test_16_invalid_result_handling(self):
        def bad_call_tool(name, args, business_id=None):
            return "not a dict"

        tools.call_tool = bad_call_tool
        rt = self._rt(auto_start=True)
        h = rt.submit(_make_request())
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        r = _result(rt, h)
        self.assertEqual(r.status, RuntimeResultStatus.FAILED)
        self.assertEqual(r.error.error_type, RuntimeErrorType.INVALID_RESULT)

    # ------------------------------------------------------------------
    # 15. Authorization/governance rejection (fail-closed, never grants)
    # ------------------------------------------------------------------

    def test_17_governance_denial(self):
        rt = self._rt(auto_start=True, governance_check=lambda req: False)
        h = rt.submit(_make_request())
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        r = _result(rt, h)
        self.assertEqual(r.status, RuntimeResultStatus.FAILED)
        self.assertEqual(r.error.error_type, RuntimeErrorType.GOVERNANCE_DENIED)

    def test_18_governance_error_fails_closed(self):
        rt = self._rt(auto_start=True, governance_check=_boom_check)
        h = rt.submit(_make_request())
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        r = _result(rt, h)
        self.assertEqual(r.error.error_type, RuntimeErrorType.GOVERNANCE_DENIED)
        self.assertIn("errored", r.error.message)

    # ------------------------------------------------------------------
    # 16. Secret-safe representation (redaction at transport boundary)
    # ------------------------------------------------------------------

    def test_19_secret_safe_representation(self):
        rt = self._rt(auto_start=False)
        h = rt.submit(_make_request(
            input_data={"text": "hello", "api_key": "sk-super-secret-123"},
            metadata_extra={"password": "hunter2"}))
        rt.start(h.handle_id)
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        r = _result(rt, h)
        self.assertEqual(r.output["echo"], "hello")       # tool echoed text only
        for ev in rt.events():
            s = json.dumps(ev)
            self.assertNotIn("sk-super-secret-123", s)
            self.assertNotIn("hunter2", s)
        with self.assertRaises(ValueError):
            _make_request(input_data={"code": lambda: 1})  # executable rejected

    # ------------------------------------------------------------------
    # 17. Correlation identity preservation
    # ------------------------------------------------------------------

    def test_20_correlation_identity_preservation(self):
        rt = self._rt(auto_start=False)
        h = rt.submit(_make_request(exec_id="exe_corr_9", mission="m_9", task="t_9",
                                    corr="corr_9", tool="echo",
                                    input_data={"text": "corr"}))
        rt.start(h.handle_id)
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        r = _result(rt, h)
        self.assertEqual(r.execution_id, "exe_corr_9")
        self.assertEqual(r.job_id, "exe_corr_9")
        self.assertEqual(r.correlation_id, "corr_9")
        evs = [e for e in rt.events() if e["event_type"] == "TRANSPORT_SUCCEEDED"]
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["mission_id"], "m_9")
        self.assertEqual(evs[0]["task_id"], "t_9")
        self.assertEqual(evs[0]["attempt_no"], 1)
        self.assertEqual(evs[0]["correlation_id"], "corr_9")

    # ------------------------------------------------------------------
    # 18. No executable payload bypass & no shell/eval
    # ------------------------------------------------------------------

    def test_21_no_executable_payload_bypass(self):
        # Executable-looking STRINGS are opaque data at the transport layer —
        # the tool registry (tools.call_tool) is the only interpreter boundary.
        # So this is legal payload data:
        job = RuntimeJob(job_id="e", execution_id="e", mission_id="m", task_id="t",
                         attempt_no=1, input={"shell": "rm -rf /"},
                         metadata={"tool": "echo"}, timeout_sec=None,
                         correlation_id="c", capabilities=CAPS)
        self.assertEqual(job.input["shell"], "rm -rf /")
        # But executable OBJECTS (callables) must be rejected by the contract —
        # in both input and metadata.
        with self.assertRaises(ValueError):
            _make_request(metadata_extra={"fn": lambda: 1})
        # Proves the transport never imports or uses eval/exec/subprocess
        # primitives (docstring prose is allowed to name the rule; usage is not).
        import agent.hermes_runtime as hr
        with open(hr.__file__) as fh:
            src = fh.read()
        for usage in ("import subprocess", "from subprocess", "subprocess.run",
                      "subprocess.Popen", "os.system", "shell=True", "eval(",
                      "exec(", "pickle.loads"):
            self.assertNotIn(usage, src)

    # ------------------------------------------------------------------
    # 19/20. Backward compatibility (legacy governed boundary unaffected)
    # ------------------------------------------------------------------

    def test_22_backward_compatibility(self):
        # Legacy call_tool still works after Hermes used it
        rt = self._rt(auto_start=True)
        h = rt.submit(_make_request(tool="echo", input_data={"text": "legacy"}))
        _wait_until(lambda: rt.result(h.handle_id) is not None)
        self.assertEqual(_result(rt, h).status, RuntimeResultStatus.SUCCEEDED)
        direct = tools.call_tool("echo", {"text": "still works"})
        self.assertEqual(direct["ok"], True)
        self.assertEqual(direct["echo"], "still works")
        unknown = tools.call_tool("definitely_not_a_tool_42", {})
        self.assertEqual(unknown["ok"], False)
        self.assertIn("Unknown tool", unknown["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)