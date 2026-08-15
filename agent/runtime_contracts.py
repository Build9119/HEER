"""Runtime Contracts (Phase 3.4.1) — portable seam between the Execution Engine and future Hermes runtime transports.

IT CONTAINS NO RUNTIME EXECUTION: no workers/threads/subprocess/containers/network,
no scheduler/retry/governance/lease logic, no SQLite, no eval/exec/dynamic imports.
HEER DECIDES. EE OWNS EXECUTION ATTEMPTS. HERMES EXECUTES.
"""
from __future__ import annotations

import json
import math
import types
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

__all__ = ["RuntimeResultStatus", "RuntimeErrorType", "RuntimeTransportKind",
           "RuntimeIsolation", "RuntimeCapability", "APPROVED_ERROR_TYPES",
           "RESULT_STATUS_VALUES", "RuntimeJob", "RuntimeRequest", "RuntimeResult",
           "RuntimeError", "RuntimeHandle", "RuntimeCapabilities", "to_dict",
           "from_dict", "to_json", "from_json"]


class RuntimeResultStatus(Enum):
    """Runtime-level outcomes only — NOT Phase 3.2 task states."""
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


APPROVED_ERROR_TYPES: tuple = ("TIMEOUT", "CRASH", "INVALID_RESULT", "AUTH_DENIED",
                               "GOVERNANCE_DENIED", "CAPACITY_LIMIT", "TRANSPORT", "UNKNOWN")
RESULT_STATUS_VALUES: tuple = tuple(s.value for s in RuntimeResultStatus)


class RuntimeErrorType(Enum):
    """Approved eight-category runtime error taxonomy (HEER_PHASE34 §4.4)."""
    TIMEOUT = "TIMEOUT"
    CRASH = "CRASH"
    INVALID_RESULT = "INVALID_RESULT"
    AUTH_DENIED = "AUTH_DENIED"
    GOVERNANCE_DENIED = "GOVERNANCE_DENIED"
    CAPACITY_LIMIT = "CAPACITY_LIMIT"
    TRANSPORT = "TRANSPORT"
    UNKNOWN = "UNKNOWN"


class RuntimeTransportKind(Enum):
    INPROCESS = "INPROCESS"
    SUBPROCESS = "SUBPROCESS"
    CONTAINER = "CONTAINER"
    REMOTE = "REMOTE"
    K8S = "K8S"


class RuntimeIsolation(Enum):
    NONE = "NONE"
    PROCESS = "PROCESS"
    CONTAINER = "CONTAINER"
    SANDBOX = "SANDBOX"


class RuntimeCapability(Enum):
    """Capabilities describe what a runtime CAN do — they NEVER grant authz."""
    CANCELLATION = "cancellation"
    HEARTBEAT = "heartbeat"
    STREAMING = "streaming"
    TIMEOUT = "timeout"
    SANDBOXING = "sandboxing"
    CHECKPOINTING = "checkpointing"


# ---------------------------------------------------------------------------
# Validation helpers (pure, deterministic)
# ---------------------------------------------------------------------------

