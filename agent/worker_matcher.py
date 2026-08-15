#!/usr/bin/env python3
"""worker_matcher.py — HEER Deterministic Worker Capability Matching Engine
(Phase 3.6.2).

Pure, deterministic DECISION/SELECTION layer over the Worker Registry
(Phase 3.5) and the frozen dispatch contracts (Phase 3.6.1).

SCOPE (frozen — HEER_PHASE36_WORKER_DISPATCH_GATE.md sections 3, 5, 8, 10,
20, 23):
  - candidate discovery (tenant-scoped registry read)
  - tenant eligibility (hard)
  - worker liveness eligibility (hard; LIVE-only by default)
  - hard capability filtering (tool classes, runtime features, isolation,
    architecture)
  - deterministic ordering (DETERMINISTIC_FIRST_ELIGIBLE by worker_id)
  - DispatchDecision / CapabilityMatch construction (frozen contracts)

The matcher is a DECISION/SELECTION layer ONLY. It MUST NOT become:
  a scheduler, dispatcher, executor, authorization engine, approval engine,
  lease manager, retry manager, task-state manager, persistence authority,
  Hermes transport, or worker lifecycle manager (gate sections 3, 11, 23).

NO SIDE EFFECTS AFTER THE DECISION (gate section 20):
  - no sleeps, threads, network I/O, file writes, SQLite, audit records, events
  - no tool calls, no Hermes invocation, no Execution Engine calls
  - no registry mutation (read-only: list() / status() only)

Capability is DESCRIPTIVE, never authorization (I3, I10): matching selects a
candidate; it grants nothing. Worker-reported capacity is never a hard gate
(I22): no capacity fields are consulted. Liveness is fabric-local, never an EE
lease (I11). No second execution identity is created (I19): execution_id is a
read-only correlation reference (I7/I8).
"""
from __future__ import annotations

from .dispatch_contracts import (
    CapabilityMatch,
    DispatchConstraints,
    DispatchDecision,
    DispatchReason,
    WorkerCandidate,
    from_dict as _dispatch_from_dict,
)
from .worker_contracts import WorkerLivenessState

__all__ = ["WorkerMatcher"]


