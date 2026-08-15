#!/usr/bin/env python3
"""Unit tests for HEER Worker Fabric Contracts (Phase 3.5.1).
Run from repo root:  python3 tests/worker_contracts_test.py
Deterministic: no sleeps, network, SQLite, server, threads, or real tools.
"""
import os, sys, unittest, json
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path: sys.path.insert(0, _BASE)
from agent import worker_contracts as wc
from agent.runtime_contracts import (
    RuntimeCapabilities, RuntimeJob, RuntimeRequest, RuntimeCapability,
    RuntimeTransportKind, RuntimeIsolation,
    to_dict as rc_to_dict, from_dict as rc_from_dict,
)
from agent.worker_contracts import (
    WorkerLivenessState, WorkerIdentity, WorkerCapabilities, WorkerLiveness,
    WORKER_LIVENESS_STATE_VALUES,
    to_dict, from_dict, to_json, from_json,
)

RC = RuntimeCapabilities(transport=RuntimeTransportKind.INPROCESS,
                         isolation=RuntimeIsolation.NONE, max_concurrency=4,
                         supports_heartbeat=True, supports_hard_timeout=False,
                         features=frozenset({RuntimeCapability.CANCELLATION}))


def caps(tool_classes=None, cpu=None, mem=None, arch=None, net=None,
         region=None, compliance=None, version=None, rc=None):
    return WorkerCapabilities(
        runtime_capabilities=rc if rc is not None else RC,
        tool_classes=("bash", "file") if tool_classes is None else tool_classes,
        max_cpu_cores=cpu, max_memory_mb=mem, architecture=arch,
        network_policy=net, region=region, compliance_boundary=compliance,
        runtime_version=version)


def identity(worker="w_1", instance="w_1_inst_1", epoch=1, tenants=None,
             caps_value=None, isolation=RuntimeIsolation.NONE, transport="rt_1"):
    return WorkerIdentity(
        worker_id=worker, worker_instance_id=instance, worker_epoch=epoch,
        tenant_scope=("tenant_a",) if tenants is None else tenants,
        capabilities=caps_value, isolation_mode=isolation,
        transport_identity=transport)


def liveness(worker="w_1", instance="w_1_inst_1", epoch=1,
             state=WorkerLivenessState.LIVE, reported_at=None, seq=1):
    return WorkerLiveness(
        worker_id=worker, worker_instance_id=instance, worker_epoch=epoch,
        state=state,
        reported_at=100.0 if reported_at is None else reported_at,
        heartbeat_seq=seq)


