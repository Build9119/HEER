#!/usr/bin/env python3
"""Unit tests for HEER Worker Dispatch & Capability Matching Contracts
(Phase 3.6.1).

Coverage: all 22 gate test areas (HEER_PHASE36_WORKER_DISPATCH_GATE.md §21)
that are representable at the CONTRACT layer, plus authority-structure /
serialization / determinism / JSON-safety assertions. Contract layer only:
no selection logic exists here — this module tests the immutable shapes,
validation discipline, and authority boundaries.

Run from repo root:  python3 tests/dispatch_contracts_test.py
Deterministic: no sleeps, network, SQLite, server, threads, or real tools.
"""
import os, sys, unittest, json
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path: sys.path.insert(0, _BASE)
from agent import dispatch_contracts as dc
from agent.runtime_contracts import (
    RuntimeCapabilities, RuntimeTransportKind, RuntimeIsolation,
    RuntimeCapability,
)
from agent.worker_contracts import (
    WorkerLivenessState, WorkerIdentity, WorkerCapabilities, WorkerLiveness,
)
from agent.dispatch_contracts import (
    DispatchOrdering, DispatchReason,
    WorkerCandidate, CapabilityMatch, DispatchDecision,
    DispatchConstraints, DispatchPolicy,
    DISPATCH_ORDERING_VALUES, DISPATCH_REASON_VALUES,
    to_dict, from_dict, to_json, from_json,
)

RC = RuntimeCapabilities(transport=RuntimeTransportKind.INPROCESS,
                         isolation=RuntimeIsolation.NONE, max_concurrency=4,
                         supports_heartbeat=True, supports_hard_timeout=False,
                         features=frozenset({RuntimeCapability.CANCELLATION}))


def caps(tool_classes=None, arch=None, rc=None):
    return WorkerCapabilities(
        runtime_capabilities=rc if rc is not None else RC,
        tool_classes=("bash", "file") if tool_classes is None else tool_classes,
        max_cpu_cores=4, max_memory_mb=2048, architecture=arch,
        network_policy="restricted", region="us-west", compliance_boundary="none",
        runtime_version="1.0.0")


def identity(worker="w_1", instance="w_1_inst_1", epoch=1, tenants=None,
             caps_value=None, isolation=RuntimeIsolation.NONE, transport="rt_1"):
    return WorkerIdentity(
        worker_id=worker, worker_instance_id=instance, worker_epoch=epoch,
        tenant_scope=("tenant_a",) if tenants is None else tenants,
        capabilities=caps_value, isolation_mode=isolation,
        transport_identity=transport)


def candidate(worker="w_1", instance="w_1_inst_1", epoch=1, tenants=None,
              caps_value=None, state=WorkerLivenessState.LIVE,
              isolation=RuntimeIsolation.NONE, transport="rt_1",
              registered_at=100.0, reported_at=110.0, seq=2):
    return WorkerCandidate(
        identity=identity(worker=worker, instance=instance, epoch=epoch,
                          tenants=tenants, caps_value=caps_value,
                          isolation=isolation, transport=transport),
        state=state, registered_at=registered_at,
        reported_at=reported_at, heartbeat_seq=seq)


def match(cand=None, execution="exec_1", hard=None, soft=None, at=120.0):
    return CapabilityMatch(
        candidate=cand if cand is not None else candidate(),
        execution_id=execution,
        matched_hard_attributes=hard, matched_soft_attributes=soft,
        matched_at=at)


def decision(cand=None, execution="exec_1", reason=DispatchReason.SELECTED,
             at=130.0):
    if reason is DispatchReason.SELECTED and cand is None:
        cand = candidate()
    return DispatchDecision(
        execution_id=execution, candidate=cand, reason=reason, decided_at=at)


def constraints(**kw):
    return DispatchConstraints(**kw)


