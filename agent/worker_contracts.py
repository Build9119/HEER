"""Worker Fabric Contracts (Phase 3.5.1) — immutable, JSON-safe contract layer for the
Phase 3.5 Worker Fabric architecture gate (HEER_PHASE35_WORKER_FABRIC_GATE.md).

SCOPE: CONTRACTS ONLY. This module contains no worker implementation:
no worker daemon, no registry service, no scheduler, no worker pool,
no subprocess/container/remote transport, no service discovery, no broker,
no network server, no database.

It contains no execution: workers execute jobs ONLY when the Execution Engine
authorizes them. THIS MODULE GRANTS NOTHING.

Authority boundaries (frozen — HEER_PHASE35_WORKER_FABRIC_GATE.md sections 1, 15, 21):
  Execution Engine retains sole authority for:
    - execution_id
    - attempt lifecycle (attempt_no)
    - task lifecycle (PENDING/READY/RUNNING/COMPLETED/FAILED/BLOCKED/CANCELLED)
    - leases / lease expiry (lease_owner, lease_expires_at)
    - retry policy / exponential backoff / max attempts
    - cancellation policy / timeout policy
    - final persistence authority
    - audit authority (no competing audit store)
  Hermes/runtime remains the runtime transport only.
  Worker Fabric contracts carry NO policy authority:
    - capabilities are descriptive metadata only (capability != authorization, I10)
    - worker liveness is NOT an EE lease (I11)
    - workers acquire no autonomy (I16)
    - no frozen Phase 3.1/3.2/3.3/3.4 contract is mutated (I17)

Job/result identity is NOT duplicated here: a worker executes exactly one frozen
RuntimeJob and returns one frozen RuntimeResult (gate sections 2 and 4). This module
introduces NO second execution identity (I5/I6). Identity verification/attestation is
NOT implemented here — the gate leaves attestation unresolved (gate section 22) and it
is recorded as an open implementation concern; registration is represented only by the
fabric-local liveness states defined in the gate section 3.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

from .runtime_contracts import (
    RuntimeCapabilities,
    RuntimeIsolation,
    _enum_from,
    _json_safe_copy,
    _require_id,
    _require_str_opt,
    _require_ts,
)

__all__ = [
    "WorkerLivenessState",
    "WorkerIdentity",
    "WorkerCapabilities",
    "WorkerLiveness",
    "WORKER_LIVENESS_STATE_VALUES",
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
]


class WorkerLivenessState(Enum):
    """Fabric-local registration/liveness states — exactly the four states defined by
    HEER_PHASE35_WORKER_FABRIC_GATE.md section 3.

    These states are worker-liveness metadata ONLY and are NEVER an EE lease
    (invariant I11). Lease authority remains in the Execution Engine.
    """
    REGISTERED = "REGISTERED"
    LIVE = "LIVE"
    STALE = "STALE"
    DEPARTED = "DEPARTED"


WORKER_LIVENESS_STATE_VALUES: tuple = tuple(s.value for s in WorkerLivenessState)


# ---------------------------------------------------------------------------
# Validation helpers (pure, deterministic — same discipline as runtime_contracts)
# ---------------------------------------------------------------------------

def _require_positive_int(value, name, *, allow_none=False):
    """Positive int required; optional None allowed for capacity-report fields."""
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive int")
    return value


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


def _require_worker_caps(value):
    if value is None:
        return None
    if not isinstance(value, WorkerCapabilities):
        raise ValueError("capabilities must be WorkerCapabilities or None")
    return value


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class WorkerCapabilities:
    """Descriptive worker capability metadata — NEVER authorization (invariant I10).

    A worker advertising a capability is NOT thereby authorized to execute anything.
    Authorization remains upstream: L0-L3 approvals, tool allowlist, and the
    Execution Engine attempt claim. `runtime_capabilities` references the frozen
    Phase 3.4 RuntimeCapabilities contract (frozen composition — never mutated).

    Resource fields (max_cpu_cores / max_memory_mb) are CAPACITY REPORTS ONLY —
    the Execution Engine enforces resource policy (gate section 11).
    """
    runtime_capabilities: RuntimeCapabilities | None = None
    tool_classes: tuple = field(default_factory=tuple)   # tuple[str, ...]
    max_cpu_cores: int | None = None
    max_memory_mb: int | None = None
    architecture: str | None = None
    network_policy: str | None = None
    region: str | None = None
    compliance_boundary: str | None = None
    runtime_version: str | None = None

    def __post_init__(self):
        object.__setattr__(
            self, "runtime_capabilities",
            _require_caps_ref(self.runtime_capabilities))
        object.__setattr__(
            self, "tool_classes", _require_str_tuple(self.tool_classes, "tool_classes"))
        object.__setattr__(
            self, "max_cpu_cores",
            _require_positive_int(self.max_cpu_cores, "max_cpu_cores", allow_none=True))
        object.__setattr__(
            self, "max_memory_mb",
            _require_positive_int(self.max_memory_mb, "max_memory_mb", allow_none=True))
        object.__setattr__(
            self, "architecture", _require_str_opt(self.architecture, "architecture"))
        object.__setattr__(
            self, "network_policy", _require_str_opt(self.network_policy, "network_policy"))
        object.__setattr__(
            self, "region", _require_str_opt(self.region, "region"))
        object.__setattr__(
            self, "compliance_boundary",
            _require_str_opt(self.compliance_boundary, "compliance_boundary"))
        object.__setattr__(
            self, "runtime_version", _require_str_opt(self.runtime_version, "runtime_version"))


def _require_caps_ref(value):
    if value is None:
        return None
    if not isinstance(value, RuntimeCapabilities):
        raise ValueError("runtime_capabilities must be RuntimeCapabilities or None")
    return value


@dataclass(frozen=True, slots=True)
class WorkerIdentity:
    """Immutable worker identity -- exactly the fields defined by gate section 3.

    Identity is DESCRIPTIVE: it identifies a worker so the Execution Engine can
    correlate results. It grants nothing. Worker identity cannot be caller-modified
    to claim authority (spoofing) because nothing in this contract IS authority:
    the EE validates correlation before any state write. Attestation/verification
    is intentionally NOT implemented here (gate section 22 open question).

    Liveness is intentionally separate and mutable (`WorkerLiveness`) because the
    gate models identity as immutable and liveness as mutable.
    """
    worker_id: str
    worker_instance_id: str
    worker_epoch: int
    tenant_scope: tuple = field(default_factory=tuple)   # tuple[str, ...]
    capabilities: WorkerCapabilities | None = None
    isolation_mode: RuntimeIsolation = RuntimeIsolation.NONE
    transport_identity: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "worker_id", _require_id(self.worker_id, "worker_id"))
        object.__setattr__(
            self, "worker_instance_id",
            _require_id(self.worker_instance_id, "worker_instance_id"))
        object.__setattr__(
            self, "worker_epoch",
            _require_positive_int(self.worker_epoch, "worker_epoch"))
        object.__setattr__(
            self, "tenant_scope", _require_str_tuple(self.tenant_scope, "tenant_scope"))
        object.__setattr__(
            self, "capabilities", _require_worker_caps(self.capabilities))
        object.__setattr__(
            self, "isolation_mode", _enum_from(self.isolation_mode, RuntimeIsolation))
        object.__setattr__(
            self, "transport_identity",
            _require_str_opt(self.transport_identity, "transport_identity"))


@dataclass(frozen=True, slots=True)
class WorkerLiveness:
    """Fabric-local liveness report — NOT an EE lease (invariant I11).

    This contract contains NO lease fields (no lease_owner / lease_expires_at),
    no retry fields, and no task-state fields. The Execution Engine remains the sole
    lease authority; worker liveness is a signal only. `heartbeat_seq` is a
    fabric-local monotonic counter for stale-report detection.
    """
    worker_id: str
    worker_instance_id: str
    worker_epoch: int
    state: WorkerLivenessState
    reported_at: float
    heartbeat_seq: int | None = None

    def __post_init__(self):
        object.__setattr__(self, "worker_id", _require_id(self.worker_id, "worker_id"))
        object.__setattr__(
            self, "worker_instance_id",
            _require_id(self.worker_instance_id, "worker_instance_id"))
        object.__setattr__(
            self, "worker_epoch",
            _require_positive_int(self.worker_epoch, "worker_epoch"))
        object.__setattr__(
            self, "state", _enum_from(self.state, WorkerLivenessState))
        ts = _require_ts(self.reported_at, "reported_at")
        if ts is None:
            raise ValueError("reported_at is required")
        object.__setattr__(self, "reported_at", ts)
        object.__setattr__(
            self, "heartbeat_seq",
            _require_positive_int(self.heartbeat_seq, "heartbeat_seq", allow_none=True))


# ---------------------------------------------------------------------------
# Serialization (deterministic, JSON-safe, secret-safe — same conventions as
# agent/runtime_contracts.py; no second incompatible format)
# ---------------------------------------------------------------------------

def _check_required(data, required, name):
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be a dict")
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"{name} missing required keys: {sorted(missing)}")


def to_dict(obj):
    """Deterministic JSON-safe dict for the worker-fabric contracts.

    The worker contracts contain NO payload fields (no input/output/metadata/
    details) — only immutable identity, capability, and liveness metadata — so
    secret redaction is vacuously satisfied. Serialization uses `redact=False`
    to preserve the frozen `RuntimeCapabilities` sub-contract bit-for-bit
    (frozen `_cap_to_dict` emits `supports_secrets` raw; redacting it would
    corrupt the boolean on round-trip). `_json_safe_copy(redact=False)` still
    enforces JSON-safety (rejects callables/bytes/non-finite values).
    """
    if isinstance(obj, WorkerCapabilities):
        return _json_safe_copy({
            "runtime_capabilities": None if obj.runtime_capabilities is None
                else _runtime_caps_to_dict(obj.runtime_capabilities),
            "tool_classes": list(obj.tool_classes),
            "max_cpu_cores": obj.max_cpu_cores,
            "max_memory_mb": obj.max_memory_mb,
            "architecture": obj.architecture,
            "network_policy": obj.network_policy,
            "region": obj.region,
            "compliance_boundary": obj.compliance_boundary,
            "runtime_version": obj.runtime_version,
        }, redact=False)
    if isinstance(obj, WorkerIdentity):
        return _json_safe_copy({
            "worker_id": obj.worker_id,
            "worker_instance_id": obj.worker_instance_id,
            "worker_epoch": obj.worker_epoch,
            "tenant_scope": list(obj.tenant_scope),
            "capabilities": None if obj.capabilities is None
                else to_dict(obj.capabilities),
            "isolation_mode": obj.isolation_mode.value,
            "transport_identity": obj.transport_identity,
        }, redact=False)
    if isinstance(obj, WorkerLiveness):
        return _json_safe_copy({
            "worker_id": obj.worker_id,
            "worker_instance_id": obj.worker_instance_id,
            "worker_epoch": obj.worker_epoch,
            "state": obj.state.value,
            "reported_at": obj.reported_at,
            "heartbeat_seq": obj.heartbeat_seq,
        }, redact=False)
    raise TypeError(f"unsupported worker contract: {type(obj).__name__}")


def _runtime_caps_to_dict(caps):
    """Serialize the frozen RuntimeCapabilities via its own public serializer
    (composition — the frozen contract is never re-serialized by a new format)."""
    from .runtime_contracts import to_dict as _rc_to_dict
    return _rc_to_dict(caps)


_REQUIRED_IDENTITY = ("worker_id", "worker_instance_id", "worker_epoch")
_REQUIRED_LIVENESS = ("worker_id", "worker_instance_id", "worker_epoch",
                      "state", "reported_at")


def from_dict(data, obj_type):
    """Reconstruct a worker-fabric contract from a dict (full validation)."""
    if obj_type is WorkerIdentity:
        _check_required(data, _REQUIRED_IDENTITY, "WorkerIdentity")
        caps = data.get("capabilities")
        return WorkerIdentity(
            worker_id=data["worker_id"],
            worker_instance_id=data["worker_instance_id"],
            worker_epoch=data["worker_epoch"],
            tenant_scope=data.get("tenant_scope", ()),
            capabilities=None if caps is None else from_dict(caps, WorkerCapabilities),
            isolation_mode=data.get("isolation_mode", "NONE"),
            transport_identity=data.get("transport_identity"))
    if obj_type is WorkerCapabilities:
        if not isinstance(data, dict):
            raise ValueError("WorkerCapabilities must be a dict")
        rc = data.get("runtime_capabilities")
        return WorkerCapabilities(
            runtime_capabilities=None if rc is None
                else _runtime_caps_from_dict(rc),
            tool_classes=data.get("tool_classes", ()),
            max_cpu_cores=data.get("max_cpu_cores"),
            max_memory_mb=data.get("max_memory_mb"),
            architecture=data.get("architecture"),
            network_policy=data.get("network_policy"),
            region=data.get("region"),
            compliance_boundary=data.get("compliance_boundary"),
            runtime_version=data.get("runtime_version"))
    if obj_type is WorkerLiveness:
        _check_required(data, _REQUIRED_LIVENESS, "WorkerLiveness")
        return WorkerLiveness(
            worker_id=data["worker_id"],
            worker_instance_id=data["worker_instance_id"],
            worker_epoch=data["worker_epoch"],
            state=_enum_from(data["state"], WorkerLivenessState),
            reported_at=data["reported_at"],
            heartbeat_seq=data.get("heartbeat_seq"))
    raise TypeError(f"unsupported worker contract type: {obj_type!r}")


def _runtime_caps_from_dict(data):
    """Reconstruct the frozen RuntimeCapabilities via its own public deserializer."""
    from .runtime_contracts import from_dict as _rc_from_dict
    return _rc_from_dict(data, RuntimeCapabilities)


def to_json(obj):
    """Deterministic canonical JSON (sorted keys, compact separators) —
    identical convention to runtime_contracts.to_json."""
    return json.dumps(to_dict(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def from_json(text, obj_type):
    """Reconstruct a worker-fabric contract from canonical JSON text."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("from_json requires a JSON string")
    return from_dict(json.loads(text), obj_type)
