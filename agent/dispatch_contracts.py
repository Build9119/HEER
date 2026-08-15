#!/usr/bin/env python3
"""dispatch_contracts.py — HEER Worker Dispatch & Capability Matching Contracts
(Phase 3.6.1).

Immutable, JSON-safe contract layer for the Phase 3.6 Worker Dispatch gate
(HEER_PHASE36_WORKER_DISPATCH_GATE.md).

SCOPE: CONTRACTS ONLY. This module contains no dispatch implementation:
no candidate selection, no matching algorithm, no assignment, no scheduling,
no transport binding, no registry interaction, no policy engine.

It selects NOTHING and AUTHORIZES NOTHING. Dispatch is a pure function over
registry entries + request metadata (gate section 3); these contracts describe
the immutable shapes that pure function consumes and produces (gate section 20).

Authority boundaries (frozen — gate sections 3, 11, 23):
  Execution Engine (I1): execution_id, attempts, leases, retries, task state,
    cancellation, final persistence.
  Governance (I18): approvals L0-L3 + allowlist + attempt claim.
  Hermes adapter (I15): submit/start/cancel/heartbeat/status/result/recover/
    terminate.
  Worker Registry (I2): descriptive identity/capability/liveness — frozen,
    never modified here; WorkerIdentity/WorkerCapabilities/WorkerLiveness are
    composed, never redefined (I17).

These contracts carry NO authority:
  - MATCHING only: descriptive attribute evaluation (gate sections 3, 5).
  - Capability is descriptive, never authorization (I3).
  - No claim/lease/retry/task-state/authorize/schedule surface (I4-I6, I14, I19).
  - Deterministic-first-eligible is the ONLY frozen ordering (gate sections 10,
    25): weighted/least-loaded/round-robin/capability-score/policy-driven
    scheduling (options B-H) are OPEN and deliberately NOT representable.
  - Worker-reported capacity is never a hard gate (I22): no capacity fields
    exist anywhere in this module.
  - Dispatch re-validates candidate liveness/epoch at dispatch time (I21); the
    WorkerCandidate snapshot carries the registry liveness triple only.
  - No second execution identity is introduced (I19, derived from I7/I8):
    `execution_id` appears ONLY as a read-only correlation reference on
    CapabilityMatch and DispatchDecision; `job_id` / `idempotency_key` are
    never redefined.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import cast

from .runtime_contracts import (
    RuntimeCapability,
    RuntimeIsolation,
    _enum_from,
    _json_safe_copy,
    _require_id,
    _require_str_opt,
    _require_ts,
)
from .worker_contracts import (
    WorkerIdentity,
    WorkerLivenessState,
    from_dict as _worker_from_dict,
    to_dict as _worker_to_dict,
)

__all__ = [
    "DispatchOrdering",
    "DispatchReason",
    "WorkerCandidate",
    "CapabilityMatch",
    "DispatchDecision",
    "DispatchConstraints",
    "DispatchPolicy",
    "DISPATCH_ORDERING_VALUES",
    "DISPATCH_REASON_VALUES",
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
]


class DispatchOrdering(Enum):
    """Frozen dispatch ordering — EXACTLY ONE member (gate sections 10, 25).

    Deterministic first-eligible (sorted by worker_id) is the ONLY frozen
    default: reproducible, tenant-safe, and zero new authority. Weighted
    ranking, least-loaded, round-robin, capability score, tenant-aware
    ordering and policy-driven scheduling (options B-H) are OPEN and
    deliberately NOT representable here.
    """
    DETERMINISTIC_FIRST_ELIGIBLE = "DETERMINISTIC_FIRST_ELIGIBLE"


DISPATCH_ORDERING_VALUES: tuple = tuple(o.value for o in DispatchOrdering)


class DispatchReason(Enum):
    """Descriptive dispatch outcome reason (gate sections 16, 20).

    Reasons map 1:1 to the additive observability events DISPATCH_SELECTED /
    DISPATCH_NO_ELIGIBLE / DISPATCH_TENANT_REJECTED. A reason explains an
    outcome; it grants nothing.
    """
    SELECTED = "SELECTED"
    NO_ELIGIBLE = "NO_ELIGIBLE"
    TENANT_REJECTED = "TENANT_REJECTED"


DISPATCH_REASON_VALUES: tuple = tuple(r.value for r in DispatchReason)


# ---------------------------------------------------------------------------
# Validation helpers (pure, deterministic — same discipline as runtime_contracts
# and worker_contracts)
# ---------------------------------------------------------------------------

def _require_liveness_state(value):
    if isinstance(value, WorkerLivenessState):
        return value
    raise ValueError("state must be WorkerLivenessState")


def _require_nonneg_int(value, name):
    """Non-negative int (registry heartbeat_seq starts at 0)."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative int")
    return value