def _require_id(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_str_opt(value, name):
    if value is None:
        return None
    return _require_id(value, name)


def _require_attempt_no(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"attempt_no must be a positive int, got {value!r}")
    return value


def _require_ts(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a numeric timestamp")
    ts = float(value)
    if not math.isfinite(ts):
        raise ValueError(f"{name} must be finite")
    return ts


def _require_positive_float(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number or None")
    f = float(value)
    if not (math.isfinite(f) and f > 0):
        raise ValueError(f"{name} must be > 0")
    return f


def _require_bool(value, name):
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be bool")
    return value


_SECRET_KEY_PARTS = ("secret", "token", "password", "passwd", "api_key", "apikey", "credential")


def _is_secret_key(key):
    return any(part in key.lower() for part in _SECRET_KEY_PARTS)


def _json_safe_copy(value, redact):
    """JSON-safe deep copy; rejects callables/bytes/sets; redacts secret keys."""
    if isinstance(value, Mapping):
        out = {}
        for key, val in value.items():
            key = key if isinstance(key, str) else str(key)
            if redact and _is_secret_key(key):
                out[key] = "[REDACTED]"
            else:
                out[key] = _json_safe_copy(val, redact)
        return out
    if isinstance(value, (list, tuple)):
        return [_json_safe_copy(v, redact) for v in value]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite float is not JSON-safe")
        return value
    if callable(value):
        raise ValueError("callables are not allowed in runtime contracts")
    if isinstance(value, (bytes, bytearray, set, frozenset)):
        raise ValueError(f"type not allowed: {type(value).__name__}")
    raise ValueError(f"type not allowed: {type(value).__name__}")


def _freeze_mapping(value, name):
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a dict-like mapping")
    safe = _json_safe_copy(dict(value), redact=False)
    if not isinstance(safe, dict):
        raise ValueError(f"{name} must serialize to a dict")
    return types.MappingProxyType(safe)


def _require_caps(value):
    if value is None:
        return None
    if not isinstance(value, RuntimeCapabilities):
        raise ValueError("capabilities must be RuntimeCapabilities or None")
    return value


def _enum_from(value, cls):
    if isinstance(value, cls):
        return value
    if isinstance(value, str):
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"invalid {cls.__name__} value: {value!r}") from None
    raise ValueError(f"{cls.__name__} requires string or enum member")


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RuntimeJob:
    """Immutable identity + metadata for one runtime dispatch. job_id == execution_id."""
    job_id: str
    execution_id: str
    mission_id: str
    task_id: str
    attempt_no: int
    input: Mapping[str, object]
    metadata: Mapping[str, object]
    timeout_sec: float | None
    correlation_id: str
    capabilities: RuntimeCapabilities | None = None
    cancel_token: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "job_id", _require_id(self.job_id, "job_id"))
        object.__setattr__(self, "execution_id", _require_id(self.execution_id, "execution_id"))
        if self.job_id != self.execution_id:
            raise ValueError("job_id must equal execution_id (canonical dedup identity)")
        object.__setattr__(self, "mission_id", _require_id(self.mission_id, "mission_id"))
        object.__setattr__(self, "task_id", _require_id(self.task_id, "task_id"))
        object.__setattr__(self, "attempt_no", _require_attempt_no(self.attempt_no))
        object.__setattr__(self, "input", _freeze_mapping(self.input, "input"))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata, "metadata"))
        object.__setattr__(self, "timeout_sec", _require_positive_float(self.timeout_sec, "timeout_sec"))
        object.__setattr__(self, "correlation_id", _require_id(self.correlation_id, "correlation_id"))
        object.__setattr__(self, "capabilities", _require_caps(self.capabilities))
        object.__setattr__(self, "cancel_token", _require_str_opt(self.cancel_token, "cancel_token"))


@dataclass(frozen=True, slots=True)
class RuntimeRequest:
    """Dispatch request; idempotency_key defaults to execution identity."""
    job: RuntimeJob
    requested_at: float
    requested_by: str
    capabilities_required: RuntimeCapabilities | None
    idempotency_key: str | None = None

    def __post_init__(self):
        if not isinstance(self.job, RuntimeJob):
            raise ValueError("job must be a RuntimeJob")
        object.__setattr__(self, "requested_at", _require_ts(self.requested_at, "requested_at"))
        object.__setattr__(self, "requested_by", _require_id(self.requested_by, "requested_by"))
        object.__setattr__(self, "capabilities_required", _require_caps(self.capabilities_required))
        key = self.idempotency_key if self.idempotency_key is not None else self.job.execution_id
        object.__setattr__(self, "idempotency_key", _require_id(key, "idempotency_key"))

    def is_duplicate_of(self, other):
        if not isinstance(other, RuntimeRequest):
            return False
        return (self.idempotency_key == other.idempotency_key
                and self.job.job_id == other.job.job_id
                and self.job.execution_id == other.job.execution_id)


@dataclass(frozen=True, slots=True)
class RuntimeError:
    """Structured error; retryable is DESCRIPTIVE only — EE decides retries."""
    error_type: RuntimeErrorType
    message: str
    retryable: bool = False
    execution_id: str | None = None
    job_id: str | None = None
    runtime_id: str | None = None
    correlation_id: str | None = None
    details: Mapping[str, object] | None = None

    def __post_init__(self):
        object.__setattr__(self, "error_type", _enum_from(self.error_type, RuntimeErrorType))
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be a non-empty string")
        object.__setattr__(self, "retryable", _require_bool(self.retryable, "retryable"))
        object.__setattr__(self, "execution_id", _require_str_opt(self.execution_id, "execution_id"))
        object.__setattr__(self, "job_id", _require_str_opt(self.job_id, "job_id"))
        object.__setattr__(self, "runtime_id", _require_str_opt(self.runtime_id, "runtime_id"))
        object.__setattr__(self, "correlation_id", _require_str_opt(self.correlation_id, "correlation_id"))
        object.__setattr__(self, "details", None if self.details is None
                           else _freeze_mapping(self.details, "details"))