class WorkerMatcher:
    """Deterministic worker capability matching engine (Phase 3.6.2).

    Consumes the Worker Registry's descriptive entries and a
    DispatchConstraints declaration; produces a frozen DispatchDecision (and a
    frozen CapabilityMatch via evaluate()). Pure: identical registry snapshot +
    constraints + execution_id + decided_at produce an identical decision.

    Public surface:
      match(constraints, *, execution_id, decided_at=None) -> DispatchDecision
      evaluate(constraints, *, execution_id, decided_at=None)
          -> (DispatchDecision, CapabilityMatch | None)

    No other public methods exist: no dispatch/assign/schedule/execute/
    authorize/approve/acquire_lease/retry/cancel/complete surface (gate
    sections 3, 11, 23; authority tests).
    """

    def __init__(self, registry):
        """Bind to a WorkerRegistry (read-only consumer)."""
        if not (hasattr(registry, "list") and hasattr(registry, "status")):
            raise ValueError("registry must expose list() and status()")
        self._registry = registry

    def match(self, constraints, *, execution_id, decided_at=None):
        """Return the frozen DispatchDecision for the constraints.

        decided_at=None defaults to 0.0 (deterministic sentinel) so match()
        remains a pure function of its inputs; callers pass an explicit
        timestamp for observability.
        """
        return self.evaluate(constraints, execution_id=execution_id,
                             decided_at=decided_at)[0]

    def evaluate(self, constraints, *, execution_id, decided_at=None):
        """Full evaluation: (DispatchDecision, CapabilityMatch | None).

        CapabilityMatch is None when no candidate is selected (NO_ELIGIBLE /
        TENANT_REJECTED). Both returned objects are frozen dispatch contracts.
        """
        if not isinstance(constraints, DispatchConstraints):
            raise ValueError("constraints must be a DispatchConstraints")
        if not isinstance(execution_id, str) or not execution_id.strip():
            raise ValueError("execution_id must be a non-empty string")
        ts = 0.0 if decided_at is None else decided_at

        total = self._registry.status()["total"]
        if total == 0:
            return self._no_eligible(execution_id, ts), None

        entries = self._registry.list(tenant_scope=constraints.tenant_scope)
        if not entries:
            if constraints.tenant_scope is not None:
                return self._tenant_rejected(execution_id, ts), None
            return self._no_eligible(execution_id, ts), None

        candidates = []
        for entry in entries:
            cand = _dispatch_from_dict(entry, WorkerCandidate)
            if self._eligible(cand, constraints):
                candidates.append(cand)

        if not candidates:
            return self._no_eligible(execution_id, ts), None

        # Deterministic first-eligible: explicit stable order by the identity
        # triple (worker_id, worker_instance_id, worker_epoch). The registry
        # already returns sorted-by-worker_id entries; the explicit sort makes
        # the ordering robust and self-documenting (gate sections 10, 25).
        candidates.sort(key=lambda c: (c.identity.worker_id,
                                       c.identity.worker_instance_id,
                                       c.identity.worker_epoch))
        selected = candidates[0]
        cmatch = CapabilityMatch(
            candidate=selected,
            execution_id=execution_id,
            matched_hard_attributes=self._matched_hard_attributes(constraints),
            matched_soft_attributes=(),
            matched_at=ts)
        decision = DispatchDecision(
            execution_id=execution_id, candidate=selected,
            reason=DispatchReason.SELECTED, decided_at=ts)
        return decision, cmatch

    # ------------------------------------------------------------------
    # Decision helpers (frozen contracts only)
    # ------------------------------------------------------------------

    @staticmethod
    def _no_eligible(execution_id, ts):
        return DispatchDecision(
            execution_id=execution_id, candidate=None,
            reason=DispatchReason.NO_ELIGIBLE, decided_at=ts)

    @staticmethod
    def _tenant_rejected(execution_id, ts):
        return DispatchDecision(
            execution_id=execution_id, candidate=None,
            reason=DispatchReason.TENANT_REJECTED, decided_at=ts)

    # ------------------------------------------------------------------
    # Eligibility (hard filters only — descriptive, never authorization)
    # ------------------------------------------------------------------

    @staticmethod
    def _eligible(cand, constraints):
        """Hard eligibility: tenant, liveness, isolation, tool classes,
        runtime features, architecture. Capacity is NEVER consulted (I22)."""
        if constraints.tenant_scope is not None:
            if constraints.tenant_scope not in cand.identity.tenant_scope:
                return False
        if constraints.require_live:
            if cand.state != WorkerLivenessState.LIVE:
                return False
        else:
            # require_live=False relaxes LIVE-only to admit REGISTERED (gate
            # section 8: a minimum-liveness policy may admit REGISTERED);
            # STALE and DEPARTED remain hard-excluded in ALL cases.
            if cand.state not in (WorkerLivenessState.LIVE,
                                  WorkerLivenessState.REGISTERED):
                return False
        if constraints.required_isolation is not None:
            if cand.identity.isolation_mode != constraints.required_isolation:
                return False
        caps = cand.identity.capabilities
        if constraints.required_tool_classes:
            if caps is None:
                return False
            if not set(constraints.required_tool_classes) <= set(caps.tool_classes):
                return False
        if constraints.required_runtime_features:
            if caps is None or caps.runtime_capabilities is None:
                return False
            worker_feats = {f.value for f in caps.runtime_capabilities.features}
            if not set(constraints.required_runtime_features) <= worker_feats:
                return False
        if constraints.required_architecture is not None:
            if caps is None or caps.architecture != constraints.required_architecture:
                return False
        return True

    @staticmethod
    def _matched_hard_attributes(constraints):
        """Deterministic sorted tuple of hard attribute names that matched.

        liveness and worker_epoch are always-evaluated hard attributes (gate
        section 5); the remaining names are reported only when the constraint
        declared them (and the candidate satisfied them — the candidate is
        already known eligible at this point).
        """
        attrs = {"liveness", "worker_epoch"}
        if constraints.tenant_scope is not None:
            attrs.add("tenant_scope")
        if constraints.required_isolation is not None:
            attrs.add("isolation_mode")
        if constraints.required_tool_classes:
            attrs.add("tool_classes")
        if constraints.required_runtime_features:
            attrs.add("runtime_features")
        if constraints.required_architecture is not None:
            attrs.add("architecture")
        return tuple(sorted(attrs))