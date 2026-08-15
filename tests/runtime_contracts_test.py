#!/usr/bin/env python3
"""Unit tests for HEER Runtime Contracts (Phase 3.4.1).
Run from repo root:  python3 tests/runtime_contracts_test.py
Deterministic: no sleeps, network, SQLite, server, threads, or real tools.
"""
import os, sys, unittest, json
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path: sys.path.insert(0, _BASE)
from agent.runtime_contracts import (
    RuntimeJob, RuntimeRequest, RuntimeResult, RuntimeError, RuntimeHandle,
    RuntimeCapabilities, RuntimeResultStatus, RuntimeErrorType,
    RuntimeTransportKind, RuntimeIsolation, RuntimeCapability,
    to_dict, from_dict, to_json, from_json,
)

CAPS = RuntimeCapabilities(transport=RuntimeTransportKind.INPROCESS, isolation=RuntimeIsolation.NONE,
                           max_concurrency=8, supports_heartbeat=True, supports_hard_timeout=True,
                           features=frozenset({RuntimeCapability.CANCELLATION, RuntimeCapability.TIMEOUT}))


def job(eid="exec_1", mid="mission_1", tid="task_1", attempt=1,
        input_data=None, metadata_data=None):
    return RuntimeJob(job_id=eid, execution_id=eid, mission_id=mid, task_id=tid,
                      attempt_no=attempt,
                      input={"tag": "t"} if input_data is None else input_data,
                      metadata={"tool": "fake_tool"} if metadata_data is None else metadata_data,
                      timeout_sec=60.0, correlation_id="corr_1", capabilities=CAPS)