def _require_required_ts(value, name):
    ts = _require_ts(value, name)
    if ts is None:
        raise ValueError(f"{name} is required")
    return ts


def _require_str_tuple(value, name):
    """Normalize to a sorted, deduplicated, immutable tuple of non-empty strings.

    Sorted order makes serialization deterministic and stable across instances.
    """
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be an iterable of strings, not a string")
    if not isinstance(value, Iterable):
        raise ValueError(f"{name} must be an iterable of strings")
    out = []
    for entry in value:
        if isinstance(entry, bool) or not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"{name} entries must be non-empty strings")
        out.append(entry)
    return tuple(sorted(set(out)))


def _require_feature_tuple(value):
    """Runtime-feature requirement names must be known RuntimeCapability values
    (descriptive hard-eligibility filter only — gate section 5, I3)."""
    if value is None:
        return ()
    out = _require_str_tuple(value, "required_runtime_features")
    known = {m.value for m in RuntimeCapability}
    bad = [f for f in out if f not in known]
    if bad:
        raise ValueError(f"unknown runtime feature(s): {sorted(bad)}")
    return out


def _require_isolation_opt(value):
    if value is None:
        return None
    return _enum_from(value, RuntimeIsolation)


def _require_candidate(value):
    if value is not None and not isinstance(value, WorkerCandidate):
        raise ValueError("candidate must be WorkerCandidate or None")
    return value


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class WorkerCandidate:
    """Immutable snapshot of a registry entry (gate section 20).

    Identity triple = (worker_id, worker_instance_id, worker_epoch) — carried
    by the frozen WorkerIdentity (composed, never redefined). The liveness
    snapshot (state / registered_at / reported_at / heartbeat_seq) is
    fabric-local descriptive state, never an EE lease (I11). tenant_scope is
    carried via the identity (I9). transport_identity likewise comes from the
    frozen identity.

    This contract grants NO execution authority: it carries no execution_id,
    no job identity, no mission/task/attempt fields, no lease, no retry, and
    no task state.
    """
    identity: WorkerIdentity
    state: WorkerLivenessState = WorkerLivenessState.REGISTERED
    registered_at: float = 0.0
    reported_at: float | None = None
    heartbeat_seq: int = 0

    def __post_init__(self):
        if not isinstance(self.identity, WorkerIdentity):
            raise ValueError("identity must be a WorkerIdentity")
        object.__setattr__(self, "state",
                           _enum_from(self.state, WorkerLivenessState))
        object.__setattr__(self, "registered_at",
                           _require_required_ts(self.registered_at, "registered_at"))
        object.__setattr__(self, "reported_at",
                           _require_ts(self.reported_at, "reported_at"))
        object.__setattr__(self, "heartbeat_seq",
                           _require_nonneg_int(self.heartbeat_seq, "heartbeat_seq"))