@dataclass(frozen=True, slots=True)
class RuntimeResult:
    """Runtime-level result (NOT a task-state machine)."""
    execution_id: str
    job_id: str
    status: RuntimeResultStatus
    output: Mapping[str, object] | None = None
    error: RuntimeError | None = None
    started_at: float | None = None
    finished_at: float | None = None
    runtime_id: str | None = None
    worker_id: str | None = None
    correlation_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=lambda: {})

    def __post_init__(self):
        object.__setattr__(self, "execution_id", _require_id(self.execution_id, "execution_id"))
        object.__setattr__(self, "job_id", _require_id(self.job_id, "job_id"))
        object.__setattr__(self, "status", _enum_from(self.status, RuntimeResultStatus))
        if self.output is not None:
            object.__setattr__(self, "output", _freeze_mapping(self.output, "output"))
        if self.error is not None and not isinstance(self.error, RuntimeError):
            raise ValueError("error must be a RuntimeError or None")
        object.__setattr__(self, "started_at", _require_ts(self.started_at, "started_at"))
        object.__setattr__(self, "finished_at", _require_ts(self.finished_at, "finished_at"))
        if self.started_at is not None and self.finished_at is not None \
                and self.finished_at < self.started_at:
            raise ValueError("finished_at must be >= started_at")
        object.__setattr__(self, "runtime_id", _require_str_opt(self.runtime_id, "runtime_id"))
        object.__setattr__(self, "worker_id", _require_str_opt(self.worker_id, "worker_id"))
        object.__setattr__(self, "correlation_id", _require_str_opt(self.correlation_id, "correlation_id"))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata, "metadata"))


@dataclass(frozen=True, slots=True)
class RuntimeHandle:
    """Handle identity — NOT an EE lease; lease fields remain EE-owned."""
    handle_id: str
    execution_id: str
    runtime_id: str | None = None
    worker_id: str | None = None
    submitted_at: float | None = None

    def __post_init__(self):
        object.__setattr__(self, "handle_id", _require_id(self.handle_id, "handle_id"))
        object.__setattr__(self, "execution_id", _require_id(self.execution_id, "execution_id"))
        object.__setattr__(self, "runtime_id", _require_str_opt(self.runtime_id, "runtime_id"))
        object.__setattr__(self, "worker_id", _require_str_opt(self.worker_id, "worker_id"))
        object.__setattr__(self, "submitted_at", _require_ts(self.submitted_at, "submitted_at"))


@dataclass(frozen=True, slots=True)
class RuntimeCapabilities:
    """Typed runtime capabilities — capability only, NEVER authorization."""
    transport: RuntimeTransportKind
    isolation: RuntimeIsolation
    max_concurrency: int | None = None
    supports_heartbeat: bool = False
    supports_hard_timeout: bool = False
    supports_secrets: bool = False
    supports_tenant_isolation: bool = False
    features: frozenset = frozenset()

    def __post_init__(self):
        object.__setattr__(self, "transport", _enum_from(self.transport, RuntimeTransportKind))
        object.__setattr__(self, "isolation", _enum_from(self.isolation, RuntimeIsolation))
        if self.max_concurrency is not None:
            if isinstance(self.max_concurrency, bool) \
                    or not isinstance(self.max_concurrency, int) or self.max_concurrency < 1:
                raise ValueError("max_concurrency must be a positive int or None")
        object.__setattr__(self, "supports_heartbeat",
                           _require_bool(self.supports_heartbeat, "supports_heartbeat"))
        object.__setattr__(self, "supports_hard_timeout",
                           _require_bool(self.supports_hard_timeout, "supports_hard_timeout"))
        object.__setattr__(self, "supports_secrets",
                           _require_bool(self.supports_secrets, "supports_secrets"))
        object.__setattr__(self, "supports_tenant_isolation",
                           _require_bool(self.supports_tenant_isolation, "supports_tenant_isolation"))
        if isinstance(self.features, (list, tuple, set)):
            feats = frozenset(self.features)
            object.__setattr__(self, "features", feats)
        elif isinstance(self.features, frozenset):
            feats = self.features
        else:
            raise ValueError("features must be a frozenset of RuntimeCapability members")
        for f in feats:
            if not isinstance(f, RuntimeCapability):
                raise ValueError(f"invalid feature: {f!r} (must be RuntimeCapability)")


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _cap_to_dict(caps):
    return {
        "transport": caps.transport.value,
        "isolation": caps.isolation.value,
        "max_concurrency": caps.max_concurrency,
        "supports_heartbeat": caps.supports_heartbeat,
        "supports_hard_timeout": caps.supports_hard_timeout,
        "supports_secrets": caps.supports_secrets,
        "supports_tenant_isolation": caps.supports_tenant_isolation,
        "features": sorted(f.value for f in caps.features),
    }


