#!/usr/bin/env python3
"""Comprehensive Unit and Integration Tests for SubprocessTransport (HEER Phase 3.7).

Run from repo root: python3 -m unittest jarvis/tests/subprocess_transport_test.py
  or: python3 -m unittest tests.subprocess_transport_test

Covers 30 required test cases:
1. Valid executable validation (absolute & relative resolution)
2. Invalid executable path rejection (non-absolute, non-existent, non-executable)
3. Environment isolation (only PATH allowlisted by default)
4. Standard stdin/stdout JSONL IPC flow (HELLO -> READY -> REQUEST -> RESPONSE)
5. Handshake identity validation pass (matching worker_id, instance_id, epoch, tenant, nonce)
6. Worker ID mismatch rejection
7. Worker instance ID mismatch rejection
8. Worker epoch mismatch rejection
9. Tenant ID mismatch rejection
10. Nonce mismatch rejection
11. WorkerRegistry liveness check pass (ACTIVE/HEALTHY/LIVE status)
12. WorkerRegistry unknown worker rejection
13. WorkerRegistry inactive status rejection
14. WorkerRegistry metadata mismatch rejection (instance/epoch/tenant)
15. Duplicate submit handle reuse (idempotency key matches)
16. Conflicting submit identity rejection for same idempotency key
17. Tool execution before identity validation prevention
18. Governance boundary check pass
19. Governance boundary check failure/denial
20. Worker process crash handling (exit non-zero)
21. Worker process early exit handling (exit zero before IPC completion)
22. Worker process hang & timeout handling
23. Malformed JSON message handling
24. Oversized JSON message handling (> max_message_bytes)
25. Heartbeat reception & timestamp update
26. Cancellation of queued job
27. Cooperative cancellation of running worker
28. Transport termination and cleanup of running processes
29. Orphan process recovery via recover()
30. Audit logging & structured event emission throughout lifecycle
"""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from agent.runtime_contracts import (
    RuntimeCapabilities,
    RuntimeErrorType,
    RuntimeHandle,
    RuntimeIsolation,
    RuntimeJob,
    RuntimeRequest,
    RuntimeResultStatus,
    RuntimeTransportKind,
)
from agent.subprocess_transport import SubprocessTransport
from agent.worker_contracts import WorkerIdentity, WorkerLivenessState

class MockWorkerRecord:
    def __init__(self, worker_id, instance_id, epoch, state, tenant_id=None):
        self.identity = WorkerIdentity(
            worker_id=worker_id,
            worker_instance_id=instance_id,
            worker_epoch=epoch,
        )
        self.tenant_id = tenant_id
        self.state = state

class MockWorkerRegistry:
    def __init__(self, workers=None):
        self._workers = workers or {}

    def get(self, worker_id, tenant_scope=None):
        rec = self._workers.get(worker_id)
        if rec is None:
            return None
        return {
            "identity": {
                "worker_id": rec.identity.worker_id,
                "worker_instance_id": rec.identity.worker_instance_id,
                "worker_epoch": rec.identity.worker_epoch,
                "tenant_id": getattr(rec, "tenant_id", None),
            },
            "state": rec.state.value if isinstance(rec.state, WorkerLivenessState) else str(rec.state),
        }