@dataclass(frozen=True, slots=True)
class CapabilityMatch:
    """Candidate + matched descriptive attributes (gate section 20).

    Correlates to `execution_id` as a READ-ONLY reference: the match ECHOES the
    already-authorized execution identity (job_id == execution_id, I7/I8) and
    NEVER creates or owns one (I19). `matched_hard_attributes` /
    `matched_soft_attributes` are descriptive attribute names ONLY (gate
    section 5) — matching is not authorization (I3) and grants no
    execution/lease/retry/task-state authority.
    """
    candidate: WorkerCandidate
    execution_id: str
    matched_hard_attributes: tuple = field(default_factory=tuple)
    matched_soft_attributes: tuple = field(default_factory=tuple)
    matched_at: float = 0.0

    def __post_init__(self):
        if not isinstance(self.candidate, WorkerCandidate):
            raise ValueError("candidate must be a WorkerCandidate")
        object.__setattr__(self, "execution_id",
                           _require_id(self.execution_id, "execution_id"))
        object.__setattr__(
            self, "matched_hard_attributes",
            _require_str_tuple(self.matched_hard_attributes,
                               "matched_hard_attributes"))
        object.__setattr__(
            self, "matched_soft_attributes",
            _require_str_tuple(self.matched_soft_attributes,
                               "matched_soft_attributes"))
        object.__setattr__(self, "matched_at",
                           _require_required_ts(self.matched_at, "matched_at"))


@dataclass(frozen=True, slots=True)
class DispatchDecision:
    """Outcome of a dispatch/matching evaluation (gate section 20).

    Identified by the execution correlation + candidate. `candidate` is None
    exactly when no eligible worker exists (reason NO_ELIGIBLE /
    TENANT_REJECTED). The decision selects a candidate — or none — and nothing
    else (gate sections 3, 11, 23 I4-I6, I18-I19): it carries NO
    claim/lease/retry/authorize/task-state surface.
    """
    execution_id: str
    candidate: WorkerCandidate | None
    reason: DispatchReason = DispatchReason.SELECTED
    decided_at: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, "execution_id",
                           _require_id(self.execution_id, "execution_id"))
        object.__setattr__(self, "candidate", _require_candidate(self.candidate))
        object.__setattr__(self, "reason", _enum_from(self.reason, DispatchReason))
        object.__setattr__(self, "decided_at",
                           _require_required_ts(self.decided_at, "decided_at"))
        if self.candidate is None and self.reason is DispatchReason.SELECTED:
            raise ValueError("candidate is required when reason is SELECTED")
        if self.candidate is not None and self.reason is not DispatchReason.SELECTED:
            raise ValueError("reason must be SELECTED when a candidate is present")


@dataclass(frozen=True, slots=True)
class DispatchConstraints:
    """Descriptive hard-attribute filter-set DECLARATION (gate sections 5, 8, 20).

    Declares which descriptive attributes a candidate must satisfy: tenant
    scope, liveness (LIVE-only by default — gate section 8), isolation mode,
    tool classes, runtime features, and architecture. This is MATCHING only
    (gate section 3): eliminating a candidate is descriptive filtering, never
    rejection of the job, and never authorization (I3, I18).

    Deliberately ABSENT (gate sections 9, 23 I22): no capacity fields
    (max_concurrency / max_cpu_cores / max_memory_mb / queue depth) —
    worker-reported capacity is never a hard gate, and soft ranking is OPEN.
    `ordering` is frozen to deterministic-first-eligible; nothing else is
    representable (gate sections 10, 25).
    """
    tenant_scope: str | None = None
    require_live: bool = True
    required_isolation: RuntimeIsolation | None = None
    required_tool_classes: tuple = field(default_factory=tuple)
    required_runtime_features: tuple = field(default_factory=tuple)
    required_architecture: str | None = None
    ordering: DispatchOrdering = DispatchOrdering.DETERMINISTIC_FIRST_ELIGIBLE

    def __post_init__(self):
        object.__setattr__(self, "tenant_scope",
                           _require_str_opt(self.tenant_scope, "tenant_scope"))
        if not isinstance(self.require_live, bool):
            raise ValueError("require_live must be a bool")
        object.__setattr__(self, "required_isolation",
                           _require_isolation_opt(self.required_isolation))
        object.__setattr__(
            self, "required_tool_classes",
            _require_str_tuple(self.required_tool_classes, "required_tool_classes"))
        object.__setattr__(
            self, "required_runtime_features",
            _require_feature_tuple(self.required_runtime_features))
        object.__setattr__(
            self, "required_architecture",
            _require_str_opt(self.required_architecture, "required_architecture"))
        object.__setattr__(self, "ordering",
                           _enum_from(self.ordering, DispatchOrdering))


