#!/usr/bin/env python3
"""worker_registry_test.py — Phase 3.5.2 Worker Registry & Lifecycle tests.

Deterministic, stdlib-only, no network / no SQLite / no real tools / no sleeps.
Covers the full registration collision matrix, heartbeat semantics, stale
detection, departure, capability discovery (descriptive only), tenant
isolation, concurrent operations, authority boundaries (I1–I8, I10, I11),
deterministic queries, and JSON-safe serialization.

Run:  python3 tests/worker_registry_test.py
"""
import json
import threading
import unittest
from typing import Any, cast

from agent.runtime_contracts import (
    RuntimeCapabilities,
    RuntimeCapability,
    RuntimeIsolation,
    RuntimeTransportKind,
)
from agent.worker_contracts import WorkerCapabilities, WorkerIdentity, WorkerLivenessState
from agent.worker_registry import WorkerRegistry


def _caps(tool_classes=("bash", "file"), features=()):
    rc = RuntimeCapabilities(
        transport=RuntimeTransportKind.INPROCESS,
        isolation=RuntimeIsolation.PROCESS,
        max_concurrency=4,
        supports_heartbeat=True,
        supports_hard_timeout=True,
        supports_secrets=False,
        supports_tenant_isolation=True,
        features=frozenset(features),
    )
    return WorkerCapabilities(
        runtime_capabilities=rc,
        tool_classes=tool_classes,
        max_cpu_cores=4,
        architecture="arm64",
        network_policy="allow",
        region="in",
        compliance_boundary="default",
        runtime_version="1.0.0",
    )


def _identity(worker_id="w-1", instance="i-1", epoch=1, tenant=("t1",),
              caps=None, isolation=RuntimeIsolation.PROCESS, transport="rt-1"):
    return WorkerIdentity(
        worker_id=worker_id,
        worker_instance_id=instance,
        worker_epoch=epoch,
        tenant_scope=tenant,
        capabilities=caps,
        isolation_mode=isolation,
        transport_identity=transport,
    )


def _entry(reg, wid="w-1"):
    """Registry query result with Optional narrowed (worker is always present
    in these tests; the registry itself returns None only when absent)."""
    entry = reg.get(wid)
    assert entry is not None
    return entry


def _caps_of(reg, wid="w-1"):
    """Capabilities block with Optional narrowed (helpers always supply caps)."""
    caps = _entry(reg, wid)["identity"]["capabilities"]
    assert caps is not None
    return caps


