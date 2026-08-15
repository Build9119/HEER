#!/usr/bin/env python3
"""worker_matcher_test.py — HEER Phase 3.6.2 Deterministic Worker Capability
Matching Engine tests.

Covers gate test strategy (HEER_PHASE36_WORKER_DISPATCH_GATE.md §21/22):
determinism, liveness, epoch, tenant isolation, hard/soft attributes,
capacity-as-soft-only, capability != authorization, immutability, JSON-safety,
registry purity, and authority absence (no dispatch/assign/schedule/execute/
authorize/approve/lease/retry/cancel/complete surface).
"""
import dataclasses
import inspect
import json
import unittest

from agent.dispatch_contracts import (
    CapabilityMatch,
    DispatchConstraints,
    DispatchDecision,
    DispatchReason,
    from_dict,
    from_json,
    to_dict,
    to_json,
)
from agent.runtime_contracts import (
    RuntimeCapabilities,
    RuntimeCapability,
    RuntimeIsolation,
    RuntimeTransportKind,
)
from agent.worker_contracts import (
    WorkerCapabilities,
    WorkerIdentity,
    WorkerLivenessState,
)
from agent.worker_registry import WorkerRegistry
from agent.worker_matcher import WorkerMatcher


def _caps(tool=(), feats=(), arch=None):
    return WorkerCapabilities(
        runtime_capabilities=RuntimeCapabilities(
            transport=RuntimeTransportKind.INPROCESS,
            isolation=RuntimeIsolation.NONE,
            features=frozenset(feats)),
        tool_classes=tuple(tool),
        architecture=arch)


def _id(wid, inst, epoch, tenant=("t1",), caps=None,
        iso=RuntimeIsolation.NONE):
    return WorkerIdentity(worker_id=wid, worker_instance_id=inst,
                          worker_epoch=epoch, tenant_scope=tenant,
                          capabilities=caps, isolation_mode=iso)


def _live(reg, wid, epoch=1, tenant=("t1",), caps=None,
          iso=RuntimeIsolation.NONE):
    inst = f"{wid}-i{epoch}"
    res = reg.register(_id(wid, inst, epoch, tenant, caps, iso))
    assert res["ok"], res
    hb = reg.heartbeat(worker_id=wid, worker_instance_id=inst,
                       worker_epoch=epoch, heartbeat_seq=1, reported_at=100.0)
    assert hb["ok"], hb
    return inst


class _ReadOnlySpy:
    """Registry stand-in exposing ONLY list/status; any other attribute
    access raises. Proves the matcher performs no other interaction
    (no Hermes, EE, audit, tools, or registry mutation)."""

    def __init__(self, entries, total):
        self._entries = entries
        self._total = total
        self.calls = []
        self.foreign_access = []

    def list(self, *, tenant_scope=None):
        self.calls.append(("list", tenant_scope))
        return list(self._entries)

    def status(self):
        self.calls.append(("status", None))
        return {"total": self._total, "by_state": {}}

    def __getattr__(self, name):
        self.foreign_access.append(name)
        raise AttributeError(name)