class RuntimeContractsTest(unittest.TestCase):

    def test_01_runtime_job_creation(self):
        j = job()
        self.assertEqual(j.job_id, "exec_1"); self.assertEqual(j.attempt_no, 1)
        self.assertEqual(j.timeout_sec, 60.0); self.assertEqual(j.correlation_id, "corr_1")
        self.assertEqual(j.metadata["tool"], "fake_tool")

    def test_02_runtime_job_immutability(self):
        j = job()
        with self.assertRaises(AttributeError):
            j.attempt_no = 2
        with self.assertRaises(TypeError):
            dict.__setitem__(j.input, "x", 1)

    def test_03_execution_id_equals_job_id_invariant(self):
        with self.assertRaises(ValueError):
            RuntimeJob(job_id="a", execution_id="b", mission_id="m", task_id="t",
                       attempt_no=1, input={}, metadata={}, timeout_sec=None, correlation_id="c")

    def test_04_invalid_identifiers_rejected(self):
        for field in ("job_id", "mission_id", "task_id", "correlation_id"):
            with self.assertRaises(ValueError):
                RuntimeJob(job_id="e" if field != "job_id" else "", execution_id="e",
                           mission_id="m" if field != "mission_id" else "",
                           task_id="t" if field != "task_id" else "",
                           attempt_no=1, input={}, metadata={}, timeout_sec=None,
                           correlation_id="c" if field != "correlation_id" else "")

    def test_05_invalid_attempt_no_rejected(self):
        for bad in (0, -1, 1.5, True, "1", None):
            with self.assertRaises(ValueError):
                job(attempt=bad)

    def test_06_runtime_request_creation(self):
        r = RuntimeRequest(job=job(), requested_at=100.0, requested_by="execution_engine",
                           capabilities_required=CAPS)
        self.assertEqual(r.job.job_id, "exec_1"); self.assertEqual(r.requested_by, "execution_engine")

    def test_07_idempotency_key_behavior(self):
        r1 = RuntimeRequest(job=job(), requested_at=1.0, requested_by="ee", capabilities_required=None)
        r2 = RuntimeRequest(job=job(), requested_at=2.0, requested_by="ee", capabilities_required=None)
        self.assertEqual(r1.idempotency_key, "exec_1"); self.assertEqual(r2.idempotency_key, "exec_1")
        self.assertTrue(r1.is_duplicate_of(r2))
        r3 = RuntimeRequest(job=job(eid="exec_2"), requested_at=1.0, requested_by="ee",
                            capabilities_required=None)
        self.assertFalse(r1.is_duplicate_of(r3))

    def test_08_runtime_result_success(self):
        r = RuntimeResult(execution_id="exec_1", job_id="exec_1",
                          status=RuntimeResultStatus.SUCCEEDED, output={"ok": True},
                          started_at=10.0, finished_at=12.0)
        self.assertEqual(r.status, RuntimeResultStatus.SUCCEEDED)
        self.assertEqual(r.output["ok"], True)

    def test_09_runtime_result_failure(self):
        err = RuntimeError(error_type=RuntimeErrorType.CRASH, message="worker died",
                           retryable=True, execution_id="exec_1", job_id="exec_1")
        r = RuntimeResult(execution_id="exec_1", job_id="exec_1",
                          status=RuntimeResultStatus.FAILED, error=err,
                          started_at=1.0, finished_at=2.0)
        self.assertEqual(r.error.error_type, RuntimeErrorType.CRASH)
        self.assertTrue(r.error.retryable); self.assertEqual(r.error.job_id, "exec_1")

    def test_10_timestamp_validation(self):
        with self.assertRaises(ValueError):
            RuntimeResult(execution_id="e", job_id="e", status=RuntimeResultStatus.SUCCEEDED,
                          started_at=10.0, finished_at=9.0)
        with self.assertRaises(ValueError):
            RuntimeResult(execution_id="e", job_id="e", status=RuntimeResultStatus.SUCCEEDED,
                          started_at=float("nan"), finished_at=9.0)


    def test_11_runtime_error_taxonomy(self):
        expected = {"TIMEOUT", "CRASH", "INVALID_RESULT", "AUTH_DENIED", "GOVERNANCE_DENIED",
                    "CAPACITY_LIMIT", "TRANSPORT", "UNKNOWN"}
        self.assertEqual(expected, {e.name for e in RuntimeErrorType})
        self.assertEqual(expected, set(RuntimeErrorType.__members__.keys()))

    def test_12_retryable_is_descriptive_only(self):
        err = RuntimeError(error_type=RuntimeErrorType.TRANSPORT, message="conn lost", retryable=True)
        self.assertTrue(err.retryable)
        err2 = RuntimeError(error_type=RuntimeErrorType.CRASH, message="boom", retryable=False)
        self.assertFalse(err2.retryable)

    def test_13_runtime_handle_identity(self):
        h = RuntimeHandle(handle_id="hdl_abc", execution_id="exec_1", runtime_id="rt_1",
                          worker_id="w_1", submitted_at=5.0)
        self.assertEqual(h.handle_id, "hdl_abc"); self.assertEqual(h.worker_id, "w_1")
        self.assertFalse(any(hasattr(h, f) for f in ("lease_owner", "lease_expires_at")))

    def test_14_runtime_capabilities(self):
        self.assertEqual(CAPS.transport, RuntimeTransportKind.INPROCESS)
        self.assertEqual(CAPS.max_concurrency, 8)
        self.assertTrue(CAPS.supports_heartbeat)
        self.assertIn(RuntimeCapability.CANCELLATION, CAPS.features)
        with self.assertRaises(ValueError):
            RuntimeCapabilities(transport=RuntimeTransportKind.INPROCESS,
                                isolation=RuntimeIsolation.NONE, max_concurrency=0)

    def test_15_serialization_round_trip(self):
        for obj in (job(),
                    RuntimeRequest(job=job(), requested_at=1.0, requested_by="ee",
                                   capabilities_required=None),
                    RuntimeResult(execution_id="e", job_id="e",
                                  status=RuntimeResultStatus.SUCCEEDED, output={"ok": True}),
                    RuntimeHandle(handle_id="h", execution_id="e", submitted_at=1.0),
                    CAPS,
                    RuntimeError(error_type=RuntimeErrorType.TIMEOUT, message="m", retryable=True)):
            d = to_dict(obj); restored = from_dict(d, type(obj))
            self.assertEqual(to_dict(restored), d, f"round-trip failed for {type(obj).__name__}")

    def test_16_malformed_deserialization_rejected(self):
        with self.assertRaises(ValueError):
            from_dict({"job_id": "x"}, RuntimeJob)
        with self.assertRaises(ValueError):
            from_dict({"execution_id": "e", "job_id": "e",
                       "status": "NOT_A_STATUS"}, RuntimeResult)
        with self.assertRaises(ValueError):
            from_dict({"job_id": "e", "execution_id": "e", "mission_id": "m",
                       "task_id": "t", "attempt_no": 1, "correlation_id": "c",
                       "capabilities": {"transport": "BOGUS", "isolation": "NONE"}},
                      RuntimeJob)
        with self.assertRaises((ValueError, TypeError)):
            from_dict("not a dict", RuntimeJob)

    def test_17_json_safe_serialization(self):
        j2 = to_dict(job())
        json.dumps(j2)
        self.assertTrue(all(isinstance(v, (str, int, float, bool, type(None), dict))
                            for v in j2.values()))

    def test_18_no_executable_payload_acceptance(self):
        with self.assertRaises(ValueError):
            job(input_data={"code": lambda: None})
        with self.assertRaises(ValueError):
            job(metadata_data={"f": lambda: None})
        with self.assertRaises(ValueError):
            RuntimeError(error_type=RuntimeErrorType.UNKNOWN, message="m",
                         details={"code": lambda: None})
        with self.assertRaises(ValueError):
            job(input_data={"cmd": b"rm -rf /"})

    def test_19_deterministic_serialization(self):
        self.assertEqual(to_json(job()), to_json(job()))
        r = RuntimeResult(execution_id="e", job_id="e",
                          status=RuntimeResultStatus.SUCCEEDED, output={"z": 1, "a": 2})
        self.assertEqual(to_json(r), to_json(from_dict(to_dict(r), RuntimeResult)))
        s = to_json(job())
        self.assertNotIn(": ", s); self.assertNotIn(", ", s)
        self.assertEqual(list(json.loads(s).keys()), sorted(json.loads(s).keys()))

    def test_20_secret_safe_representation(self):
        j = job(input_data={"api_key": "sk-1234", "note": "hello"})
        d = to_dict(j)
        self.assertEqual(d["input"]["api_key"], "[REDACTED]")
        self.assertEqual(d["input"]["note"], "hello")
        self.assertIn("sk-1234", str(j.input))
        self.assertNotIn("sk-1234", to_json(j))


if __name__ == "__main__":
    unittest.main(verbosity=2)