class WorkerRegistryTest(unittest.TestCase):
    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def test_01_first_registration(self):
        reg = WorkerRegistry()
        r = reg.register(_identity())
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], WorkerLivenessState.REGISTERED.value)
        self.assertFalse(r["duplicate"])
        entry = _entry(reg)
        self.assertEqual(entry["state"], WorkerLivenessState.REGISTERED.value)
        self.assertEqual(entry["heartbeat_seq"], 0)

    def test_02_duplicate_registration_idempotent(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        r = reg.register(_identity())
        self.assertTrue(r["ok"])
        self.assertTrue(r["duplicate"])
        self.assertEqual(reg.status()["total"], 1)

    def test_03_identity_preserved(self):
        reg = WorkerRegistry()
        reg.register(_identity(caps=_caps()))
        ident = _entry(reg)["identity"]
        self.assertEqual(ident["worker_id"], "w-1")
        self.assertEqual(ident["worker_instance_id"], "i-1")
        self.assertEqual(ident["worker_epoch"], 1)
        self.assertEqual(ident["tenant_scope"], ["t1"])
        self.assertEqual(ident["isolation_mode"], RuntimeIsolation.PROCESS.value)
        self.assertEqual(ident["transport_identity"], "rt-1")
        self.assertEqual(_caps_of(reg)["tool_classes"], ["bash", "file"])

    def test_04_instance_identity_preserved(self):
        reg = WorkerRegistry()
        reg.register(_identity(instance="i-9"))
        self.assertEqual(_entry(reg)["identity"]["worker_instance_id"], "i-9")

    def test_05_epoch_preserved(self):
        reg = WorkerRegistry()
        reg.register(_identity(epoch=7))
        self.assertEqual(_entry(reg)["identity"]["worker_epoch"], 7)

    def test_06_older_epoch_rejected(self):
        reg = WorkerRegistry()
        reg.register(_identity(epoch=2))
        r = reg.register(_identity(epoch=1))
        self.assertFalse(r["ok"])
        self.assertTrue(r.get("stale"))
        self.assertEqual(_entry(reg)["identity"]["worker_epoch"], 2)

    def test_07_newer_epoch_supersedes(self):
        reg = WorkerRegistry()
        reg.register(_identity(instance="i-1", epoch=1))
        r = reg.register(_identity(instance="i-2", epoch=2))
        self.assertTrue(r["ok"])
        self.assertTrue(r.get("superseded"))
        entry = _entry(reg)
        self.assertEqual(entry["identity"]["worker_instance_id"], "i-2")
        self.assertEqual(entry["identity"]["worker_epoch"], 2)
        self.assertEqual(entry["heartbeat_seq"], 0)  # sequence reset on supersede

    def test_08_new_instance_same_epoch_rejected(self):
        reg = WorkerRegistry()
        reg.register(_identity(instance="i-1", epoch=1))
        r = reg.register(_identity(instance="i-2", epoch=1))
        self.assertFalse(r["ok"])
        self.assertIn("epoch", r["error"])

    def test_09_register_non_identity_rejected(self):
        # Defensive runtime check: a caller that violates the typed contract
        # must be rejected, not crash or corrupt registry state.
        reg = WorkerRegistry()
        r = reg.register(cast(Any, "not-an-identity"))
        self.assertFalse(r["ok"])

    def test_10_tenant_scope_preserved(self):
        reg = WorkerRegistry()
        reg.register(_identity(tenant=("t1", "t2")))
        self.assertEqual(_entry(reg)["identity"]["tenant_scope"], ["t1", "t2"])

    def test_11_capabilities_preserved(self):
        reg = WorkerRegistry()
        reg.register(_identity(caps=_caps()))
        caps = _caps_of(reg)
        self.assertEqual(caps["tool_classes"], ["bash", "file"])
        self.assertEqual(caps["max_cpu_cores"], 4)
        self.assertEqual(caps["architecture"], "arm64")
        self.assertEqual(caps["region"], "in")
        self.assertEqual(caps["runtime_version"], "1.0.0")

    def test_12_isolation_mode_preserved(self):
        reg = WorkerRegistry()
        reg.register(_identity(isolation=RuntimeIsolation.CONTAINER))
        self.assertEqual(
            _entry(reg)["identity"]["isolation_mode"],
            RuntimeIsolation.CONTAINER.value,
        )

    def test_13_capabilities_mutable_at_registration(self):
        # Gate §3: capabilities are mutable at registration (deployment).
        reg = WorkerRegistry()
        reg.register(_identity(caps=_caps(tool_classes=("bash",))))
        reg.register(_identity(caps=_caps(tool_classes=("bash", "python"))))
        self.assertEqual(_caps_of(reg)["tool_classes"], ["bash", "python"])

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    def test_14_heartbeat_promotes_to_live(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        r = reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                          worker_epoch=1, heartbeat_seq=1, reported_at=1.0)
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], WorkerLivenessState.LIVE.value)
        self.assertEqual(_entry(reg)["state"], WorkerLivenessState.LIVE.value)
        self.assertEqual(_entry(reg)["heartbeat_seq"], 1)

    def test_15_heartbeat_sequence_monotonic(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        for seq in (1, 2, 3):
            r = reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                              worker_epoch=1, heartbeat_seq=seq, reported_at=float(seq))
            self.assertTrue(r["ok"])
            self.assertEqual(r["seq"], seq)
        self.assertEqual(_entry(reg)["heartbeat_seq"], 3)

    def test_16_duplicate_heartbeat_idempotent(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                      worker_epoch=1, heartbeat_seq=2, reported_at=2.0)
        r = reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                          worker_epoch=1, heartbeat_seq=2, reported_at=2.0)
        self.assertTrue(r["ok"])
        self.assertTrue(r["duplicate"])
        self.assertEqual(_entry(reg)["heartbeat_seq"], 2)

    def test_17_sequence_regression_rejected(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                      worker_epoch=1, heartbeat_seq=3, reported_at=3.0)
        r = reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                          worker_epoch=1, heartbeat_seq=2, reported_at=2.0)
        self.assertFalse(r["ok"])
        self.assertEqual(r["current_seq"], 3)

    def test_18_stale_epoch_heartbeat_rejected(self):
        reg = WorkerRegistry()
        reg.register(_identity(epoch=2))
        r = reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                          worker_epoch=1, heartbeat_seq=1, reported_at=1.0)
        self.assertFalse(r["ok"])
        self.assertTrue(r.get("stale"))

    def test_19_stale_instance_heartbeat_rejected(self):
        reg = WorkerRegistry()
        reg.register(_identity(instance="i-1"))
        r = reg.heartbeat(worker_id="w-1", worker_instance_id="i-2",
                          worker_epoch=1, heartbeat_seq=1, reported_at=1.0)
        self.assertFalse(r["ok"])
        self.assertTrue(r.get("stale"))

    def test_20_heartbeat_unregistered_rejected(self):
        reg = WorkerRegistry()
        r = reg.heartbeat(worker_id="w-99", worker_instance_id="i-1",
                          worker_epoch=1, heartbeat_seq=1, reported_at=1.0)
        self.assertFalse(r["ok"])

    def test_21_heartbeat_invalid_contract_rejected(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        r = reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                          worker_epoch=1, heartbeat_seq=1,
                          reported_at=float("nan"))
        self.assertFalse(r["ok"])
        self.assertIn("invalid heartbeat", r["error"])

    def test_22_heartbeat_after_depart_rejected(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        reg.depart(worker_id="w-1", worker_instance_id="i-1", worker_epoch=1)
        r = reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                          worker_epoch=1, heartbeat_seq=1, reported_at=1.0)
        self.assertFalse(r["ok"])
        self.assertIn("departed", r["error"])

    def test_23_heartbeat_revives_stale(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                      worker_epoch=1, heartbeat_seq=1, reported_at=1.0)
        reg.mark_stale(worker_id="w-1", worker_instance_id="i-1", worker_epoch=1)
        self.assertEqual(_entry(reg)["state"], WorkerLivenessState.STALE.value)
        r = reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                          worker_epoch=1, heartbeat_seq=2, reported_at=2.0)
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], WorkerLivenessState.LIVE.value)

    # ------------------------------------------------------------------
    # Stale detection / departure
    # ------------------------------------------------------------------

    def test_24_mark_stale(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                      worker_epoch=1, heartbeat_seq=1, reported_at=1.0)
        r = reg.mark_stale(worker_id="w-1", worker_instance_id="i-1", worker_epoch=1)
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], WorkerLivenessState.STALE.value)
        self.assertEqual(_entry(reg)["state"], WorkerLivenessState.STALE.value)

    def test_25_mark_stale_idempotent(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        reg.mark_stale(worker_id="w-1", worker_instance_id="i-1", worker_epoch=1)
        r = reg.mark_stale(worker_id="w-1", worker_instance_id="i-1", worker_epoch=1)
        self.assertTrue(r["ok"])
        self.assertTrue(r["duplicate"])

    def test_26_mark_stale_stale_instance_rejected(self):
        reg = WorkerRegistry()
        reg.register(_identity(instance="i-1"))
        r = reg.mark_stale(worker_id="w-1", worker_instance_id="i-2", worker_epoch=1)
        self.assertFalse(r["ok"])

    def test_27_depart(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        r = reg.depart(worker_id="w-1", worker_instance_id="i-1", worker_epoch=1)
        self.assertTrue(r["ok"])
        self.assertEqual(r["state"], WorkerLivenessState.DEPARTED.value)
        self.assertEqual(_entry(reg)["state"], WorkerLivenessState.DEPARTED.value)

    def test_28_depart_idempotent(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        reg.depart(worker_id="w-1", worker_instance_id="i-1", worker_epoch=1)
        r = reg.depart(worker_id="w-1", worker_instance_id="i-1", worker_epoch=1)
        self.assertTrue(r["ok"])
        self.assertTrue(r["duplicate"])

    def test_29_departed_not_revived_by_old_heartbeat(self):
        reg = WorkerRegistry()
        reg.register(_identity())
        reg.depart(worker_id="w-1", worker_instance_id="i-1", worker_epoch=1)
        r = reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                          worker_epoch=1, heartbeat_seq=1, reported_at=1.0)
        self.assertFalse(r["ok"])
        self.assertEqual(_entry(reg)["state"], WorkerLivenessState.DEPARTED.value)

    def test_30_new_instance_after_depart_registers(self):
        # A NEW instance with a NEWER epoch may register fresh (gate §3/§6).
        reg = WorkerRegistry()
        reg.register(_identity(instance="i-1", epoch=1))
        reg.depart(worker_id="w-1", worker_instance_id="i-1", worker_epoch=1)
        r = reg.register(_identity(instance="i-2", epoch=2))
        self.assertTrue(r["ok"])
        self.assertEqual(_entry(reg)["identity"]["worker_epoch"], 2)
        self.assertEqual(_entry(reg)["state"], WorkerLivenessState.REGISTERED.value)

    # ------------------------------------------------------------------
    # Capability discovery (descriptive only — never authorization)
    # ------------------------------------------------------------------

    def test_31_list_by_capability_tool_class(self):
        reg = WorkerRegistry()
        reg.register(_identity(worker_id="w-1", caps=_caps(tool_classes=("bash", "file"))))
        reg.register(_identity(worker_id="w-2", caps=_caps(tool_classes=("python",))))
        found = reg.list_by_capability("bash")
        self.assertEqual([f["identity"]["worker_id"] for f in found], ["w-1"])

    def test_32_list_by_capability_runtime_feature(self):
        reg = WorkerRegistry()
        reg.register(_identity(worker_id="w-1",
                               caps=_caps(features=(RuntimeCapability.HEARTBEAT,))))
        found = reg.list_by_capability(RuntimeCapability.HEARTBEAT.value)
        self.assertEqual([f["identity"]["worker_id"] for f in found], ["w-1"])

    def test_33_capability_no_match(self):
        reg = WorkerRegistry()
        reg.register(_identity(caps=_caps(tool_classes=("bash",))))
        self.assertEqual(reg.list_by_capability("gpu"), [])

    def test_34_capability_is_not_authorization(self):
        # I10: capability is descriptive. The registry grants nothing.
        reg = WorkerRegistry()
        reg.register(_identity(caps=_caps(tool_classes=("bash",))))
        self.assertFalse(hasattr(reg, "authorize"))
        self.assertFalse(hasattr(reg, "grant"))
        found = reg.list_by_capability("bash")
        self.assertEqual(len(found), 1)
        for key in ("authorized", "permission", "allowed", "policy"):
            self.assertNotIn(key, found[0])

    def test_35_capability_tenant_scoped(self):
        reg = WorkerRegistry()
        reg.register(_identity(worker_id="w-1", tenant=("t1",),
                               caps=_caps(tool_classes=("bash",))))
        reg.register(_identity(worker_id="w-2", tenant=("t2",),
                               caps=_caps(tool_classes=("bash",))))
        found = reg.list_by_capability("bash", tenant_scope="t1")
        self.assertEqual([f["identity"]["worker_id"] for f in found], ["w-1"])

    # ------------------------------------------------------------------
    # Tenant isolation
    # ------------------------------------------------------------------

    def test_36_list_tenant_scoped(self):
        reg = WorkerRegistry()
        reg.register(_identity(worker_id="w-1", tenant=("t1",)))
        reg.register(_identity(worker_id="w-2", tenant=("t2",)))
        reg.register(_identity(worker_id="w-3", tenant=("t1", "t2")))
        self.assertEqual(
            [e["identity"]["worker_id"] for e in reg.list(tenant_scope="t1")],
            ["w-1", "w-3"],
        )
        self.assertEqual(
            [e["identity"]["worker_id"] for e in reg.list(tenant_scope="t2")],
            ["w-2", "w-3"],
        )

    def test_37_get_tenant_scoped(self):
        reg = WorkerRegistry()
        reg.register(_identity(worker_id="w-1", tenant=("t1",)))
        self.assertIsNone(reg.get("w-1", tenant_scope="t2"))
        self.assertIsNotNone(reg.get("w-1", tenant_scope="t1"))

    def test_38_identity_cannot_override_tenant_scope(self):
        # I5: worker identity cannot override tenant isolation.
        reg = WorkerRegistry()
        reg.register(_identity(worker_id="w-1", tenant=("t1",)))
        # A t2-scoped query never sees the t1-only worker, regardless of
        # what the worker's identity claims.
        self.assertEqual(reg.list(tenant_scope="t2"), [])
        self.assertIsNone(reg.get("w-1", tenant_scope="t2"))

    # ------------------------------------------------------------------
    # Concurrency
    # ------------------------------------------------------------------

    def test_39_concurrent_registrations(self):
        reg = WorkerRegistry()
        n = 8
        barrier = threading.Barrier(n)
        results = []

        def worker(i):
            barrier.wait()
            results.append(reg.register(
                _identity(worker_id=f"w-{i}", instance=f"i-{i}", epoch=1)))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertTrue(all(r["ok"] for r in results))
        self.assertEqual(reg.status()["total"], n)

    def test_40_concurrent_heartbeats(self):
        # The registry serializes mutations under one RLock. Out-of-order seqs
        # are legitimately rejected (see test_17); the deterministic invariants
        # here are: no crash/corruption, the HIGHEST seq always gets applied
        # (nothing higher can precede it), and the final state is LIVE.
        reg = WorkerRegistry()
        reg.register(_identity())
        n = 8
        barrier = threading.Barrier(n)
        results = []

        def beat(i):
            barrier.wait()
            results.append(reg.heartbeat(
                worker_id="w-1", worker_instance_id="i-1", worker_epoch=1,
                heartbeat_seq=i + 1, reported_at=float(i + 1)))

        threads = [threading.Thread(target=beat, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertTrue(any(r["ok"] for r in results))
        self.assertEqual(_entry(reg)["heartbeat_seq"], n)
        self.assertEqual(_entry(reg)["state"], WorkerLivenessState.LIVE.value)

    # ------------------------------------------------------------------
    # Authority boundaries (I1–I8, I11)
    # ------------------------------------------------------------------

    def test_41_no_ee_lease_fields(self):
        # I4/I11: worker liveness is NOT an EE lease; no lease fields.
        reg = WorkerRegistry()
        reg.register(_identity())
        entry = _entry(reg)
        for key in ("lease_owner", "lease_expires_at", "lease_ttl",
                    "lease_expired", "lease"):
            self.assertNotIn(key, entry)
            self.assertNotIn(key, entry["identity"])

    def test_42_no_retry_authority(self):
        # I3: registry has no retry authority.
        reg = WorkerRegistry()
        reg.register(_identity())
        entry = _entry(reg)
        for key in ("retry_count", "max_attempts", "backoff", "attempt_no",
                    "retry", "backoff_base"):
            self.assertNotIn(key, entry)
        for method in ("retry", "schedule_retry", "backoff"):
            self.assertFalse(hasattr(reg, method))

    def test_43_no_task_state_authority(self):
        # I2: registry has no task/mission/execution state authority.
        reg = WorkerRegistry()
        reg.register(_identity())
        entry = _entry(reg)
        for key in ("task_id", "mission_id", "execution_id", "task_status",
                    "attempt", "execution"):
            self.assertNotIn(key, entry)
        for method in ("transition_task", "start_mission", "cancel_task",
                       "claim_execution", "finalize"):
            self.assertFalse(hasattr(reg, method))

    def test_44_no_scheduling(self):
        # I11: registry is not a scheduler.
        reg = WorkerRegistry()
        for method in ("dispatch", "assign", "schedule", "select_worker",
                       "place", "enqueue"):
            self.assertFalse(hasattr(reg, method))

    # ------------------------------------------------------------------
    # Determinism / serialization
    # ------------------------------------------------------------------

    def test_45_deterministic_list_order(self):
        reg = WorkerRegistry()
        for wid in ("w-3", "w-1", "w-2"):
            reg.register(_identity(worker_id=wid, instance=f"i-{wid}"))
        self.assertEqual(
            [e["identity"]["worker_id"] for e in reg.list()],
            ["w-1", "w-2", "w-3"],
        )

    def test_46_deterministic_status(self):
        reg = WorkerRegistry()
        reg.register(_identity(worker_id="w-1"))
        reg.register(_identity(worker_id="w-2", instance="i-2"))
        reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                      worker_epoch=1, heartbeat_seq=1, reported_at=1.0)
        reg.depart(worker_id="w-2", worker_instance_id="i-2", worker_epoch=1)
        st = reg.status()
        self.assertEqual(st["total"], 2)
        self.assertEqual(st["by_state"][WorkerLivenessState.LIVE.value], 1)
        self.assertEqual(st["by_state"][WorkerLivenessState.DEPARTED.value], 1)

    def test_47_empty_registry(self):
        reg = WorkerRegistry()
        self.assertEqual(reg.list(), [])
        self.assertEqual(reg.status()["total"], 0)
        self.assertIsNone(reg.get("w-1"))

    def test_48_entry_dict_json_safe(self):
        reg = WorkerRegistry()
        reg.register(_identity(caps=_caps()))
        reg.heartbeat(worker_id="w-1", worker_instance_id="i-1",
                      worker_epoch=1, heartbeat_seq=1, reported_at=1.0)
        text = json.dumps(_entry(reg))
        self.assertIn("worker_id", text)
        self.assertIn("heartbeat_seq", text)


if __name__ == "__main__":
    unittest.main()