def to_dict(obj):
    """Deterministic JSON-safe dict; secret-like keys redacted on serialization."""
    if isinstance(obj, RuntimeJob):
        return {
            "job_id": obj.job_id, "execution_id": obj.execution_id,
            "mission_id": obj.mission_id, "task_id": obj.task_id,
            "attempt_no": obj.attempt_no,
            "input": _json_safe_copy(dict(obj.input), redact=True),
            "metadata": _json_safe_copy(dict(obj.metadata), redact=True),
            "timeout_sec": obj.timeout_sec, "correlation_id": obj.correlation_id,
            "capabilities": None if obj.capabilities is None else _cap_to_dict(obj.capabilities),
            "cancel_token": obj.cancel_token,
        }
    if isinstance(obj, RuntimeRequest):
        return {
            "job": to_dict(obj.job), "requested_at": obj.requested_at,
            "requested_by": obj.requested_by,
            "capabilities_required": None if obj.capabilities_required is None
                                     else _cap_to_dict(obj.capabilities_required),
            "idempotency_key": obj.idempotency_key,
        }
    if isinstance(obj, RuntimeError):
        return {
            "error_type": obj.error_type.value, "message": obj.message,
            "retryable": obj.retryable, "execution_id": obj.execution_id,
            "job_id": obj.job_id, "runtime_id": obj.runtime_id,
            "correlation_id": obj.correlation_id,
            "details": None if obj.details is None
                       else _json_safe_copy(dict(obj.details), redact=True),
        }
    if isinstance(obj, RuntimeResult):
        return {
            "execution_id": obj.execution_id, "job_id": obj.job_id,
            "status": obj.status.value,
            "output": None if obj.output is None
                      else _json_safe_copy(dict(obj.output), redact=True),
            "error": None if obj.error is None else to_dict(obj.error),
            "started_at": obj.started_at, "finished_at": obj.finished_at,
            "runtime_id": obj.runtime_id, "worker_id": obj.worker_id,
            "correlation_id": obj.correlation_id,
            "metadata": _json_safe_copy(dict(obj.metadata), redact=True),
        }
    if isinstance(obj, RuntimeHandle):
        return {
            "handle_id": obj.handle_id, "execution_id": obj.execution_id,
            "runtime_id": obj.runtime_id, "worker_id": obj.worker_id,
            "submitted_at": obj.submitted_at,
        }
    if isinstance(obj, RuntimeCapabilities):
        return _cap_to_dict(obj)
    raise TypeError(f"unsupported runtime contract: {type(obj).__name__}")


def _caps_from_dict(data):
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError("capabilities must be a dict or None")
    return RuntimeCapabilities(
        transport=_enum_from(data.get("transport"), RuntimeTransportKind),
        isolation=_enum_from(data.get("isolation"), RuntimeIsolation),
        max_concurrency=data.get("max_concurrency"),
        supports_heartbeat=bool(data.get("supports_heartbeat", False)),
        supports_hard_timeout=bool(data.get("supports_hard_timeout", False)),
        supports_secrets=bool(data.get("supports_secrets", False)),
        supports_tenant_isolation=bool(data.get("supports_tenant_isolation", False)),
        features=frozenset(_enum_from(f, RuntimeCapability)
                           for f in data.get("features", ())),
    )