class DispatchContractsTest(unittest.TestCase):

    # ------------------------------------------------------------------
    # Gate §20 — contract shapes
    # ------------------------------------------------------------------

    def test_01_worker_candidate_snapshot_shape(self):
        c = candidate()
        self.assertEqual(c.identity.worker_id, "w_1")
        self.assertEqual(c.identity.worker_instance_id, "w_1_inst_1")
        self.assertEqual(c.identity.worker_epoch, 1)
        self.assertEqual(c.state, WorkerLivenessState.LIVE)
        self.assertEqual(c.registered_at, 100.0)
        self.assertEqual(c.reported_at, 110.0)
        self.assertEqual(c.heartbeat_seq, 2)
        self.assertEqual(c.identity.tenant_scope, ("tenant_a",))
        self.assertEqual(c.identity.transport_identity, "rt_1")

    def test_02_capability_match_shape(self):
        m = match(hard=("tool_classes",), soft=("region",))
        self.assertEqual(m.execution_id, "exec_1")
        self.assertEqual(m.candidate.identity.worker_id, "w_1")
        self.assertEqual(m.matched_hard_attributes, ("tool_classes",))
        self.assertEqual(m.matched_soft_attributes, ("region",))
        self.assertEqual(m.matched_at, 120.0)

    def test_03_dispatch_decision_shapes(self):
        d = decision(reason=DispatchReason.NO_ELIGIBLE)
        self.assertIsNone(d.candidate)
        self.assertEqual(d.reason, DispatchReason.NO_ELIGIBLE)
        self.assertEqual(d.execution_id, "exec_1")
        d2 = decision()
        self.assertIsNotNone(d2.candidate)
        self.assertEqual(d2.reason, DispatchReason.SELECTED)
        self.assertEqual(d2.candidate.identity.worker_id, "w_1")
        d3 = decision(reason=DispatchReason.TENANT_REJECTED)
        self.assertIsNone(d3.candidate)

    def test_04_dispatch_constraints_shape(self):
        con = constraints(tenant_scope="tenant_a", require_live=True,
                          required_isolation=RuntimeIsolation.NONE,
                          required_tool_classes=("bash",),
                          required_runtime_features=("cancellation",),
                          required_architecture="arm64")
        self.assertEqual(con.tenant_scope, "tenant_a")
        self.assertTrue(con.require_live)
        self.assertEqual(con.required_isolation, RuntimeIsolation.NONE)
        self.assertEqual(con.required_tool_classes, ("bash",))
        self.assertEqual(con.required_runtime_features, ("cancellation",))
        self.assertEqual(con.required_architecture, "arm64")
        self.assertEqual(con.ordering,
                         DispatchOrdering.DETERMINISTIC_FIRST_ELIGIBLE)

    def test_05_dispatch_policy_shape(self):
        p = DispatchPolicy(policy_id="pol_1", description="first eligible")
        self.assertEqual(p.policy_id, "pol_1")
        self.assertEqual(p.ordering,
                         DispatchOrdering.DETERMINISTIC_FIRST_ELIGIBLE)
        self.assertEqual(p.description, "first eligible")

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_06_all_contracts_immutable(self):
        for obj in (candidate(), match(), decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1")):
            with self.assertRaises(AttributeError):
                if isinstance(obj, WorkerCandidate):
                    obj.state = WorkerLivenessState.STALE
                elif isinstance(obj, CapabilityMatch):
                    obj.execution_id = "exec_2"
                elif isinstance(obj, DispatchDecision):
                    obj.candidate = None
                elif isinstance(obj, DispatchConstraints):
                    obj.tenant_scope = "tenant_b"
                else:
                    obj.policy_id = "pol_2"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_07_worker_candidate_validation(self):
        with self.assertRaises(ValueError):
            WorkerCandidate(identity="not identity", state=WorkerLivenessState.LIVE,
                            registered_at=1.0)
        with self.assertRaises(ValueError):
            WorkerCandidate(identity=identity(), state="BOGUS", registered_at=1.0)
        with self.assertRaises(ValueError):
            WorkerCandidate(identity=identity(), state=WorkerLivenessState.LIVE,
                            registered_at=None)
        with self.assertRaises(ValueError):
            WorkerCandidate(identity=identity(), state=WorkerLivenessState.LIVE,
                            registered_at=1.0, reported_at=float("nan"))
        with self.assertRaises(ValueError):
            WorkerCandidate(identity=identity(), state=WorkerLivenessState.LIVE,
                            registered_at=1.0, heartbeat_seq=-1)
        with self.assertRaises(ValueError):
            WorkerCandidate(identity=identity(), state=WorkerLivenessState.LIVE,
                            registered_at=1.0, heartbeat_seq=True)

    def test_08_capability_match_validation(self):
        with self.assertRaises(ValueError):
            CapabilityMatch(candidate=candidate(), execution_id="")
        with self.assertRaises(ValueError):
            CapabilityMatch(candidate=candidate(), execution_id="exec_1",
                            matched_hard_attributes="bash")
        with self.assertRaises(ValueError):
            CapabilityMatch(candidate=candidate(), execution_id="exec_1",
                            matched_at=None)
        with self.assertRaises(ValueError):
            CapabilityMatch(candidate="not candidate", execution_id="exec_1")

    def test_09_dispatch_decision_validation(self):
        # SELECTED requires a candidate
        with self.assertRaises(ValueError):
            DispatchDecision(execution_id="exec_1", candidate=None,
                             reason=DispatchReason.SELECTED)
        # NO_ELIGIBLE / TENANT_REJECTED must NOT carry a candidate
        with self.assertRaises(ValueError):
            DispatchDecision(execution_id="exec_1", candidate=candidate(),
                             reason=DispatchReason.NO_ELIGIBLE)
        with self.assertRaises(ValueError):
            DispatchDecision(execution_id="exec_1", candidate=candidate(),
                             reason=DispatchReason.TENANT_REJECTED)
        with self.assertRaises(ValueError):
            DispatchDecision(execution_id="exec_1", candidate=candidate(),
                             reason="BOGUS")
        with self.assertRaises(ValueError):
            DispatchDecision(execution_id="exec_1", candidate=candidate(),
                             decided_at=None)
        with self.assertRaises(ValueError):
            DispatchDecision(execution_id="", candidate=None,
                             reason=DispatchReason.NO_ELIGIBLE)

    def test_10_dispatch_constraints_validation(self):
        with self.assertRaises(ValueError):
            constraints(required_tool_classes="bash")
        with self.assertRaises(ValueError):
            constraints(required_tool_classes=("",))
        with self.assertRaises(ValueError):
            constraints(required_tool_classes=(True,))
        with self.assertRaises(ValueError):
            constraints(required_runtime_features=("NOT_REAL",))
        with self.assertRaises(ValueError):
            constraints(required_isolation="BOGUS")
        with self.assertRaises(ValueError):
            constraints(ordering="ROUND_ROBIN")
        with self.assertRaises(ValueError):
            constraints(require_live="yes")

    def test_11_dispatch_policy_validation(self):
        with self.assertRaises(ValueError):
            DispatchPolicy(policy_id="")
        with self.assertRaises(ValueError):
            DispatchPolicy(policy_id="pol_1", ordering="WEIGHTED")
        with self.assertRaises(ValueError):
            DispatchPolicy(policy_id="pol_1", description="ok",
                           ordering="ROUND_ROBIN")

    # ------------------------------------------------------------------
    # Deterministic serialization / round-trip / JSON safety
    # ------------------------------------------------------------------

    def test_12_deterministic_serialization(self):
        for obj in (candidate(), match(), decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1")):
            self.assertEqual(to_json(obj), to_json(obj))
            s = to_json(obj)
            self.assertEqual(list(json.loads(s).keys()),
                             sorted(json.loads(s).keys()))
            self.assertNotIn(": ", s)
            self.assertNotIn(", ", s)

    def test_13_serialization_round_trip_all_types(self):
        objs = [
            candidate(),
            candidate(state=WorkerLivenessState.STALE, seq=9),
            candidate(caps_value=caps()),
            match(),
            match(cand=candidate(caps_value=caps()), hard=("tool_classes",),
                  soft=("region",)),
            decision(),
            decision(cand=None, reason=DispatchReason.NO_ELIGIBLE),
            decision(cand=None, reason=DispatchReason.TENANT_REJECTED),
            constraints(tenant_scope="tenant_b", require_live=False,
                        required_tool_classes=("file",),
                        required_runtime_features=("heartbeat", "cancellation"),
                        required_architecture="x86_64"),
            DispatchPolicy(policy_id="pol_1"),
            DispatchPolicy(policy_id="pol_2", description="desc"),
        ]
        for obj in objs:
            d = to_dict(obj)
            restored = from_dict(d, type(obj))
            self.assertEqual(to_dict(restored), d,
                             f"dict round-trip failed for {type(obj).__name__}")
            self.assertEqual(from_json(to_json(obj), type(obj)), obj,
                             f"json round-trip failed for {type(obj).__name__}")

    def test_14_json_safety(self):
        for obj in (candidate(), match(), decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1"),
                    candidate(caps_value=caps()),
                    decision(cand=None, reason=DispatchReason.NO_ELIGIBLE)):
            d = to_dict(obj)
            json.dumps(d)
            self.assertIsInstance(d, dict)
            self.assertNotIn("__dict__", json.dumps(d))
            self.assertNotIn(".<locals>", json.dumps(d))

    def test_15_malformed_input_rejection(self):
        with self.assertRaises(ValueError):
            from_dict({"identity": {}, "state": "LIVE"}, WorkerCandidate)
        with self.assertRaises(ValueError):
            from_dict("not a dict", WorkerCandidate)
        with self.assertRaises(ValueError):
            from_dict({"execution_id": "exec_1"}, CapabilityMatch)
        with self.assertRaises(ValueError):
            from_dict({"execution_id": "exec_1", "candidate": "wrong"},
                      DispatchDecision)
        with self.assertRaises(ValueError):
            from_json("not json {", WorkerCandidate)
        with self.assertRaises(ValueError):
            from_dict({"execution_id": "exec_1", "candidate": None,
                       "reason": "BOGUS"}, DispatchDecision)

    def test_16_unsupported_type_rejection(self):
        with self.assertRaises(TypeError):
            to_dict("not a contract")
        with self.assertRaises(TypeError):
            from_dict({}, dict)

    # ------------------------------------------------------------------
    # Authority absence — gate §21 area 21 (no claim/lease/retry/authorize)
    # ------------------------------------------------------------------

    def test_17_no_claim_authority(self):
        for obj in (candidate(), match(), decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1")):
            for f in ("claim", "claim_attempt", "acquire", "attempt_no"):
                self.assertFalse(hasattr(obj, f),
                                 f"{type(obj).__name__} must not expose {f}")

    def test_18_no_lease_authority(self):
        for obj in (candidate(), match(), decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1")):
            for f in ("lease_owner", "lease_expires_at", "lease_ttl", "lease"):
                self.assertFalse(hasattr(obj, f),
                                 f"{type(obj).__name__} must not expose {f}")
        self.assertFalse(hasattr(dc, "DispatchLease"),
                         "no lease contract may be introduced")

    def test_19_no_retry_authority(self):
        for obj in (candidate(), match(), decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1")):
            for f in ("retry_count", "max_retries", "backoff", "next_retry_at",
                      "retryable", "attempts"):
                self.assertFalse(hasattr(obj, f),
                                 f"{type(obj).__name__} must not expose {f}")

    def test_20_no_task_state_authority(self):
        for obj in (candidate(), match(), decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1")):
            for f in ("status", "task_state", "mission_state", "completed",
                      "failed"):
                self.assertFalse(hasattr(obj, f),
                                 f"{type(obj).__name__} must not expose {f}")
        self.assertFalse(hasattr(dc, "TaskState"),
                         "no task-state enum may be introduced")

    def test_21_no_authorization_fields(self):
        for obj in (candidate(), match(), decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1")):
            for f in ("authorized", "allowed_tools", "permissions", "policy",
                      "can_execute", "grants", "is_authorized", "approval"):
                self.assertFalse(hasattr(obj, f),
                                 f"{type(obj).__name__} must not expose {f}")
        d = to_dict(candidate())
        flat = json.dumps(d).lower()
        for marker in ("author", "allow", "permit", "grant", "approv"):
            self.assertNotIn(marker, flat,
                             f"candidate dict must not carry {marker}")

    def test_22_no_scheduling_fields(self):
        for obj in (candidate(), match(), decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1")):
            for f in ("priority", "weight", "score", "fairness", "tie_break",
                      "queue_depth", "load"):
                self.assertFalse(hasattr(obj, f),
                                 f"{type(obj).__name__} must not expose {f}")

    # ------------------------------------------------------------------
    # Gate §21 area 16 — capacity is NEVER a hard gate (I22): no capacity
    # fields exist in the dispatch constraint/policy contracts
    # ------------------------------------------------------------------

    def test_23_no_capacity_hard_gate_fields(self):
        for f in ("max_concurrency", "max_cpu_cores", "max_memory_mb",
                  "capacity", "rate_limit"):
            self.assertFalse(hasattr(constraints(), f),
                             f"DispatchConstraints must not expose {f}")
            self.assertFalse(hasattr(DispatchPolicy(policy_id="p"), f),
                             f"DispatchPolicy must not expose {f}")

    # ------------------------------------------------------------------
    # Gate §10/§25 — ordering frozen to deterministic-first-eligible ONLY
    # ------------------------------------------------------------------

    def test_24_ordering_frozen_to_deterministic_first_eligible(self):
        self.assertEqual(DISPATCH_ORDERING_VALUES,
                         ("DETERMINISTIC_FIRST_ELIGIBLE",))
        self.assertEqual(1, len(DispatchOrdering))
        for obj in (constraints(), DispatchPolicy(policy_id="p")):
            self.assertEqual(obj.ordering,
                             DispatchOrdering.DETERMINISTIC_FIRST_ELIGIBLE)

    # ------------------------------------------------------------------
    # Gate §21 area 11 — idempotency (job_id == execution_id)
    # ------------------------------------------------------------------

    def test_25_no_second_execution_identity(self):
        # Dispatch contracts carry execution_id only as correlation: no job_id
        # and no idempotency_key may exist on any dispatch contract.
        for obj in (candidate(), match(), decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1")):
            for f in ("job_id", "idempotency_key"):
                self.assertFalse(hasattr(obj, f),
                                 f"{type(obj).__name__} must not redefine {f}")
        self.assertFalse(hasattr(dc, "DispatchJob"),
                         "no second job contract may be introduced")

    # ------------------------------------------------------------------
    # Gate §21 area 8 — duplicate dispatch (dedup surface lives in Hermes;
    # contracts must not mint a new execution identity)
    # ------------------------------------------------------------------

    def test_26_duplicate_dispatch_correlation_preserved(self):
        m1 = match(execution="exec_1")
        m2 = match(execution="exec_1")
        self.assertEqual(m1.execution_id, m2.execution_id)
        self.assertEqual(to_dict(m1), to_dict(m2))
        d1 = decision(execution="exec_1")
        d2 = decision(execution="exec_1")
        self.assertEqual(to_dict(d1), to_dict(d2))

    # ------------------------------------------------------------------
    # Gate §21 area 1 — deterministic matching: same input, same output
    # ------------------------------------------------------------------

    def test_27_deterministic_contracts(self):
        c1 = candidate(worker="w_2", seq=4)
        c2 = candidate(worker="w_2", seq=4)
        self.assertEqual(c1, c2)
        self.assertEqual(to_json(c1), to_json(c2))
        # sorted/deduped attribute tuples are deterministic
        self.assertEqual(
            constraints(required_tool_classes=("b", "a", "b"),
                        required_runtime_features=("cancellation",
                                                   "heartbeat",
                                                   "cancellation")
                        ).required_tool_classes,
            ("a", "b"))
        self.assertEqual(
            constraints(
                required_runtime_features=("heartbeat", "cancellation")
            ).required_runtime_features,
            ("cancellation", "heartbeat"))

    # ------------------------------------------------------------------
    # Gate §21 area 9 — capability ≠ authorization (I3)
    # ------------------------------------------------------------------

    def test_28_capability_match_has_no_authorization_semantics(self):
        m = match(hard=("tool_classes", "runtime_features"))
        # attribute-name tuples are sorted for deterministic serialization
        self.assertEqual(m.matched_hard_attributes, ("runtime_features",
                                                     "tool_classes"))
        for f in ("authorized", "granted", "allowed", "approved"):
            self.assertFalse(hasattr(m, f),
                             f"CapabilityMatch must not expose {f}")
        d = to_dict(m)
        flat = json.dumps(d).lower()
        for marker in ("author", "allow", "permit", "grant", "approv"):
            self.assertNotIn(marker, flat)

    def test_29_capability_spoofing_posture(self):
        # A forged/self-reported capability is representable as descriptive
        # metadata only: the contract carries no trust/attestation claim.
        forged = caps(tool_classes=("sudo",), arch="fake_arch")
        c = candidate(caps_value=forged)
        d = to_dict(c)
        self.assertEqual(d["identity"]["capabilities"]["tool_classes"],
                         ["sudo"])
        self.assertEqual(d["identity"]["capabilities"]["architecture"],
                         "fake_arch")
        # and there is no attestation/trust field anywhere
        for f in ("attestation", "signature", "verified", "trusted"):
            self.assertFalse(hasattr(forged, f),
                             f"WorkerCapabilities must not expose {f}")
        flat = json.dumps(d).lower()
        for marker in ("signature", "verified", "trusted"):
            self.assertNotIn(marker, flat)

    # ------------------------------------------------------------------
    # Gate §21 area 6 / §6 — tenant isolation (I9): WorkerCandidate carries
    # tenant_scope via the frozen identity; the dispatch constraint declares
    # tenant scope as a hard attribute.
    # ------------------------------------------------------------------

    def test_30_tenant_scope_carried_on_candidate(self):
        c = candidate(tenants=("tenant_a",))
        self.assertEqual(c.identity.tenant_scope, ("tenant_a",))
        with self.assertRaises(AttributeError):
            c.identity.tenant_scope = ("tenant_b",)
        con = constraints(tenant_scope="tenant_a")
        self.assertEqual(con.tenant_scope, "tenant_a")
        d = to_dict(c)
        self.assertEqual(d["identity"]["tenant_scope"], ["tenant_a"])

    def test_31_tenant_iso_identity_cannot_override(self):
        c = candidate(tenants=("tenant_a",))
        # tenant scope is immutable on the composed frozen identity
        with self.assertRaises(AttributeError):
            c.identity.tenant_scope = ("tenant_b",)
        self.assertEqual(c.identity.tenant_scope, ("tenant_a",))

    # ------------------------------------------------------------------
    # Gate §21 area 5 / §8 — epoch correctness (I10): WorkerCandidate binds
    # the exact (worker_id, worker_instance_id, worker_epoch) triple
    # ------------------------------------------------------------------

    def test_32_epoch_triple_binding(self):
        c1 = candidate(worker="w_1", instance="w_1_inst_1", epoch=1)
        c2 = candidate(worker="w_1", instance="w_1_inst_2", epoch=2)
        self.assertNotEqual(c1, c2)
        d1 = to_dict(c1)
        d2 = to_dict(c2)
        self.assertEqual(d1["identity"]["worker_instance_id"], "w_1_inst_1")
        self.assertEqual(d2["identity"]["worker_instance_id"], "w_1_inst_2")
        self.assertEqual(d1["identity"]["worker_epoch"], 1)
        self.assertEqual(d2["identity"]["worker_epoch"], 2)
        # same triple -> identical deterministic snapshot
        self.assertEqual(to_dict(candidate()), to_dict(candidate()))
        # epoch cannot be 0 or negative (frozen WorkerIdentity validation)
        with self.assertRaises(ValueError):
            candidate(epoch=0)

    # ------------------------------------------------------------------
    # Gate §21 areas 3, 4, 22 — liveness eligibility (I11): state is carried
    # and LIVE is the default-required constraint; STALE/DEPARTED/REGISTERED
    # are excluded by the (proposed) require_live filter.
    # ------------------------------------------------------------------

    def test_33_liveness_states_representable(self):
        for st in (WorkerLivenessState.REGISTERED, WorkerLivenessState.LIVE,
                   WorkerLivenessState.STALE, WorkerLivenessState.DEPARTED):
            c = candidate(state=st)
            self.assertEqual(c.state, st)
            self.assertEqual(to_dict(c)["state"], st.value)
        self.assertTrue(constraints().require_live)
        self.assertFalse(constraints(require_live=False).require_live)

    def test_34_stale_and_departed_never_selected_by_default(self):
        # The contract enforces LIVE-only by DEFAULT via require_live=True.
        # STALE / DEPARTED are representable (registry describes them) but the
        # default constraint excludes them from eligibility — matching logic
        # is a later seam; the CONTRACT declares the default.
        self.assertTrue(constraints().require_live)
        for st in (WorkerLivenessState.STALE, WorkerLivenessState.DEPARTED,
                   WorkerLivenessState.REGISTERED):
            c = candidate(state=st)
            self.assertEqual(c.state, st)

    def test_35_worker_candidate_has_no_lease_fields(self):
        c = candidate()
        for f in ("lease_owner", "lease_expires_at", "lease_ttl"):
            self.assertFalse(hasattr(c, f),
                             f"WorkerCandidate must not expose {f}")

    # ------------------------------------------------------------------
    # Gate §21 area 7 — capability matching (hard filter + soft ranking
    # DECLARATION ONLY — no matching logic exists in this phase)
    # ------------------------------------------------------------------

    def test_36_hard_and_soft_attributes_representable(self):
        m = match(hard=("tenant_scope", "isolation_mode", "tool_classes",
                        "runtime_features", "architecture", "worker_epoch",
                        "liveness"),
                  soft=("region", "network", "compliance"))
        # attribute-name tuples are sorted for deterministic serialization
        self.assertEqual(m.matched_hard_attributes,
                         ("architecture", "isolation_mode", "liveness",
                          "runtime_features", "tenant_scope", "tool_classes",
                          "worker_epoch"))
        self.assertEqual(m.matched_soft_attributes,
                         ("compliance", "network", "region"))
        self.assertEqual(to_dict(m)["matched_hard_attributes"],
                         ["architecture", "isolation_mode", "liveness",
                          "runtime_features", "tenant_scope", "tool_classes",
                          "worker_epoch"])

    def test_37_dispatch_constraints_declares_hard_filters(self):
        con = constraints(required_isolation=RuntimeIsolation.NONE,
                          required_tool_classes=("bash",),
                          required_runtime_features=("cancellation",),
                          required_architecture="arm64")
        d = to_dict(con)
        self.assertEqual(d["required_isolation"], "NONE")
        self.assertEqual(d["required_tool_classes"], ["bash"])
        self.assertEqual(d["required_runtime_features"], ["cancellation"])
        self.assertEqual(d["required_architecture"], "arm64")

    # ------------------------------------------------------------------
    # Gate §21 area 12 — lease race: contracts carry no lease fields (the
    # DispatchDecision never owns a lease; EE sweep remains authority)
    # ------------------------------------------------------------------

    def test_38_scheduling_and_lease_race_fields_absent(self):
        d = decision()
        for f in ("lease_expires_at", "lease_owner", "scheduled_at",
                  "queue_position"):
            self.assertFalse(hasattr(d, f),
                             f"DispatchDecision must not expose {f}")

    # ------------------------------------------------------------------
    # Gate §21 area 17 — observability correlation (§16 lineage)
    # ------------------------------------------------------------------

    def test_39_execution_id_correlation_lineage(self):
        c = candidate(worker="w_7", instance="w_7_inst_3", epoch=2,
                      transport="rt_9")
        m = match(cand=c, execution="exec_42")
        d = decision(cand=c, execution="exec_42")
        # mission_id -> task_id -> execution_id -> worker lineage is carried
        # by contract composition: execution correlation + worker triple +
        # transport identity are all preserved in the deterministic dicts.
        md = to_dict(m)
        dd = to_dict(d)
        self.assertEqual(md["execution_id"], "exec_42")
        self.assertEqual(dd["execution_id"], "exec_42")
        self.assertEqual(md["candidate"]["identity"]["worker_id"], "w_7")
        self.assertEqual(md["candidate"]["identity"]["worker_instance_id"],
                         "w_7_inst_3")
        self.assertEqual(md["candidate"]["identity"]["worker_epoch"], 2)
        self.assertEqual(md["candidate"]["identity"]["transport_identity"],
                         "rt_9")

    # ------------------------------------------------------------------
    # Gate §21 area 22 — REQUIRED_RUNTIME_FEATURES validation against the
    # frozen RuntimeCapability enum (descriptive hard-eligibility, I3)
    # ------------------------------------------------------------------

    def test_40_runtime_feature_requirements_validate_against_frozen_enum(self):
        valid = [m.value for m in RuntimeCapability]
        con = constraints(required_runtime_features=tuple(valid))
        self.assertEqual(con.required_runtime_features, tuple(sorted(valid)))
        with self.assertRaises(ValueError):
            constraints(required_runtime_features=("NOT_A_FEATURE",))
        with self.assertRaises(ValueError):
            constraints(required_runtime_features=("cancellation",
                                                   "NOT_A_FEATURE"))

    # ------------------------------------------------------------------
    # Reason taxonomy (§16 / §20): SELECTED / NO_ELIGIBLE / TENANT_REJECTED
    # ------------------------------------------------------------------

    def test_41_reason_taxonomy_exact(self):
        self.assertEqual(DISPATCH_REASON_VALUES,
                         ("SELECTED", "NO_ELIGIBLE", "TENANT_REJECTED"))
        self.assertEqual(3, len(DispatchReason))
        for r in DispatchReason:
            self.assertIn(r.value, DISPATCH_REASON_VALUES)

    # ------------------------------------------------------------------
    # Secret-safety (registry contract discipline — no secret material)
    # ------------------------------------------------------------------

    def test_42_secret_safe_serialization(self):
        for obj in (candidate(), candidate(caps_value=caps()), match(),
                    decision(), constraints(),
                    DispatchPolicy(policy_id="pol_1")):
            d = to_dict(obj)
            flat = json.dumps(d).lower()
            for secret_marker in ("api_key", "token", "password",
                                  "authorization", "credential"):
                self.assertNotIn(secret_marker, flat)
            # "secret" may appear ONLY inside the frozen supports_secrets
            # capability flag (a boolean descriptor, never secret material):
            # every "secret" occurrence must be part of "supports_secrets",
            # and no field may be literally named "secret" nor hold a
            # secret-like string value.
            self.assertEqual(flat.count("secret"),
                             flat.count("supports_secrets"))
            self.assertNotIn('"secret"', flat)
            self.assertNotIn(": \"secret", flat)

    # ------------------------------------------------------------------
    # Deserializer forward-compat: missing optional fields default sanely
    # ------------------------------------------------------------------

    def test_43_deserializer_defaults(self):
        # minimal candidate dict (only required keys): defaults fill the rest
        cand_d = to_dict(candidate())
        minimal = {k: cand_d[k] for k in ("identity", "state",
                                          "registered_at")}
        c = from_dict(minimal, WorkerCandidate)
        self.assertEqual(c.reported_at, None)
        self.assertEqual(c.heartbeat_seq, 0)
        # reason defaults to SELECTED when candidate present
        d = from_dict({"execution_id": "exec_1",
                       "candidate": to_dict(candidate())},
                      DispatchDecision)
        self.assertEqual(d.reason, DispatchReason.SELECTED)
        # constraints default ordering
        con = from_dict({}, DispatchConstraints)
        self.assertEqual(con.ordering,
                         DispatchOrdering.DETERMINISTIC_FIRST_ELIGIBLE)
        self.assertTrue(con.require_live)
        # policy default ordering
        p = from_dict({"policy_id": "pol_1"}, DispatchPolicy)
        self.assertEqual(p.ordering,
                         DispatchOrdering.DETERMINISTIC_FIRST_ELIGIBLE)


if __name__ == "__main__":
    unittest.main(verbosity=2)