class WorkerContractsTest(unittest.TestCase):

    def test_01_worker_identity_creation(self):
        i = identity(caps_value=caps())
        self.assertEqual(i.worker_id, "w_1")
        self.assertEqual(i.worker_instance_id, "w_1_inst_1")
        self.assertEqual(i.worker_epoch, 1)
        self.assertEqual(i.tenant_scope, ("tenant_a",))
        self.assertIsInstance(i.capabilities, WorkerCapabilities)
        self.assertEqual(i.isolation_mode, RuntimeIsolation.NONE)
        self.assertEqual(i.transport_identity, "rt_1")

    def test_02_worker_identity_immutability(self):
        i = identity()
        with self.assertRaises(AttributeError):
            i.worker_id = "w_2"
        with self.assertRaises(AttributeError):
            i.worker_epoch = 2
        with self.assertRaises(AttributeError):
            i.tenant_scope = ("tenant_b",)

    def test_03_worker_id_validation(self):
        for bad in ("", None):
            with self.assertRaises(ValueError):
                WorkerIdentity(worker_id=bad, worker_instance_id="i_1",
                               worker_epoch=1)

    def test_04_worker_instance_id_validation(self):
        for bad in ("", None):
            with self.assertRaises(ValueError):
                WorkerIdentity(worker_id="w_1", worker_instance_id=bad,
                               worker_epoch=1)

    def test_05_worker_epoch_validation(self):
        for bad in (0, -1, 1.5, True, "1", None):
            with self.assertRaises(ValueError):
                WorkerIdentity(worker_id="w_1", worker_instance_id="i_1",
                               worker_epoch=bad)

    def test_06_capabilities_validation(self):
        with self.assertRaises(ValueError):
            WorkerCapabilities(tool_classes="bash")
        with self.assertRaises(ValueError):
            WorkerCapabilities(max_cpu_cores=0)
        with self.assertRaises(ValueError):
            WorkerCapabilities(max_cpu_cores=True)
        with self.assertRaises(ValueError):
            WorkerCapabilities(max_memory_mb=-5)
        with self.assertRaises(ValueError):
            WorkerCapabilities(runtime_capabilities="not caps")

    def test_07_tenant_scope_validation(self):
        with self.assertRaises(ValueError):
            WorkerIdentity(worker_id="w", worker_instance_id="i", worker_epoch=1,
                           tenant_scope=("",))
        with self.assertRaises(ValueError):
            WorkerIdentity(worker_id="w", worker_instance_id="i", worker_epoch=1,
                           tenant_scope="tenant_a")
        with self.assertRaises(ValueError):
            WorkerIdentity(worker_id="w", worker_instance_id="i", worker_epoch=1,
                           tenant_scope=(True,))
        # deterministic: sorted + deduplicated, immutable tuple
        self.assertEqual(identity(tenants=("b", "a", "b")).tenant_scope,
                         ("a", "b"))

    def test_08_liveness_validation(self):
        with self.assertRaises(ValueError):
            WorkerLiveness(worker_id="w", worker_instance_id="i", worker_epoch=1,
                           state="BOGUS", reported_at=1.0)
        with self.assertRaises(ValueError):
            WorkerLiveness(worker_id="w", worker_instance_id="i", worker_epoch=1,
                           state=WorkerLivenessState.LIVE, reported_at=None)
        with self.assertRaises(ValueError):
            WorkerLiveness(worker_id="w", worker_instance_id="i", worker_epoch=1,
                           state=WorkerLivenessState.LIVE, reported_at=1.0,
                           heartbeat_seq=0)
        with self.assertRaises(ValueError):
            WorkerLiveness(worker_id="w", worker_instance_id="i", worker_epoch=1,
                           state=WorkerLivenessState.LIVE,
                           reported_at=float("nan"))

    def test_09_deterministic_serialization(self):
        self.assertEqual(to_json(identity()), to_json(identity()))
        self.assertEqual(to_json(caps()), to_json(caps()))
        self.assertEqual(to_json(liveness()), to_json(liveness()))
        s = to_json(identity())
        self.assertNotIn(": ", s)
        self.assertNotIn(", ", s)
        self.assertEqual(list(json.loads(s).keys()),
                         sorted(json.loads(s).keys()))

    def test_10_serialization_round_trip(self):
        for obj in (identity(), caps(), liveness(),
                    identity(caps_value=caps()),
                    caps(rc=RC),
                    liveness(state=WorkerLivenessState.STALE, seq=9)):
            d = to_dict(obj)
            restored = from_dict(d, type(obj))
            self.assertEqual(to_dict(restored), d,
                             f"dict round-trip failed for {type(obj).__name__}")
            self.assertEqual(from_json(to_json(obj), type(obj)), obj,
                             f"json round-trip failed for {type(obj).__name__}")

    def test_11_malformed_input_rejection(self):
        with self.assertRaises(ValueError):
            from_dict({"worker_id": "w_1"}, WorkerIdentity)
        with self.assertRaises(ValueError):
            from_dict("not a dict", WorkerIdentity)
        with self.assertRaises(ValueError):
            from_dict({"worker_id": "w_1", "worker_instance_id": "i_1",
                       "worker_epoch": 1, "isolation_mode": "BOGUS"},
                      WorkerIdentity)
        with self.assertRaises(ValueError):
            from_json("not json {", WorkerIdentity)
        with self.assertRaises(ValueError):
            from_dict({"worker_id": "w_1", "worker_instance_id": "i_1",
                       "worker_epoch": 1, "state": "NOT_A_STATE",
                       "reported_at": 1.0}, WorkerLiveness)

    def test_12_json_safety(self):
        for obj in (identity(), caps(), liveness()):
            d = to_dict(obj)
            json.dumps(d)
            self.assertIsInstance(d, dict)

    def test_13_executable_object_rejection(self):
        with self.assertRaises(ValueError):
            WorkerIdentity(worker_id="w", worker_instance_id="i", worker_epoch=1,
                           tenant_scope=[lambda: None])
        with self.assertRaises(ValueError):
            WorkerIdentity(worker_id="w", worker_instance_id="i", worker_epoch=1,
                           capabilities=("not caps",))
        with self.assertRaises(ValueError):
            WorkerCapabilities(tool_classes=[b"rm -rf /"])
        with self.assertRaises(ValueError):
            WorkerLiveness(worker_id="w", worker_instance_id="i", worker_epoch=1,
                           state=WorkerLivenessState.LIVE, reported_at=lambda: 1.0)

    def test_14_secret_safe_serialization(self):
        d = to_dict(identity(caps_value=caps()))
        json.dumps(d)
        flat_keys = list(d.keys())
        if isinstance(d.get("capabilities"), dict):
            flat_keys += list(d["capabilities"].keys())
        flat = " ".join(flat_keys).lower()
        for secret_marker in ("api_key", "secret", "token", "password",
                              "authorization"):
            self.assertNotIn(secret_marker, flat)
        self.assertNotIn("__dict__", json.dumps(d))
        self.assertNotIn(".<locals>", json.dumps(d))

    def test_15_capability_is_not_authorization(self):
        c = caps()
        for forbidden in ("authorized", "allowed_tools", "permissions",
                          "policy", "can_execute", "grants", "is_authorized"):
            self.assertFalse(hasattr(c, forbidden),
                             f"WorkerCapabilities must not expose {forbidden}")
        d = to_dict(c)
        flat = " ".join(d.keys()).lower()
        for marker in ("author", "allow", "permit", "grant"):
            self.assertNotIn(marker, flat)
        with self.assertRaises(AttributeError):
            c.max_cpu_cores = 99

    def test_16_identity_has_no_lease_authority(self):
        i = identity()
        for f in ("lease_owner", "lease_expires_at", "lease_ttl", "lease"):
            self.assertFalse(hasattr(i, f),
                             f"WorkerIdentity must not carry {f}")
        with self.assertRaises(TypeError):
            WorkerIdentity(worker_id="w_1", worker_instance_id="i_1",
                           worker_epoch=1, lease_owner="ee")
        self.assertFalse(hasattr(wc, "WorkerLease"),
                         "no lease contract may be introduced")

    def test_17_identity_has_no_retry_authority(self):
        i = identity()
        for f in ("retry_count", "max_retries", "backoff", "next_retry_at",
                  "retryable"):
            self.assertFalse(hasattr(i, f),
                             f"WorkerIdentity must not carry {f}")
        with self.assertRaises(TypeError):
            WorkerIdentity(worker_id="w_1", worker_instance_id="i_1",
                           worker_epoch=1, max_retries=3)

    def test_18_identity_has_no_task_state_authority(self):
        i = identity()
        for f in ("status", "task_state", "mission_state", "completed",
                  "failed", "state"):
            self.assertFalse(hasattr(i, f),
                             f"WorkerIdentity must not carry task state {f}")
        with self.assertRaises(TypeError):
            WorkerIdentity(worker_id="w_1", worker_instance_id="i_1",
                           worker_epoch=1, status="RUNNING")
        self.assertFalse(hasattr(wc, "TaskState"),
                         "no task-state enum may be introduced")

    def test_19_correlation_identifiers_preserved(self):
        j = RuntimeJob(job_id="exec_1", execution_id="exec_1",
                       mission_id="mission_1", task_id="task_1", attempt_no=1,
                       input={}, metadata={}, timeout_sec=None,
                       correlation_id="corr_1", capabilities=RC)
        d = rc_to_dict(j)
        self.assertEqual(d["job_id"], "exec_1")
        self.assertEqual(d["execution_id"], "exec_1")
        self.assertEqual(d["mission_id"], "mission_1")
        self.assertEqual(d["task_id"], "task_1")
        self.assertEqual(d["attempt_no"], 1)
        self.assertEqual(d["correlation_id"], "corr_1")
        restored = rc_from_dict(d, RuntimeJob)
        self.assertEqual(rc_to_dict(restored), d)
        i = identity()
        for f in ("mission_id", "task_id", "attempt_no", "correlation_id",
                  "job_id", "execution_id"):
            self.assertFalse(hasattr(i, f),
                             f"WorkerIdentity must not redefine {f}")

    def test_20_duplicate_execution_identity_invariant(self):
        j = RuntimeJob(job_id="exec_1", execution_id="exec_1",
                       mission_id="m", task_id="t", attempt_no=1,
                       input={}, metadata={}, timeout_sec=None,
                       correlation_id="c", capabilities=RC)
        r = RuntimeRequest(job=j, requested_at=1.0, requested_by="ee",
                           capabilities_required=None)
        self.assertEqual(r.idempotency_key, "exec_1")
        self.assertEqual(r.idempotency_key, j.execution_id)
        with self.assertRaises(ValueError):
            RuntimeJob(job_id="a", execution_id="b", mission_id="m",
                       task_id="t", attempt_no=1, input={}, metadata={},
                       timeout_sec=None, correlation_id="c")
        i = identity()
        for f in ("execution_id", "job_id", "idempotency_key"):
            self.assertFalse(hasattr(i, f),
                             f"WorkerIdentity must not redefine {f}")

    def test_21_worker_contract_does_not_mutate_runtime_request_semantics(self):
        j = RuntimeJob(job_id="exec_1", execution_id="exec_1",
                       mission_id="m", task_id="t", attempt_no=1,
                       input={}, metadata={}, timeout_sec=None,
                       correlation_id="c", capabilities=RC)
        r1 = RuntimeRequest(job=j, requested_at=1.0, requested_by="ee",
                            capabilities_required=None)
        r2 = RuntimeRequest(job=j, requested_at=2.0, requested_by="ee",
                            capabilities_required=None)
        self.assertTrue(r1.is_duplicate_of(r2))
        self.assertEqual(r1.idempotency_key, r2.idempotency_key)
        c1 = RuntimeCapabilities(transport=RuntimeTransportKind.INPROCESS,
                                 isolation=RuntimeIsolation.NONE,
                                 max_concurrency=1)
        c2 = RuntimeCapabilities(transport=RuntimeTransportKind.INPROCESS,
                                 isolation=RuntimeIsolation.NONE,
                                 max_concurrency=1)
        self.assertEqual(rc_to_dict(c1), rc_to_dict(c2))

    def test_22_backward_compatibility_runtime_contracts(self):
        c1 = RuntimeCapabilities(transport=RuntimeTransportKind.INPROCESS,
                                 isolation=RuntimeIsolation.NONE,
                                 max_concurrency=8, supports_heartbeat=True,
                                 supports_hard_timeout=False,
                                 features=frozenset(
                                     {RuntimeCapability.CANCELLATION}))
        d = rc_to_dict(c1)
        restored = rc_from_dict(d, RuntimeCapabilities)
        self.assertEqual(rc_to_dict(restored), d)
        import agent.runtime_contracts as rcmod
        self.assertIs(RuntimeCapabilities, rcmod.RuntimeCapabilities)
        # liveness-state taxonomy matches gate section 3 exactly
        self.assertEqual({"REGISTERED", "LIVE", "STALE", "DEPARTED"},
                         set(WORKER_LIVENESS_STATE_VALUES))
        self.assertEqual(4, len(WorkerLivenessState))

    def test_23_liveness_distinct_from_ee_lease(self):
        l = liveness()
        for f in ("lease_owner", "lease_expires_at", "lease_ttl"):
            self.assertFalse(hasattr(l, f),
                             f"WorkerLiveness must not carry {f}")
        with self.assertRaises(TypeError):
            WorkerLiveness(worker_id="w", worker_instance_id="i",
                           worker_epoch=1, state=WorkerLivenessState.LIVE,
                           reported_at=1.0, lease_owner="ee")

    def test_24_worker_epoch_staleness_semantics(self):
        with self.assertRaises(ValueError):
            WorkerIdentity(worker_id="w", worker_instance_id="i",
                           worker_epoch=0)
        self.assertNotEqual(identity(epoch=1), identity(epoch=2))
        self.assertNotEqual(identity(instance="w_1_inst_1"),
                            identity(instance="w_1_inst_2"))

    def test_25_tenant_scope_not_overrideable(self):
        i = identity(tenants=("tenant_a",))
        self.assertEqual(i.tenant_scope, ("tenant_a",))
        with self.assertRaises(AttributeError):
            i.tenant_scope = ("tenant_b",)
        self.assertEqual(i.tenant_scope, ("tenant_a",))


if __name__ == "__main__":
    unittest.main(verbosity=2)