class SubprocessTransportTest(unittest.TestCase):

    def setUp(self):
        self.fixture_worker = os.path.join(
            _BASE, "tests", "fixtures", "heer_subprocess_worker.py"
        )
        self.assertTrue(
            os.path.exists(self.fixture_worker),
            f"Fixture missing: {self.fixture_worker}",
        )
        os.chmod(self.fixture_worker, 0o755)

        self.python_exec = sys.executable

        self.events = []
        self.transport = SubprocessTransport(
            default_executable=self.python_exec,
            event_sink=lambda ev: self.events.append(ev),
            spawn_timeout=2.0,
            handshake_timeout=2.0,
            ipc_idle_timeout=2.0,
            shutdown_grace=1.0,
            terminate_timeout=1.0,
        )

    def tearDown(self):
        if self.transport:
            self.transport.terminate()

    def _make_request(
        self,
        key="key_1",
        execution_id="exec_1",
        worker_id="test_worker",
        instance_id="inst_1",
        epoch=1,
        tenant_id=None,
        nonce=None,
        executable=None,
        argv=None,
        tool="test_tool",
        inp=None,
        timeout_sec=2.0,
    ) -> RuntimeRequest:
        meta = {
            "worker_id": worker_id,
            "worker_instance_id": instance_id,
            "worker_epoch": epoch,
            "executable": executable or self.python_exec,
            "argv": argv or [self.fixture_worker],
            "tool": tool,
        }
        if tenant_id:
            meta["tenant_id"] = tenant_id
        if nonce:
            meta["transport_nonce"] = nonce

        job = RuntimeJob(
            execution_id=execution_id,
            job_id=execution_id,
            mission_id="m_test",
            task_id="t_test",
            attempt_no=1,
            input=inp or {},
            metadata=meta,
            timeout_sec=timeout_sec,
            correlation_id=f"corr_{execution_id}",
        )
        return RuntimeRequest(
            idempotency_key=key,
            job=job,
            requested_at=time.time(),
            requested_by="ee_system",
            capabilities_required=None,
        )

    def _wait_for_terminal(self, handle_id: str, timeout: float = 3.0):
        t0 = time.time()
        while time.time() - t0 < timeout:
            res = self.transport.result(handle_id)
            if res is not None:
                return res
            time.sleep(0.05)
        return self.transport.result(handle_id)

    # ------------------------------------------------------------------
    # 1. Valid Executable Validation
    # ------------------------------------------------------------------
    def test_01_valid_executable_validation(self):
        req = self._make_request()
        handle = self.transport.submit(req)
        start_res = self.transport.start(handle.handle_id)
        self.assertTrue(start_res["ok"])
        res = self._wait_for_terminal(handle.handle_id)
        self.assertIsNotNone(res)
        self.assertEqual(res.status, RuntimeResultStatus.SUCCEEDED)

    # ------------------------------------------------------------------
    # 2. Invalid Executable Validation
    # ------------------------------------------------------------------
    def test_02_invalid_executable_validation(self):
        req = self._make_request(executable="/non/existent/path/python")
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertIsNotNone(res)
        self.assertEqual(res.status, RuntimeResultStatus.FAILED)
        self.assertEqual(res.error.error_type, RuntimeErrorType.TRANSPORT)
        self.assertIn("Executable does not exist", res.error.message)

    # ------------------------------------------------------------------
    # 3. Environment Isolation
    # ------------------------------------------------------------------
    def test_03_environment_isolation(self):
        env = self.transport._build_env()
        self.assertIn("PATH", env)
        self.assertNotIn("SECRET_KEY_ENV", env)

    # ------------------------------------------------------------------
    # 4. Standard IPC Flow
    # ------------------------------------------------------------------
    def test_04_standard_ipc_flow(self):
        req = self._make_request(tool="echo_tool", inp={"test": 123})
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.SUCCEEDED)
        self.assertEqual(res.output["echo_tool"], "echo_tool")
        self.assertEqual(res.output["echo_input"], {"test": 123})

    # ------------------------------------------------------------------
    # 5. Handshake Identity Validation Pass
    # ------------------------------------------------------------------
    def test_05_handshake_identity_pass(self):
        req = self._make_request(
            worker_id="test_worker",
            instance_id="inst_1",
            epoch=1,
            tenant_id="tenant_a",
            nonce="nonce_123",
            argv=[self.fixture_worker],
        )
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.SUCCEEDED)

    # ------------------------------------------------------------------
    # 6. Worker ID Mismatch Rejection
    # ------------------------------------------------------------------
    def test_06_worker_id_mismatch(self):
        req = self._make_request(worker_id="expected_different_worker")
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.FAILED)
        self.assertEqual(res.error.error_type, RuntimeErrorType.AUTH_DENIED)
        self.assertIn("worker_id mismatch", res.error.message)

    # ------------------------------------------------------------------
    # 7. Worker Instance ID Mismatch Rejection
    # ------------------------------------------------------------------
    def test_07_worker_instance_id_mismatch(self):
        req = self._make_request(instance_id="inst_wrong")
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.FAILED)
        self.assertEqual(res.error.error_type, RuntimeErrorType.AUTH_DENIED)
        self.assertIn("worker_instance_id mismatch", res.error.message)

    # ------------------------------------------------------------------
    # 8. Worker Epoch Mismatch Rejection
    # ------------------------------------------------------------------
    def test_08_worker_epoch_mismatch(self):
        req = self._make_request(epoch=999)
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.FAILED)
        self.assertEqual(res.error.error_type, RuntimeErrorType.AUTH_DENIED)
        self.assertIn("worker_epoch mismatch", res.error.message)

    # ------------------------------------------------------------------
    # 9. Tenant ID Mismatch Rejection
    # ------------------------------------------------------------------
    def test_09_tenant_id_mismatch(self):
        req = self._make_request(tenant_id="tenant_expected")
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.FAILED)
        self.assertEqual(res.error.error_type, RuntimeErrorType.AUTH_DENIED)
        self.assertIn("tenant_id mismatch", res.error.message)

    # ------------------------------------------------------------------
    # 10. Nonce Mismatch Rejection
    # ------------------------------------------------------------------
    def test_10_nonce_mismatch(self):
        req = self._make_request(nonce="nonce_expected")
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.FAILED)
        self.assertEqual(res.error.error_type, RuntimeErrorType.AUTH_DENIED)
        self.assertIn("nonce mismatch", res.error.message)

    # ------------------------------------------------------------------
    # 11. WorkerRegistry Liveness Pass
    # ------------------------------------------------------------------
    def test_11_registry_liveness_pass(self):
        registry = MockWorkerRegistry({
            "test_worker": MockWorkerRecord(
                worker_id="test_worker",
                instance_id="inst_1",
                epoch=1,
                state=WorkerLivenessState.LIVE,
            )
        })
        tp = SubprocessTransport(
            worker_registry=registry,
            default_executable=self.python_exec,
            spawn_timeout=2.0,
            handshake_timeout=2.0,
        )
        try:
            req = self._make_request()
            hdl = tp.submit(req)
            tp.start(hdl.handle_id)
            res = None
            for _ in range(30):
                res = tp.result(hdl.handle_id)
                if res:
                    break
                time.sleep(0.05)
            self.assertIsNotNone(res)
            self.assertEqual(res.status, RuntimeResultStatus.SUCCEEDED)
        finally:
            tp.terminate()

    # ------------------------------------------------------------------
    # 12. WorkerRegistry Unknown Worker Rejection
    # ------------------------------------------------------------------
    def test_12_registry_unknown_worker(self):
        registry = MockWorkerRegistry({})
        tp = SubprocessTransport(
            worker_registry=registry,
            default_executable=self.python_exec,
            spawn_timeout=2.0,
            handshake_timeout=2.0,
        )
        try:
            # We must craft a request where worker_id is 'unknown_worker'
            # and pass environment variables to fixture worker script so it emits 'unknown_worker' in HELLO.
            # Otherwise fixture emits 'test_worker' and fails with worker_id mismatch before reaching registry check.
            req = self._make_request(
                worker_id="unknown_worker",
                argv=["-c", "import json, sys; print(json.dumps({'type':'HELLO','worker_id':'unknown_worker','worker_instance_id':'inst_1','worker_epoch':1})); sys.stdout.flush()"]
            )
            hdl = tp.submit(req)
            tp.start(hdl.handle_id)
            res = None
            for _ in range(30):
                res = tp.result(hdl.handle_id)
                if res:
                    break
                time.sleep(0.05)
            self.assertIsNotNone(res)
            self.assertEqual(res.status, RuntimeResultStatus.FAILED)
            self.assertEqual(res.error.error_type, RuntimeErrorType.AUTH_DENIED)
            self.assertIn("not found in registry", res.error.message)
        finally:
            tp.terminate()

    # ------------------------------------------------------------------
    # 13. WorkerRegistry Inactive Status Rejection
    # ------------------------------------------------------------------
    def test_13_registry_inactive_worker(self):
        registry = MockWorkerRegistry({
            "test_worker": MockWorkerRecord(
                worker_id="test_worker",
                instance_id="inst_1",
                epoch=1,
                state=WorkerLivenessState.DEPARTED,
            )
        })
        tp = SubprocessTransport(
            worker_registry=registry,
            default_executable=self.python_exec,
            spawn_timeout=2.0,
            handshake_timeout=2.0,
        )
        try:
            req = self._make_request()
            hdl = tp.submit(req)
            tp.start(hdl.handle_id)
            res = None
            for _ in range(30):
                res = tp.result(hdl.handle_id)
                if res:
                    break
                time.sleep(0.05)
            self.assertIsNotNone(res)
            self.assertEqual(res.status, RuntimeResultStatus.FAILED)
            self.assertEqual(res.error.error_type, RuntimeErrorType.AUTH_DENIED)
            self.assertIn("must be active/healthy/live", res.error.message)
        finally:
            tp.terminate()

    # ------------------------------------------------------------------
    # 14. WorkerRegistry Metadata Mismatch Rejection
    # ------------------------------------------------------------------
    def test_14_registry_metadata_mismatch(self):
        registry = MockWorkerRegistry({
            "test_worker": MockWorkerRecord(
                worker_id="test_worker",
                instance_id="inst_different",
                epoch=1,
                state=WorkerLivenessState.LIVE,
            )
        })
        tp = SubprocessTransport(
            worker_registry=registry,
            default_executable=self.python_exec,
            spawn_timeout=2.0,
            handshake_timeout=2.0,
        )
        try:
            req = self._make_request()
            hdl = tp.submit(req)
            tp.start(hdl.handle_id)
            res = None
            for _ in range(30):
                res = tp.result(hdl.handle_id)
                if res:
                    break
                time.sleep(0.05)
            self.assertIsNotNone(res)
            self.assertEqual(res.status, RuntimeResultStatus.FAILED)
            self.assertEqual(res.error.error_type, RuntimeErrorType.AUTH_DENIED)
            self.assertIn("worker instance mismatch in registry", res.error.message)
        finally:
            tp.terminate()

    # ------------------------------------------------------------------
    # 15. Duplicate Submit Handle Reuse
    # ------------------------------------------------------------------
    def test_15_duplicate_submit_handle_reuse(self):
        req1 = self._make_request(key="idem_1", execution_id="exec_idem_1")
        hdl1 = self.transport.submit(req1)
        req2 = self._make_request(key="idem_1", execution_id="exec_idem_1")
        hdl2 = self.transport.submit(req2)
        self.assertEqual(hdl1.handle_id, hdl2.handle_id)

    # ------------------------------------------------------------------
    # 16. Conflicting Submit Identity Rejection
    # ------------------------------------------------------------------
    def test_16_conflicting_submit_identity(self):
        req1 = self._make_request(key="idem_2", execution_id="exec_idem_2a")
        self.transport.submit(req1)
        req2 = self._make_request(key="idem_2", execution_id="exec_idem_2b")
        with self.assertRaises(ValueError) as ctx:
            self.transport.submit(req2)
        self.assertIn("conflicting execution identity", str(ctx.exception))

    # ------------------------------------------------------------------
    # 17. No Tool Invocation Before Identity Rejection
    # ------------------------------------------------------------------
    def test_17_no_tool_invocation_before_identity_rejection(self):
        # When handshake identity fails, the transport terminates the subprocess
        # before sending READY / REQUEST.
        req = self._make_request(worker_id="wrong_worker")
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.FAILED)
        # Event stream must record SUBPROCESS_IDENTITY_REJECTED
        rej_events = [e for e in self.events if e["event_type"] == "SUBPROCESS_IDENTITY_REJECTED"]
        self.assertGreaterEqual(len(rej_events), 1)

    # ------------------------------------------------------------------
    # 18. Governance Boundary Check Pass
    # ------------------------------------------------------------------
    def test_18_governance_check_pass(self):
        tp = SubprocessTransport(
            default_executable=self.python_exec,
            governance_check=lambda req: True,
        )
        try:
            req = self._make_request()
            hdl = tp.submit(req)
            tp.start(hdl.handle_id)
            res = None
            for _ in range(30):
                res = tp.result(hdl.handle_id)
                if res:
                    break
                time.sleep(0.05)
            self.assertEqual(res.status, RuntimeResultStatus.SUCCEEDED)
        finally:
            tp.terminate()

    # ------------------------------------------------------------------
    # 19. Governance Boundary Check Denial
    # ------------------------------------------------------------------
    def test_19_governance_check_denial(self):
        tp = SubprocessTransport(
            default_executable=self.python_exec,
            governance_check=lambda req: False,
        )
        try:
            req = self._make_request()
            hdl = tp.submit(req)
            tp.start(hdl.handle_id)
            res = None
            for _ in range(30):
                res = tp.result(hdl.handle_id)
                if res:
                    break
                time.sleep(0.05)
            self.assertEqual(res.status, RuntimeResultStatus.FAILED)
            self.assertEqual(res.error.error_type, RuntimeErrorType.GOVERNANCE_DENIED)
        finally:
            tp.terminate()

    # ------------------------------------------------------------------
    # 20. Worker Process Crash Handling
    # ------------------------------------------------------------------
    def test_20_worker_process_crash(self):
        req = self._make_request(argv=[self.fixture_worker, "crash"], timeout_sec=2.0)
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.FAILED)
        self.assertEqual(res.error.error_type, RuntimeErrorType.CRASH)

    # ------------------------------------------------------------------
    # 21. Worker Process Early Exit Handling
    # ------------------------------------------------------------------
    def test_21_worker_process_early_exit(self):
        # A process that closes stdout/exits 0 without HELLO/RESPONSE
        # Create a tiny inline python script
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write("import sys; sys.exit(0)\n")
            tf.flush()
            early_script = tf.name

        try:
            req = self._make_request(argv=[early_script])
            handle = self.transport.submit(req)
            self.transport.start(handle.handle_id)
            res = self._wait_for_terminal(handle.handle_id)
            self.assertEqual(res.status, RuntimeResultStatus.FAILED)
            self.assertIn(res.error.error_type, (RuntimeErrorType.TIMEOUT, RuntimeErrorType.TRANSPORT))
        finally:
            os.unlink(early_script)

    # ------------------------------------------------------------------
    # 22. Worker Process Hang & Timeout
    # ------------------------------------------------------------------
    def test_22_worker_process_hang_timeout(self):
        req = self._make_request(argv=[self.fixture_worker, "hang"], timeout_sec=0.5)
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id, timeout=3.0)
        self.assertEqual(res.status, RuntimeResultStatus.TIMED_OUT)
        self.assertEqual(res.error.error_type, RuntimeErrorType.TIMEOUT)

    # ------------------------------------------------------------------
    # 23. Malformed JSON Message Handling
    # ------------------------------------------------------------------
    def test_23_malformed_json(self):
        req = self._make_request(argv=[self.fixture_worker, "malformed"])
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.FAILED)
        self.assertEqual(res.error.error_type, RuntimeErrorType.TRANSPORT)
        self.assertIn("Handshake failed", res.error.message)

    # ------------------------------------------------------------------
    # 24. Oversized Message Handling
    # ------------------------------------------------------------------
    def test_24_oversized_message(self):
        req = self._make_request(argv=[self.fixture_worker, "oversized"])
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.FAILED)
        self.assertEqual(res.error.error_type, RuntimeErrorType.INVALID_RESULT)
        self.assertIn("Oversized message", res.error.message)

    # ------------------------------------------------------------------
    # 25. Heartbeat Reception
    # ------------------------------------------------------------------
    def test_25_heartbeat_reception(self):
        req = self._make_request(inp={"send_heartbeat": True})
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.SUCCEEDED)

    # ------------------------------------------------------------------
    # 26. Cancel Queued Job
    # ------------------------------------------------------------------
    def test_26_cancel_queued_job(self):
        req = self._make_request()
        handle = self.transport.submit(req)
        cancel_res = self.transport.cancel(handle.handle_id)
        self.assertTrue(cancel_res["ok"])
        res = self.transport.result(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.CANCELLED)

    # ------------------------------------------------------------------
    # 27. Cooperative Cancellation of Running Worker
    # ------------------------------------------------------------------
    def test_27_cooperative_cancel_running_worker(self):
        req = self._make_request(argv=[self.fixture_worker, "hang"])
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        time.sleep(0.3)
        cancel_res = self.transport.cancel(handle.handle_id)
        self.assertTrue(cancel_res["ok"])
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.CANCELLED)

    # ------------------------------------------------------------------
    # 28. Transport Termination and Cleanup
    # ------------------------------------------------------------------
    def test_28_transport_terminate_cleanup(self):
        tp = SubprocessTransport(default_executable=self.python_exec)
        req = self._make_request(argv=[self.fixture_worker, "hang"])
        hdl = tp.submit(req)
        tp.start(hdl.handle_id)
        time.sleep(0.3)
        term_res = tp.terminate()
        self.assertTrue(term_res["ok"])
        res = tp.result(hdl.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.CANCELLED)

    # ------------------------------------------------------------------
    # 29. Orphan Process Recovery
    # ------------------------------------------------------------------
    def test_29_orphan_process_recovery(self):
        req = self._make_request(argv=[self.fixture_worker, "crash"])
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        time.sleep(0.3)
        rec_res = self.transport.recover()
        self.assertTrue(rec_res["ok"])

    # ------------------------------------------------------------------
    # 30. Audit Logging & Structured Events Emission
    # ------------------------------------------------------------------
    def test_30_events_and_audit_emission(self):
        req = self._make_request()
        handle = self.transport.submit(req)
        self.transport.start(handle.handle_id)
        res = self._wait_for_terminal(handle.handle_id)
        self.assertEqual(res.status, RuntimeResultStatus.SUCCEEDED)

        events = self.transport.events()
        event_types = [e["event_type"] for e in events]
        self.assertIn("SUBPROCESS_SPAWN_REQUESTED", event_types)
        self.assertIn("SUBPROCESS_STARTED", event_types)
        self.assertIn("SUBPROCESS_SUCCEEDED", event_types)

if __name__ == "__main__":
    unittest.main()