@dataclass(frozen=True, slots=True)
class DispatchPolicy:
    """Dispatch ordering policy — frozen to deterministic first-eligible
    (gate sections 10, 20, 25).

    Identified by `policy_id`. The ONLY representable ordering is
    DETERMINISTIC_FIRST_ELIGIBLE (sorted by worker_id): reproducible,
    tenant-safe, zero new authority. Weighted/least-loaded/round-robin/
    capability-score/policy-driven scheduling (options B-H) are OPEN and
    deliberately NOT representable: there are no weight, priority, fairness,
    or tie-break ranking fields.

    A dispatch policy influences the ORDER of eligible candidates only; it
    grants nothing and authorizes nothing (I14, I20). `description` is a
    human-readable declaration, never an executable rule set.
    """
    policy_id: str
    ordering: DispatchOrdering = DispatchOrdering.DETERMINISTIC_FIRST_ELIGIBLE
    description: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "policy_id",
                           _require_id(self.policy_id, "policy_id"))
        object.__setattr__(self, "ordering",
                           _enum_from(self.ordering, DispatchOrdering))
        object.__setattr__(self, "description",
                           _require_str_opt(self.description, "description"))


# ---------------------------------------------------------------------------
# Serialization (deterministic, JSON-safe, secret-safe — same conventions as
# agent/worker_contracts.py and agent/runtime_contracts.py; no second
# incompatible format)
# ---------------------------------------------------------------------------

def _check_required(data, required, name):
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be a dict")
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"{name} missing required keys: {sorted(missing)}")


def to_dict(obj):
    """Deterministic JSON-safe dict for the dispatch contracts.

    WorkerCandidate mirrors the registry's `_entry_dict()` shape exactly
    (identity + state + registered_at + reported_at + heartbeat_seq), so a
    registry entry snapshot reconstructs into the contract directly.
    Serialization uses `redact=False` to preserve the frozen worker/runtime
    sub-contracts bit-for-bit (same convention as worker_contracts.to_dict).
    `_json_safe_copy` still enforces JSON-safety (rejects callables/bytes/
    non-finite values).
    """
    if isinstance(obj, WorkerCandidate):
        return _json_safe_copy({
            "identity": _worker_to_dict(obj.identity),
            "state": obj.state.value,
            "registered_at": obj.registered_at,
            "reported_at": obj.reported_at,
            "heartbeat_seq": obj.heartbeat_seq,
        }, redact=False)
    if isinstance(obj, CapabilityMatch):
        return _json_safe_copy({
            "candidate": to_dict(obj.candidate),
            "execution_id": obj.execution_id,
            "matched_hard_attributes": list(obj.matched_hard_attributes),
            "matched_soft_attributes": list(obj.matched_soft_attributes),
            "matched_at": obj.matched_at,
        }, redact=False)
    if isinstance(obj, DispatchDecision):
        return _json_safe_copy({
            "execution_id": obj.execution_id,
            "candidate": None if obj.candidate is None else to_dict(obj.candidate),
            "reason": obj.reason.value,
            "decided_at": obj.decided_at,
        }, redact=False)
    if isinstance(obj, DispatchConstraints):
        return _json_safe_copy({
            "tenant_scope": obj.tenant_scope,
            "require_live": obj.require_live,
            "required_isolation": None if obj.required_isolation is None
                else obj.required_isolation.value,
            "required_tool_classes": list(obj.required_tool_classes),
            "required_runtime_features": list(obj.required_runtime_features),
            "required_architecture": obj.required_architecture,
            "ordering": obj.ordering.value,
        }, redact=False)
    if isinstance(obj, DispatchPolicy):
        return _json_safe_copy({
            "policy_id": obj.policy_id,
            "ordering": obj.ordering.value,
            "description": obj.description,
        }, redact=False)
    raise TypeError(f"unsupported dispatch contract: {type(obj).__name__}")