_REQUIRED_JOB = ("job_id", "execution_id", "mission_id", "task_id", "attempt_no", "correlation_id")
_REQUIRED_RESULT = ("execution_id", "job_id", "status")
_REQUIRED_ERROR = ("error_type", "message")
_REQUIRED_HANDLE = ("handle_id", "execution_id")
_REQUIRED_REQUEST = ("job", "requested_at", "requested_by")


def _check_required(data, required, name):
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be a dict")
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"{name} missing required keys: {sorted(missing)}")


def from_dict(data, obj_type):
    """Reconstruct a contract from a dict with full validation (object -> dict -> object)."""
    if obj_type is RuntimeJob:
        _check_required(data, _REQUIRED_JOB, "RuntimeJob")
        return RuntimeJob(
            job_id=data["job_id"], execution_id=data["execution_id"],
            mission_id=data["mission_id"], task_id=data["task_id"],
            attempt_no=data["attempt_no"], input=data.get("input", {}),
            metadata=data.get("metadata", {}), timeout_sec=data.get("timeout_sec"),
            correlation_id=data["correlation_id"],
            capabilities=_caps_from_dict(data.get("capabilities")),
            cancel_token=data.get("cancel_token"))
    if obj_type is RuntimeRequest:
        _check_required(data, _REQUIRED_REQUEST, "RuntimeRequest")
        job = from_dict(data["job"], RuntimeJob)
        if not isinstance(job, RuntimeJob):
            raise TypeError("RuntimeRequest.job must deserialize to RuntimeJob")
        return RuntimeRequest(
            job=job, requested_at=data["requested_at"],
            requested_by=data["requested_by"],
            capabilities_required=_caps_from_dict(data.get("capabilities_required")),
            idempotency_key=data.get("idempotency_key"))
    if obj_type is RuntimeError:
        _check_required(data, _REQUIRED_ERROR, "RuntimeError")
        return RuntimeError(
            error_type=_enum_from(data["error_type"], RuntimeErrorType),
            message=data["message"], retryable=bool(data.get("retryable", False)),
            execution_id=data.get("execution_id"), job_id=data.get("job_id"),
            runtime_id=data.get("runtime_id"), correlation_id=data.get("correlation_id"),
            details=data.get("details"))
    if obj_type is RuntimeResult:
        _check_required(data, _REQUIRED_RESULT, "RuntimeResult")
        err = data.get("error")
        if err is None:
            rerr = None
        else:
            rerr = from_dict(err, RuntimeError)
            if not isinstance(rerr, RuntimeError):
                raise TypeError("RuntimeResult.error must deserialize to RuntimeError")
        return RuntimeResult(
            execution_id=data["execution_id"], job_id=data["job_id"],
            status=_enum_from(data["status"], RuntimeResultStatus),
            output=data.get("output"),
            error=rerr,
            started_at=data.get("started_at"), finished_at=data.get("finished_at"),
            runtime_id=data.get("runtime_id"), worker_id=data.get("worker_id"),
            correlation_id=data.get("correlation_id"), metadata=data.get("metadata", {}))
    if obj_type is RuntimeHandle:
        _check_required(data, _REQUIRED_HANDLE, "RuntimeHandle")
        return RuntimeHandle(
            handle_id=data["handle_id"], execution_id=data["execution_id"],
            runtime_id=data.get("runtime_id"), worker_id=data.get("worker_id"),
            submitted_at=data.get("submitted_at"))
    if obj_type is RuntimeCapabilities:
        return _caps_from_dict(data)
    raise TypeError(f"unsupported runtime contract type: {obj_type!r}")


def to_json(obj):
    """Deterministic canonical JSON (sorted keys, compact separators)."""
    return json.dumps(to_dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def from_json(text, obj_type):
    """Reconstruct a contract from canonical JSON text."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("from_json requires a JSON string")
    return from_dict(json.loads(text), obj_type)


DEFAULT_CANCEL_PREFIX = "cfrm_"
DEFAULT_HANDLE_PREFIX = "hdl_"


def new_handle_id():
    return DEFAULT_HANDLE_PREFIX + uuid.uuid4().hex[:12]


def new_cancel_token():
    return DEFAULT_CANCEL_PREFIX + uuid.uuid4().hex[:12]