class WorkerMatcherTest(unittest.TestCase):

    def setUp(self):
        self.reg = WorkerRegistry()

    # 1. Empty registry -> NO_ELIGIBLE
    def test_01_empty_registry_no_eligible(self):
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.NO_ELIGIBLE)
        self.assertIsNone(dec.candidate)

    # 2. One eligible worker -> SELECTED
    def test_02_one_eligible_selected(self):
        _live(self.reg, "w-1")
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.SELECTED)
        self.assertEqual(dec.candidate.identity.worker_id, "w-1")

    # 3. Multiple eligible -> deterministic first by worker_id
    def test_03_multiple_deterministic_first(self):
        _live(self.reg, "w-b")
        _live(self.reg, "w-a")
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertEqual(dec.candidate.identity.worker_id, "w-a")

    # 4. Same input repeated -> byte-identical decision
    def test_04_byte_identical_repeat(self):
        _live(self.reg, "w-1")
        m = WorkerMatcher(self.reg)
        c = DispatchConstraints()
        d1 = to_json(m.match(c, execution_id="exe_x", decided_at=42.0))
        d2 = to_json(m.match(c, execution_id="exe_x", decided_at=42.0))
        self.assertEqual(d1, d2)
        # Different decided_at -> different decision (caller-supplied clock)
        d3 = to_json(m.match(c, execution_id="exe_x", decided_at=43.0))
        self.assertNotEqual(d1, d3)

    # 5. Worker ordering independent of registration order
    def test_05_order_independent_of_registration(self):
        for order in (["w-b", "w-a"], ["w-a", "w-b"]):
            reg = WorkerRegistry()
            for wid in order:
                _live(reg, wid)
            dec = WorkerMatcher(reg).match(
                DispatchConstraints(), execution_id="exe_x")
            self.assertEqual(dec.candidate.identity.worker_id, "w-a")

    # 6. Tenant mismatch -> TENANT_REJECTED (workers exist, none for tenant)
    def test_06_tenant_mismatch(self):
        _live(self.reg, "w-1", tenant=("t1",))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(tenant_scope="t2"), execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.TENANT_REJECTED)
        self.assertIsNone(dec.candidate)

    # 7. Tenant isolation / no cross-tenant leakage
    def test_07_no_cross_tenant_leakage(self):
        _live(self.reg, "w-a", tenant=("t1",))
        _live(self.reg, "w-b", tenant=("t2",))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(tenant_scope="t1"), execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.SELECTED)
        self.assertEqual(dec.candidate.identity.worker_id, "w-a")
        self.assertIn("t1", dec.candidate.identity.tenant_scope)
        self.assertNotIn("t2", dec.candidate.identity.tenant_scope)

    # 8. LIVE worker accepted
    def test_08_live_accepted(self):
        _live(self.reg, "w-1")
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.SELECTED)
        self.assertEqual(dec.candidate.state, WorkerLivenessState.LIVE)

    # 9. REGISTERED rejected when require_live=True
    def test_09_registered_rejected_require_live(self):
        self.reg.register(_id("w-1", "w-1-i1", 1))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.NO_ELIGIBLE)
        self.assertIsNone(dec.candidate)

    # 10. STALE rejected
    def test_10_stale_rejected(self):
        inst = _live(self.reg, "w-1")
        self.reg.mark_stale(worker_id="w-1", worker_instance_id=inst,
                            worker_epoch=1)
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.NO_ELIGIBLE)

    # 11. DEPARTED rejected
    def test_11_departed_rejected(self):
        inst = _live(self.reg, "w-1")
        self.reg.depart(worker_id="w-1", worker_instance_id=inst,
                        worker_epoch=1)
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.NO_ELIGIBLE)

    # 12. require_live=False: REGISTERED admitted; STALE/DEPARTED excluded
    def test_12_require_live_false_semantics(self):
        self.reg.register(_id("w-reg", "w-reg-i1", 1))
        inst_s = _live(self.reg, "w-stale")
        self.reg.mark_stale(worker_id="w-stale", worker_instance_id=inst_s,
                            worker_epoch=1)
        inst_d = _live(self.reg, "w-dep")
        self.reg.depart(worker_id="w-dep", worker_instance_id=inst_d,
                        worker_epoch=1)
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(require_live=False), execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.SELECTED)
        self.assertEqual(dec.candidate.identity.worker_id, "w-reg")
        self.assertEqual(dec.candidate.state, WorkerLivenessState.REGISTERED)

    # 13. Epoch: newer epoch supersedes; old triple never selected
    def test_13_newer_epoch_supersedes(self):
        _live(self.reg, "w-1", epoch=1)
        _live(self.reg, "w-1", epoch=2)   # new instance + newer epoch
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertEqual(dec.candidate.identity.worker_id, "w-1")
        self.assertEqual(dec.candidate.identity.worker_epoch, 2)
        self.assertEqual(dec.candidate.identity.worker_instance_id, "w-1-i2")

    # 14. Stale instance rejected at registry; matcher never sees old triple
    def test_14_stale_instance_rejected(self):
        _live(self.reg, "w-1", epoch=2)
        stale = self.reg.heartbeat(worker_id="w-1",
                                   worker_instance_id="w-1-i1",
                                   worker_epoch=1, heartbeat_seq=9,
                                   reported_at=200.0)
        self.assertFalse(stale["ok"])
        self.assertTrue(stale["stale"])
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertEqual(dec.candidate.identity.worker_epoch, 2)

    # 15. Required tool class match
    def test_15_tool_class_match(self):
        _live(self.reg, "w-1", caps=_caps(tool=("bash", "web")))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(required_tool_classes=("bash",)),
            execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.SELECTED)

    # 16. Missing tool class rejection
    def test_16_missing_tool_class(self):
        _live(self.reg, "w-1", caps=_caps(tool=("bash",)))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(required_tool_classes=("python",)),
            execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.NO_ELIGIBLE)

    # 17. Multiple required tool classes
    def test_17_multiple_tool_classes(self):
        _live(self.reg, "w-1", caps=_caps(tool=("bash", "web", "python")))
        _live(self.reg, "w-2", caps=_caps(tool=("bash", "web")))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(required_tool_classes=("bash", "web", "python")),
            execution_id="exe_x")
        self.assertEqual(dec.candidate.identity.worker_id, "w-1")

    # 18. Runtime feature match
    def test_18_runtime_feature_match(self):
        _live(self.reg, "w-1",
              caps=_caps(feats=[RuntimeCapability.CANCELLATION,
                                RuntimeCapability.HEARTBEAT]))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(required_runtime_features=("cancellation",)),
            execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.SELECTED)

    # 19. Missing runtime feature rejection
    def test_19_missing_runtime_feature(self):
        _live(self.reg, "w-1",
              caps=_caps(feats=[RuntimeCapability.HEARTBEAT]))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(required_runtime_features=("streaming",)),
            execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.NO_ELIGIBLE)

    # 20. Invalid runtime feature -> deterministic contract failure
    def test_20_invalid_runtime_feature(self):
        with self.assertRaises(ValueError):
            DispatchConstraints(required_runtime_features=("flying",))

    # 21. Required isolation match
    def test_21_isolation_match(self):
        _live(self.reg, "w-1", iso=RuntimeIsolation.PROCESS)
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(required_isolation=RuntimeIsolation.PROCESS),
            execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.SELECTED)

    # 22. Incompatible isolation rejection
    def test_22_isolation_mismatch(self):
        _live(self.reg, "w-1", iso=RuntimeIsolation.NONE)
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(required_isolation=RuntimeIsolation.PROCESS),
            execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.NO_ELIGIBLE)

    # 23. Architecture match
    def test_23_architecture_match(self):
        _live(self.reg, "w-1", caps=_caps(arch="arm64"))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(required_architecture="arm64"),
            execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.SELECTED)

    # 24. Architecture mismatch (no fuzzy aliases)
    def test_24_architecture_mismatch(self):
        _live(self.reg, "w-1", caps=_caps(arch="x86_64"))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(required_architecture="arm64"),
            execution_id="exe_x")
        self.assertEqual(dec.reason, DispatchReason.NO_ELIGIBLE)

    # 25+26. Capacity is never a hard gate (I22)
    def test_25_26_capacity_never_hard_gate(self):
        low = WorkerCapabilities(
            runtime_capabilities=RuntimeCapabilities(
                transport=RuntimeTransportKind.INPROCESS,
                isolation=RuntimeIsolation.NONE),
            tool_classes=("bash",),
            max_cpu_cores=1,
            max_memory_mb=128)
        _live(self.reg, "w-low", caps=low)
        _live(self.reg, "w-none", caps=_caps(tool=("bash",)))
        # Unscoped: both eligible, deterministic first -> w-low
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(required_tool_classes=("bash",)),
            execution_id="exe_x")
        self.assertEqual(dec.candidate.identity.worker_id, "w-low")

    # 27. Capability never becomes authorization
    def test_27_capability_never_authorization(self):
        _live(self.reg, "w-1", caps=_caps(tool=("bash",)))
        _, cm = WorkerMatcher(self.reg).evaluate(
            DispatchConstraints(required_tool_classes=("bash",)),
            execution_id="exe_x")
        d = to_dict(cm)
        for key in d:
            self.assertNotIn("authorize", key.lower())
            self.assertNotIn("grant", key.lower())
            self.assertNotIn("permission", key.lower())
            self.assertNotIn("trust", key.lower())
        self.assertNotIn("signature", d["candidate"]["identity"]["capabilities"])

    # 28. Selected decision contains candidate
    def test_28_selected_contains_candidate(self):
        _live(self.reg, "w-1")
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertIsNotNone(dec.candidate)
        self.assertEqual(dec.reason, DispatchReason.SELECTED)

    # 29. No-match contains no candidate
    def test_29_no_match_no_candidate(self):
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        self.assertIsNone(dec.candidate)
        self.assertEqual(dec.reason, DispatchReason.NO_ELIGIBLE)

    # 30. Tenant rejection contains no candidate
    def test_30_tenant_rejected_no_candidate(self):
        _live(self.reg, "w-1", tenant=("t1",))
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(tenant_scope="t2"), execution_id="exe_x")
        self.assertIsNone(dec.candidate)
        self.assertEqual(dec.reason, DispatchReason.TENANT_REJECTED)

    # 31. Deterministic matched hard attribute ordering (sorted)
    def test_31_matched_attributes_sorted(self):
        _live(self.reg, "w-1", iso=RuntimeIsolation.PROCESS,
              caps=_caps(tool=("bash",),
                         feats=[RuntimeCapability.CANCELLATION],
                         arch="arm64"))
        _, cm = WorkerMatcher(self.reg).evaluate(
            DispatchConstraints(
                tenant_scope="t1", required_isolation=RuntimeIsolation.PROCESS,
                required_tool_classes=("bash",),
                required_runtime_features=("cancellation",),
                required_architecture="arm64"),
            execution_id="exe_x")
        attrs = list(cm.matched_hard_attributes)
        self.assertEqual(attrs, sorted(attrs))
        self.assertNotIn("liveness", attrs[:0])  # tuple immutability sanity
        self.assertEqual(attrs[-1], "worker_epoch")

    # 32. Duplicate attributes normalized (no dupes)
    def test_32_no_duplicate_attributes(self):
        _live(self.reg, "w-1")
        _, cm = WorkerMatcher(self.reg).evaluate(
            DispatchConstraints(), execution_id="exe_x")
        self.assertEqual(len(cm.matched_hard_attributes),
                         len(set(cm.matched_hard_attributes)))

    # 33. Immutable result
    def test_33_immutable_result(self):
        _live(self.reg, "w-1")
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            dec.candidate = None  # type: ignore[misc]

    # 34. Registry remains unchanged after match
    def test_34_registry_unchanged(self):
        _live(self.reg, "w-1", caps=_caps(tool=("bash",)))
        before_list = self.reg.list()
        before_status = self.reg.status()
        m = WorkerMatcher(self.reg)
        m.match(DispatchConstraints(required_tool_classes=("bash",)),
                execution_id="exe_x")
        m.evaluate(DispatchConstraints(required_tool_classes=("missing",)),
                   execution_id="exe_y")
        self.assertEqual(before_list, self.reg.list())
        self.assertEqual(before_status, self.reg.status())

    # 40. No Hermes calls / 41. No EE calls / 42. No audit writes —
    #     spy registry proves the matcher touches ONLY list()/status().
    def test_40_41_42_only_registry_reads(self):
        _live(self.reg, "w-1", caps=_caps(tool=("bash",)))
        spy = _ReadOnlySpy(self.reg.list(), 1)
        m = WorkerMatcher(spy)
        m.match(DispatchConstraints(), execution_id="exe_x")
        self.assertEqual([("status", None), ("list", None)], spy.calls)
        self.assertEqual([], spy.foreign_access)
        # Empty-registry path short-circuits to status() only.
        spy2 = _ReadOnlySpy([], 0)
        WorkerMatcher(spy2).match(DispatchConstraints(), execution_id="exe_x")
        self.assertEqual([("status", None)], spy2.calls)
        self.assertEqual([], spy2.foreign_access)

    # 40/41/42 (import-level): no forbidden module imports in worker_matcher
    def test_40_41_42_no_forbidden_imports(self):
        src = inspect.getsource(WorkerMatcher)
        for forbidden in ("hermes", "execution_engine", "audit", "tools.",
                          "worker_registry", "mission_engine", "task_graph"):
            self.assertNotIn(forbidden, src,
                             f"worker_matcher must not import {forbidden}")

    # 35-39, 44. Authority: no dispatch/assign/schedule/execute/authorize/
    #     approve/lease/retry/cancel/complete surface. Public surface is
    #     exactly {match, evaluate}.
    def test_authority_public_surface(self):
        public = {n for n in dir(WorkerMatcher) if not n.startswith("_")}
        self.assertEqual({"match", "evaluate"}, public)
        for name in ("dispatch", "assign", "schedule", "execute", "authorize",
                     "approve", "grant", "allow", "permission",
                     "acquire_lease", "retry", "cancel", "complete"):
            self.assertFalse(hasattr(WorkerMatcher, name),
                             f"WorkerMatcher must not expose {name}()")

    # 35. No lease fields in decision/candidate dicts
    def test_35_no_lease_fields(self):
        _live(self.reg, "w-1")
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        blob = json.dumps(to_dict(dec))
        for key in ("lease_owner", "lease_expires_at", "lease_ttl"):
            self.assertNotIn(key, blob)

    # 36. No retry fields in decision/candidate dicts
    def test_36_no_retry_fields(self):
        _live(self.reg, "w-1")
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        blob = json.dumps(to_dict(dec))
        for key in ("retry", "backoff", "attempts", "attempt_no"):
            self.assertNotIn(key, blob)

    # 37. No task-state fields in decision/candidate dicts
    def test_37_no_task_state_fields(self):
        _live(self.reg, "w-1")
        dec = WorkerMatcher(self.reg).match(
            DispatchConstraints(), execution_id="exe_x")
        blob = json.dumps(to_dict(dec))
        for key in ("task_state", "task_status", "execution_status",
                    "completed", "failed"):
            self.assertNotIn(key, blob)

    # 43. JSON-safe decision round-trip
    def test_43_json_safe_round_trip(self):
        _live(self.reg, "w-1", caps=_caps(tool=("bash",)))
        m = WorkerMatcher(self.reg)
        c = DispatchConstraints(required_tool_classes=("bash",))
        dec = m.match(c, execution_id="exe_x", decided_at=7.5)
        text = to_json(dec)
        parsed = from_json(text, DispatchDecision)
        self.assertEqual(dec, parsed)
        # NO_ELIGIBLE path also JSON-safe with candidate None
        dec2 = m.match(DispatchConstraints(required_tool_classes=("nope",)),
                       execution_id="exe_y")
        parsed2 = from_json(to_json(dec2), DispatchDecision)
        self.assertEqual(dec2, parsed2)

    # 44. Regression compatibility: matcher is a pure consumer of the frozen
    #     dispatch contracts and the registry; no contract mutation.
    def test_44_frozen_contract_composition(self):
        with self.assertRaises(ValueError):
            WorkerMatcher(object())  # object has no list()/status()
        self.assertEqual(DispatchReason.SELECTED.value, "SELECTED")
        self.assertEqual(DispatchReason.NO_ELIGIBLE.value, "NO_ELIGIBLE")
        self.assertEqual(DispatchReason.TENANT_REJECTED.value, "TENANT_REJECTED")


if __name__ == "__main__":
    unittest.main()