_REQUIRED_CANDIDATE = ("identity", "state", "registered_at")
_REQUIRED_MATCH = ("candidate", "execution_id")
_REQUIRED_DECISION = ("execution_id", "candidate")
_REQUIRED_POLICY = ("policy_id",)


def from_dict(data, obj_type):
    """Reconstruct a dispatch contract from a dict (full validation)."""
    if obj_type is WorkerCandidate:
        _check_required(data, _REQUIRED_CANDIDATE, "WorkerCandidate")
        return WorkerCandidate(
            identity=cast(
                WorkerIdentity,
                _worker_from_dict(data["identity"], WorkerIdentity)),
            state=_enum_from(data["state"], WorkerLivenessState),
            registered_at=data["registered_at"],
            reported_at=data.get("reported_at"),
            heartbeat_seq=data.get("heartbeat_seq", 0))
    if obj_type is CapabilityMatch:
        _check_required(data, _REQUIRED_MATCH, "CapabilityMatch")
        return CapabilityMatch(
            candidate=cast(
                WorkerCandidate,
                from_dict(data["candidate"], WorkerCandidate)),
            execution_id=data["execution_id"],
            matched_hard_attributes=data.get("matched_hard_attributes", ()),
            matched_soft_attributes=data.get("matched_soft_attributes", ()),
            matched_at=data.get("matched_at", 0.0))
    if obj_type is DispatchDecision:
        _check_required(data, _REQUIRED_DECISION, "DispatchDecision")
        cand = data["candidate"]
        if cand is not None and not isinstance(cand, dict):
            raise ValueError("candidate must be a dict or None")
        return DispatchDecision(
            execution_id=data["execution_id"],
            candidate=None if cand is None else cast(
                WorkerCandidate, from_dict(cand, WorkerCandidate)),
            reason=_enum_from(data.get("reason", "SELECTED"), DispatchReason),
            decided_at=data.get("decided_at", 0.0))
    if obj_type is DispatchConstraints:
        if not isinstance(data, dict):
            raise ValueError("DispatchConstraints must be a dict")
        iso = data.get("required_isolation")
        return DispatchConstraints(
            tenant_scope=data.get("tenant_scope"),
            require_live=data.get("require_live", True),
            required_isolation=None if iso is None
                else _enum_from(iso, RuntimeIsolation),
            required_tool_classes=data.get("required_tool_classes", ()),
            required_runtime_features=data.get("required_runtime_features", ()),
            required_architecture=data.get("required_architecture"),
            ordering=_enum_from(
                data.get("ordering", "DETERMINISTIC_FIRST_ELIGIBLE"),
                DispatchOrdering))
    if obj_type is DispatchPolicy:
        _check_required(data, _REQUIRED_POLICY, "DispatchPolicy")
        return DispatchPolicy(
            policy_id=data["policy_id"],
            ordering=_enum_from(
                data.get("ordering", "DETERMINISTIC_FIRST_ELIGIBLE"),
                DispatchOrdering),
            description=data.get("description"))
    raise TypeError(f"unsupported dispatch contract type: {obj_type!r}")


def to_json(obj):
    """Deterministic canonical JSON (sorted keys, compact separators) —
    identical convention to runtime_contracts.to_json / worker_contracts.to_json."""
    return json.dumps(to_dict(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def from_json(text, obj_type):
    """Reconstruct a dispatch contract from canonical JSON text."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("from_json requires a JSON string")
    return from_dict(json.loads(text), obj_type)