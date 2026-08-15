"""Remote Worker Transport Contracts (Phase 3.8A) — immutable, JSON-safe contract layer for
the Remote Worker Transport (RWT) in Phase 3.8.

SCOPE: CONTRACTS ONLY. This module contains no transport implementation:
no HTTP client/server, no TLS/mTLS logic, no queue management, no network I/O,
no async/await, no background tasks, no subprocess/container/remote execution,
no service discovery, no broker, no database.

Authority boundaries (frozen — HEER_PHASE38_ARCHITECTURE_OWNER_DECISIONS.md D1-D10):
  Execution Engine retains sole authority for:
    - execution_id
    - attempt lifecycle (attempt_no)
    - task lifecycle (PENDING/READY/RUNNING/COMPLETED/FAILED/BLOCKED/CANCELLED)
    - leases / lease expiry (lease_owner, lease_expires_at)
    - retry policy / exponential backoff / max attempts
    - cancellation policy / timeout policy
    - final persistence authority (SQLite, audit, execution_events)
    - DAG scheduling and task assignment
    - tool governance and authorization (L0-L3 approvals, allowlists)
    - capacity limits and concurrency control

  RemoteWorkerTransport (NEW for Phase 3.8) owns:
    - Registration/heartbeat/departure transport
    - Request/result delivery over bounded queue
    - mTLS connection lifecycle
    - JSONL event emission
    - Worker identity validation (epoch, instance_id, tenant_scope)
    - Transport failure handling
    - Bounded queue + EE pull model

  RemoteWorkerTransport MUST NOT own:
    - execution_id creation
    - attempt creation
    - retry policy
    - task state transitions
    - leases
    - DAG scheduling
    - authorization / governance decisions
    - final persistence

Worker capabilities remain DESCRIPTIVE ONLY — never authorization (D10).
tenant_scope remains a hard isolation boundary (D4, D7).
Registry-authoritative epoch assignment (D3).
mTLS with control-plane CA (D2, D5).
"""
from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import uuid

from .worker_contracts import (
    WorkerCapabilities,
    WorkerIdentity,
    WorkerLiveness,
    WorkerLivenessState,
    to_dict as _worker_to_dict,
    from_dict as _worker_from_dict,
)
from .runtime_contracts import (
    RuntimeCapabilities,
    RuntimeError,
    RuntimeErrorType,
    RuntimeHandle,
    RuntimeIsolation,
    RuntimeJob,
    RuntimeRequest,
    RuntimeResult,
    RuntimeResultStatus,
    RuntimeTransportKind,
    to_dict as _runtime_to_dict,
    from_dict as _runtime_from_dict,
)

__all__ = [
    # Enums
    "RemoteWorkerEventType",
    "RemoteWorkerTransportState",
    "RemoteWorkerProtocolVersion",
    # Contracts
    "RemoteWorkerConfig",
    "RemoteWorkerConnection",
    "RemoteWorkerRegistrationRequest",
    "RemoteWorkerRegistrationResponse",
    "RemoteWorkerHeartbeatRequest",
    "RemoteWorkerHeartbeatResponse",
    "RemoteWorkerDepartureRequest",
    "RemoteWorkerDepartureResponse",
    "RemoteWorkerJobRequest",
    "RemoteWorkerJobResponse",
    "RemoteWorkerResultDelivery",
    "RemoteWorkerEvent",
    "RemoteWorkerQueueStatus",
    # Serialization
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RemoteWorkerEventType(Enum):
    """JSONL event types for observability correlation (D9)."""
    REGISTRATION = "REGISTRATION"
    HEARTBEAT = "HEARTBEAT"
    DEPARTURE = "DEPARTURE"
    REQUEST_DELIVERY = "REQUEST_DELIVERY"
    RESULT_DELIVERY = "RESULT_DELIVERY"
    ERROR = "ERROR"
    CAPACITY_LIMIT = "CAPACITY_LIMIT"
    CONNECTION_ESTABLISHED = "CONNECTION_ESTABLISHED"
    CONNECTION_CLOSED = "CONNECTION_CLOSED"
    EPOCH_ASSIGNED = "EPOCH_ASSIGNED"
    TENANT_BOUND = "TENANT_BOUND"


class RemoteWorkerTransportState(Enum):
    """Transport connection lifecycle states."""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    REGISTERING = "REGISTERING"
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    CLOSED = "CLOSED"


class RemoteWorkerProtocolVersion(Enum):
    """Supported protocol versions."""
    V1 = "v1"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _require_id(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_str_opt(value, name):
    if value is None:
        return None
    return _require_id(value, name)


def _require_positive_int(value, name, *, allow_none=False):
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive int")
    return value


def _require_nonnegative_int(value, name, *, allow_none=False):
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative int")
    return value


def _require_float(value, name, *, allow_none=False):
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a numeric value")
    f = float(value)
    if not (f == f and f != float('inf') and f != float('-inf')):  # NaN/Inf check
        raise ValueError(f"{name} must be finite")
    return f


def _require_bool(value, name):
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be bool")
    return value


def _require_str_tuple(value, name):
    """Normalize to a sorted, deduplicated, immutable tuple of non-empty strings."""
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be an iterable of strings, not a string")
    if not isinstance(value, (list, tuple, set)):
        raise ValueError(f"{name} must be an iterable of strings")
    out = []
    for entry in value:
        if isinstance(entry, bool) or not isinstance(entry, str) or not entry.strip():
            raise ValueError(f"{name} entries must be non-empty strings")
        out.append(entry)
    return tuple(sorted(set(out)))


def _require_mapping(value, name):
    if value is None:
        return types.MappingProxyType({})
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return types.MappingProxyType(dict(value))


import types


# ---------------------------------------------------------------------------
# Transport Configuration Contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RemoteWorkerConfig:
    """Immutable configuration for RemoteWorkerTransport.
    
    This is a pure configuration contract — no behavior, no network I/O.
    All values are validated on construction.
    """
    # Control plane endpoint (HTTPS with mTLS)
    control_plane_url: str
    
    # TLS/mTLS configuration
    client_cert_path: str
    client_key_path: str
    ca_cert_path: str
    
    # Worker identity
    worker_id: str
    worker_instance_id: str
    tenant_scope: tuple = field(default_factory=tuple)
    
    # Transport behavior
    protocol_version: RemoteWorkerProtocolVersion = RemoteWorkerProtocolVersion.V1
    connection_timeout_sec: float = 30.0
    request_timeout_sec: float = 60.0
    heartbeat_interval_sec: float = 10.0
    max_reconnect_attempts: int = 5
    reconnect_base_delay_sec: float = 2.0
    reconnect_max_delay_sec: float = 60.0
    
    # Queue/backpressure (D8)
    max_queue_depth: int = 100
    queue_full_behavior: str = "reject"  # "reject" | "evict_oldest"
    
    # Event emission (D9)
    event_buffer_size: int = 1000
    event_flush_interval_sec: float = 1.0
    
    # TLS verification
    verify_hostname: bool = True
    min_tls_version: str = "1.2"
    
    def __post_init__(self):
        object.__setattr__(self, "control_plane_url", _require_id(self.control_plane_url, "control_plane_url"))
        object.__setattr__(self, "client_cert_path", _require_id(self.client_cert_path, "client_cert_path"))
        object.__setattr__(self, "client_key_path", _require_id(self.client_key_path, "client_key_path"))
        object.__setattr__(self, "ca_cert_path", _require_id(self.ca_cert_path, "ca_cert_path"))
        object.__setattr__(self, "worker_id", _require_id(self.worker_id, "worker_id"))
        object.__setattr__(self, "worker_instance_id", _require_id(self.worker_instance_id, "worker_instance_id"))
        object.__setattr__(self, "tenant_scope", _require_str_tuple(self.tenant_scope, "tenant_scope"))
        
        if not isinstance(self.protocol_version, RemoteWorkerProtocolVersion):
            raise ValueError("protocol_version must be RemoteWorkerProtocolVersion")
        
        object.__setattr__(self, "connection_timeout_sec", _require_float(self.connection_timeout_sec, "connection_timeout_sec"))
        object.__setattr__(self, "request_timeout_sec", _require_float(self.request_timeout_sec, "request_timeout_sec"))
        object.__setattr__(self, "heartbeat_interval_sec", _require_float(self.heartbeat_interval_sec, "heartbeat_interval_sec"))
        object.__setattr__(self, "max_reconnect_attempts", _require_positive_int(self.max_reconnect_attempts, "max_reconnect_attempts"))
        object.__setattr__(self, "reconnect_base_delay_sec", _require_float(self.reconnect_base_delay_sec, "reconnect_base_delay_sec"))
        object.__setattr__(self, "reconnect_max_delay_sec", _require_float(self.reconnect_max_delay_sec, "reconnect_max_delay_sec"))
        object.__setattr__(self, "max_queue_depth", _require_positive_int(self.max_queue_depth, "max_queue_depth"))
        
        if self.queue_full_behavior not in ("reject", "evict_oldest"):
            raise ValueError("queue_full_behavior must be 'reject' or 'evict_oldest'")
        
        object.__setattr__(self, "event_buffer_size", _require_positive_int(self.event_buffer_size, "event_buffer_size"))
        object.__setattr__(self, "event_flush_interval_sec", _require_float(self.event_flush_interval_sec, "event_flush_interval_sec"))
        object.__setattr__(self, "verify_hostname", _require_bool(self.verify_hostname, "verify_hostname"))
        object.__setattr__(self, "min_tls_version", _require_id(self.min_tls_version, "min_tls_version"))


# ---------------------------------------------------------------------------
# Connection Contract
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RemoteWorkerConnection:
    """Immutable connection state snapshot — no live sockets, no I/O.
    
    This is a correlation-only contract for observability and debugging.
    The actual connection lifecycle is managed by the transport implementation.
    """
    connection_id: str
    state: RemoteWorkerTransportState
    remote_endpoint: str
    worker_id: str
    worker_instance_id: str
    worker_epoch: int | None
    tenant_scope: tuple
    established_at: float | None
    last_activity_at: float | None
    bytes_sent: int
    bytes_received: int
    request_count: int
    error_count: int
    protocol_version: RemoteWorkerProtocolVersion
    tls_cipher: str | None
    tls_version: str | None
    
    def __post_init__(self):
        object.__setattr__(self, "connection_id", _require_id(self.connection_id, "connection_id"))
        if not isinstance(self.state, RemoteWorkerTransportState):
            raise ValueError("state must be RemoteWorkerTransportState")
        object.__setattr__(self, "remote_endpoint", _require_id(self.remote_endpoint, "remote_endpoint"))
        object.__setattr__(self, "worker_id", _require_id(self.worker_id, "worker_id"))
        object.__setattr__(self, "worker_instance_id", _require_id(self.worker_instance_id, "worker_instance_id"))
        object.__setattr__(self, "worker_epoch", _require_positive_int(self.worker_epoch, "worker_epoch", allow_none=True))
        object.__setattr__(self, "tenant_scope", _require_str_tuple(self.tenant_scope, "tenant_scope"))
        object.__setattr__(self, "established_at", _require_float(self.established_at, "established_at", allow_none=True))
        object.__setattr__(self, "last_activity_at", _require_float(self.last_activity_at, "last_activity_at", allow_none=True))
        object.__setattr__(self, "bytes_sent", _require_nonnegative_int(self.bytes_sent, "bytes_sent"))
        object.__setattr__(self, "bytes_received", _require_nonnegative_int(self.bytes_received, "bytes_received"))
        object.__setattr__(self, "request_count", _require_nonnegative_int(self.request_count, "request_count"))
        object.__setattr__(self, "error_count", _require_nonnegative_int(self.error_count, "error_count"))
        if not isinstance(self.protocol_version, RemoteWorkerProtocolVersion):
            raise ValueError("protocol_version must be RemoteWorkerProtocolVersion")
        object.__setattr__(self, "tls_cipher", _require_str_opt(self.tls_cipher, "tls_cipher"))
        object.__setattr__(self, "tls_version", _require_str_opt(self.tls_version, "tls_version"))


# ---------------------------------------------------------------------------
# Registration Protocol Contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RemoteWorkerRegistrationRequest:
    """Worker registration request sent to control plane (D6).
    
    This is the HTTP POST /workers/register payload.
    """
    worker_identity: WorkerIdentity
    client_certificate_fingerprint: str
    capabilities: RuntimeCapabilities
    protocol_version: RemoteWorkerProtocolVersion = RemoteWorkerProtocolVersion.V1
    requested_epoch: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not isinstance(self.worker_identity, WorkerIdentity):
            raise ValueError("worker_identity must be WorkerIdentity")
        object.__setattr__(self, "client_certificate_fingerprint", _require_id(self.client_certificate_fingerprint, "client_certificate_fingerprint"))
        if not isinstance(self.capabilities, RuntimeCapabilities):
            raise ValueError("capabilities must be RuntimeCapabilities")
        if not isinstance(self.protocol_version, RemoteWorkerProtocolVersion):
            raise ValueError("protocol_version must be RemoteWorkerProtocolVersion")
        object.__setattr__(self, "requested_epoch", _require_positive_int(self.requested_epoch, "requested_epoch", allow_none=True))
        object.__setattr__(self, "metadata", _require_mapping(self.metadata, "metadata"))


@dataclass(frozen=True, slots=True)
class RemoteWorkerRegistrationResponse:
    """Control plane registration response (D6, D3).
    
    Contains the registry-assigned worker_epoch (D3).
    """
    success: bool
    worker_epoch: int | None = None
    worker_identity: WorkerIdentity | None = None
    error_code: str | None = None
    error_message: str | None = None
    assigned_capabilities: RuntimeCapabilities | None = None
    server_timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        object.__setattr__(self, "success", _require_bool(self.success, "success"))
        object.__setattr__(self, "worker_epoch", _require_positive_int(self.worker_epoch, "worker_epoch", allow_none=True))
        if self.worker_identity is not None and not isinstance(self.worker_identity, WorkerIdentity):
            raise ValueError("worker_identity must be WorkerIdentity or None")
        object.__setattr__(self, "error_code", _require_str_opt(self.error_code, "error_code"))
        object.__setattr__(self, "error_message", _require_str_opt(self.error_message, "error_message"))
        if self.assigned_capabilities is not None and not isinstance(self.assigned_capabilities, RuntimeCapabilities):
            raise ValueError("assigned_capabilities must be RuntimeCapabilities or None")
        object.__setattr__(self, "server_timestamp", _require_float(self.server_timestamp, "server_timestamp"))


# ---------------------------------------------------------------------------
# Heartbeat Protocol Contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RemoteWorkerHeartbeatRequest:
    """Worker heartbeat request (D6).
    
    This is the HTTP POST /workers/heartbeat payload.
    """
    worker_id: str
    worker_instance_id: str
    worker_epoch: int
    heartbeat_seq: int
    reported_at: float
    state: WorkerLivenessState
    metadata: Mapping[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        object.__setattr__(self, "worker_id", _require_id(self.worker_id, "worker_id"))
        object.__setattr__(self, "worker_instance_id", _require_id(self.worker_instance_id, "worker_instance_id"))
        object.__setattr__(self, "worker_epoch", _require_positive_int(self.worker_epoch, "worker_epoch"))
        object.__setattr__(self, "heartbeat_seq", _require_positive_int(self.heartbeat_seq, "heartbeat_seq"))
        object.__setattr__(self, "reported_at", _require_float(self.reported_at, "reported_at"))
        if not isinstance(self.state, WorkerLivenessState):
            raise ValueError("state must be WorkerLivenessState")
        object.__setattr__(self, "metadata", _require_mapping(self.metadata, "metadata"))


@dataclass(frozen=True, slots=True)
class RemoteWorkerHeartbeatResponse:
    """Control plane heartbeat response (D6)."""
    success: bool
    worker_epoch: int
    next_heartbeat_interval_sec: float | None = None
    error_code: str | None = None
    error_message: str | None = None
    server_timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        object.__setattr__(self, "success", _require_bool(self.success, "success"))
        object.__setattr__(self, "worker_epoch", _require_positive_int(self.worker_epoch, "worker_epoch"))
        object.__setattr__(self, "next_heartbeat_interval_sec", _require_float(self.next_heartbeat_interval_sec, "next_heartbeat_interval_sec", allow_none=True))
        object.__setattr__(self, "error_code", _require_str_opt(self.error_code, "error_code"))
        object.__setattr__(self, "error_message", _require_str_opt(self.error_message, "error_message"))
        object.__setattr__(self, "server_timestamp", _require_float(self.server_timestamp, "server_timestamp"))


# ---------------------------------------------------------------------------
# Departure Protocol Contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RemoteWorkerDepartureRequest:
    """Worker departure request (D6).
    
    This is the HTTP POST /workers/depart payload.
    """
    worker_id: str
    worker_instance_id: str
    worker_epoch: int
    reason: str = "graceful"
    metadata: Mapping[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        object.__setattr__(self, "worker_id", _require_id(self.worker_id, "worker_id"))
        object.__setattr__(self, "worker_instance_id", _require_id(self.worker_instance_id, "worker_instance_id"))
        object.__setattr__(self, "worker_epoch", _require_positive_int(self.worker_epoch, "worker_epoch"))
        object.__setattr__(self, "reason", _require_id(self.reason, "reason"))
        object.__setattr__(self, "metadata", _require_mapping(self.metadata, "metadata"))


@dataclass(frozen=True, slots=True)
class RemoteWorkerDepartureResponse:
    """Control plane departure response (D6)."""
    success: bool
    worker_epoch: int
    error_code: str | None = None
    error_message: str | None = None
    server_timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        object.__setattr__(self, "success", _require_bool(self.success, "success"))
        object.__setattr__(self, "worker_epoch", _require_positive_int(self.worker_epoch, "worker_epoch"))
        object.__setattr__(self, "error_code", _require_str_opt(self.error_code, "error_code"))
        object.__setattr__(self, "error_message", _require_str_opt(self.error_message, "error_message"))
        object.__setattr__(self, "server_timestamp", _require_float(self.server_timestamp, "server_timestamp"))


# ---------------------------------------------------------------------------
# Job Request/Result Delivery Contracts
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RemoteWorkerJobRequest:
    """Job request delivered to remote worker (D6, D8).
    
    This wraps the frozen RuntimeRequest with transport metadata.
    EE submits this to transport; transport delivers to worker.
    """
    runtime_request: RuntimeRequest
    transport_handle_id: str
    delivery_deadline: float | None = None
    correlation_id: str | None = None
    
    def __post_init__(self):
        if not isinstance(self.runtime_request, RuntimeRequest):
            raise ValueError("runtime_request must be RuntimeRequest")
        object.__setattr__(self, "transport_handle_id", _require_id(self.transport_handle_id, "transport_handle_id"))
        object.__setattr__(self, "delivery_deadline", _require_float(self.delivery_deadline, "delivery_deadline", allow_none=True))
        object.__setattr__(self, "correlation_id", _require_str_opt(self.correlation_id, "correlation_id"))


@dataclass(frozen=True, slots=True)
class RemoteWorkerJobResponse:
    """Worker's synchronous response to job request (acknowledgment)."""
    success: bool
    transport_handle_id: str
    error_code: str | None = None
    error_message: str | None = None
    server_timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        object.__setattr__(self, "success", _require_bool(self.success, "success"))
        object.__setattr__(self, "transport_handle_id", _require_id(self.transport_handle_id, "transport_handle_id"))
        object.__setattr__(self, "error_code", _require_str_opt(self.error_code, "error_code"))
        object.__setattr__(self, "error_message", _require_str_opt(self.error_message, "error_message"))
        object.__setattr__(self, "server_timestamp", _require_float(self.server_timestamp, "server_timestamp"))


@dataclass(frozen=True, slots=True)
class RemoteWorkerResultDelivery:
    """Result delivered from worker back to EE (D6, D8).
    
    This wraps the frozen RuntimeResult with transport metadata.
    Worker produces this; transport delivers to EE.
    """
    runtime_result: RuntimeResult
    transport_handle_id: str
    worker_instance_id: str
    worker_epoch: int
    correlation_id: str | None = None
    
    def __post_init__(self):
        if not isinstance(self.runtime_result, RuntimeResult):
            raise ValueError("runtime_result must be RuntimeResult")
        object.__setattr__(self, "transport_handle_id", _require_id(self.transport_handle_id, "transport_handle_id"))
        object.__setattr__(self, "worker_instance_id", _require_id(self.worker_instance_id, "worker_instance_id"))
        object.__setattr__(self, "worker_epoch", _require_positive_int(self.worker_epoch, "worker_epoch"))
        object.__setattr__(self, "correlation_id", _require_str_opt(self.correlation_id, "correlation_id"))


# ---------------------------------------------------------------------------
# Observability Event Contract (D9)
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RemoteWorkerEvent:
    """JSONL event for observability correlation (D9).
    
    All events include execution_id for traceability.
    Format matches SubprocessTransport JSONL convention.
    """
    event_id: str
    event_type: RemoteWorkerEventType
    timestamp: float
    execution_id: str | None = None
    worker_id: str | None = None
    worker_instance_id: str | None = None
    worker_epoch: int | None = None
    tenant_scope: tuple = field(default_factory=tuple)
    correlation_id: str | None = None
    attempt_no: int | None = None
    task_id: str | None = None
    mission_id: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        object.__setattr__(self, "event_id", _require_id(self.event_id, "event_id"))
        if not isinstance(self.event_type, RemoteWorkerEventType):
            raise ValueError("event_type must be RemoteWorkerEventType")
        object.__setattr__(self, "timestamp", _require_float(self.timestamp, "timestamp"))
        object.__setattr__(self, "execution_id", _require_str_opt(self.execution_id, "execution_id"))
        object.__setattr__(self, "worker_id", _require_str_opt(self.worker_id, "worker_id"))
        object.__setattr__(self, "worker_instance_id", _require_str_opt(self.worker_instance_id, "worker_instance_id"))
        object.__setattr__(self, "worker_epoch", _require_positive_int(self.worker_epoch, "worker_epoch", allow_none=True))
        object.__setattr__(self, "tenant_scope", _require_str_tuple(self.tenant_scope, "tenant_scope"))
        object.__setattr__(self, "correlation_id", _require_str_opt(self.correlation_id, "correlation_id"))
        object.__setattr__(self, "attempt_no", _require_positive_int(self.attempt_no, "attempt_no", allow_none=True))
        object.__setattr__(self, "task_id", _require_str_opt(self.task_id, "task_id"))
        object.__setattr__(self, "mission_id", _require_str_opt(self.mission_id, "mission_id"))
        object.__setattr__(self, "payload", _require_mapping(self.payload, "payload"))


# ---------------------------------------------------------------------------
# Queue Status Contract (D8)
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RemoteWorkerQueueStatus:
    """Bounded queue status for backpressure signaling (D8)."""
    worker_id: str
    worker_instance_id: str
    worker_epoch: int
    current_depth: int
    max_depth: int
    is_full: bool
    oldest_request_age_sec: float | None = None
    newest_request_age_sec: float | None = None
    total_enqueued: int = 0
    total_dequeued: int = 0
    total_rejected: int = 0
    total_evicted: int = 0
    
    def __post_init__(self):
        object.__setattr__(self, "worker_id", _require_id(self.worker_id, "worker_id"))
        object.__setattr__(self, "worker_instance_id", _require_id(self.worker_instance_id, "worker_instance_id"))
        object.__setattr__(self, "worker_epoch", _require_positive_int(self.worker_epoch, "worker_epoch"))
        object.__setattr__(self, "current_depth", _require_nonnegative_int(self.current_depth, "current_depth"))
        object.__setattr__(self, "max_depth", _require_positive_int(self.max_depth, "max_depth"))
        object.__setattr__(self, "is_full", _require_bool(self.is_full, "is_full"))
        object.__setattr__(self, "oldest_request_age_sec", _require_float(self.oldest_request_age_sec, "oldest_request_age_sec", allow_none=True))
        object.__setattr__(self, "newest_request_age_sec", _require_float(self.newest_request_age_sec, "newest_request_age_sec", allow_none=True))
        object.__setattr__(self, "total_enqueued", _require_nonnegative_int(self.total_enqueued, "total_enqueued"))
        object.__setattr__(self, "total_dequeued", _require_nonnegative_int(self.total_dequeued, "total_dequeued"))
        object.__setattr__(self, "total_rejected", _require_nonnegative_int(self.total_rejected, "total_rejected"))
        object.__setattr__(self, "total_evicted", _require_nonnegative_int(self.total_evicted, "total_evicted"))


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def _remote_event_type_to_str(value):
    if isinstance(value, RemoteWorkerEventType):
        return value.value
    return value


def _remote_transport_state_to_str(value):
    if isinstance(value, RemoteWorkerTransportState):
        return value.value
    return value


def _remote_protocol_version_to_str(value):
    if isinstance(value, RemoteWorkerProtocolVersion):
        return value.value
    return value


def _worker_liveness_state_to_str(value):
    if isinstance(value, WorkerLivenessState):
        return value.value
    return value


def _runtime_caps_to_dict(caps):
    """Serialize RuntimeCapabilities via its own serializer."""
    return _runtime_to_dict(caps)


def _worker_caps_to_dict(caps):
    """Serialize WorkerCapabilities via worker_contracts serializer."""
    return _worker_to_dict(caps)


def _worker_identity_to_dict(identity):
    """Serialize WorkerIdentity via worker_contracts serializer."""
    return _worker_to_dict(identity)


def _runtime_request_to_dict(req):
    """Serialize RuntimeRequest via runtime_contracts serializer."""
    return _runtime_to_dict(req)


def _runtime_result_to_dict(result):
    """Serialize RuntimeResult via runtime_contracts serializer."""
    return _runtime_to_dict(result)


def to_dict(obj):
    """Deterministic JSON-safe dict for RemoteWorkerTransport contracts."""
    if isinstance(obj, RemoteWorkerConfig):
        return {
            "control_plane_url": obj.control_plane_url,
            "client_cert_path": obj.client_cert_path,
            "client_key_path": obj.client_key_path,
            "ca_cert_path": obj.ca_cert_path,
            "worker_id": obj.worker_id,
            "worker_instance_id": obj.worker_instance_id,
            "tenant_scope": list(obj.tenant_scope),
            "protocol_version": _remote_protocol_version_to_str(obj.protocol_version),
            "connection_timeout_sec": obj.connection_timeout_sec,
            "request_timeout_sec": obj.request_timeout_sec,
            "heartbeat_interval_sec": obj.heartbeat_interval_sec,
            "max_reconnect_attempts": obj.max_reconnect_attempts,
            "reconnect_base_delay_sec": obj.reconnect_base_delay_sec,
            "reconnect_max_delay_sec": obj.reconnect_max_delay_sec,
            "max_queue_depth": obj.max_queue_depth,
            "queue_full_behavior": obj.queue_full_behavior,
            "event_buffer_size": obj.event_buffer_size,
            "event_flush_interval_sec": obj.event_flush_interval_sec,
            "verify_hostname": obj.verify_hostname,
            "min_tls_version": obj.min_tls_version,
        }
    if isinstance(obj, RemoteWorkerConnection):
        return {
            "connection_id": obj.connection_id,
            "state": _remote_transport_state_to_str(obj.state),
            "remote_endpoint": obj.remote_endpoint,
            "worker_id": obj.worker_id,
            "worker_instance_id": obj.worker_instance_id,
            "worker_epoch": obj.worker_epoch,
            "tenant_scope": list(obj.tenant_scope),
            "established_at": obj.established_at,
            "last_activity_at": obj.last_activity_at,
            "bytes_sent": obj.bytes_sent,
            "bytes_received": obj.bytes_received,
            "request_count": obj.request_count,
            "error_count": obj.error_count,
            "protocol_version": _remote_protocol_version_to_str(obj.protocol_version),
            "tls_cipher": obj.tls_cipher,
            "tls_version": obj.tls_version,
        }
    if isinstance(obj, RemoteWorkerRegistrationRequest):
        return {
            "worker_identity": _worker_identity_to_dict(obj.worker_identity),
            "client_certificate_fingerprint": obj.client_certificate_fingerprint,
            "capabilities": _runtime_caps_to_dict(obj.capabilities),
            "protocol_version": _remote_protocol_version_to_str(obj.protocol_version),
            "requested_epoch": obj.requested_epoch,
            "metadata": dict(obj.metadata),
        }
    if isinstance(obj, RemoteWorkerRegistrationResponse):
        return {
            "success": obj.success,
            "worker_epoch": obj.worker_epoch,
            "worker_identity": _worker_identity_to_dict(obj.worker_identity) if obj.worker_identity else None,
            "error_code": obj.error_code,
            "error_message": obj.error_message,
            "assigned_capabilities": _runtime_caps_to_dict(obj.assigned_capabilities) if obj.assigned_capabilities else None,
            "server_timestamp": obj.server_timestamp,
        }
    if isinstance(obj, RemoteWorkerHeartbeatRequest):
        return {
            "worker_id": obj.worker_id,
            "worker_instance_id": obj.worker_instance_id,
            "worker_epoch": obj.worker_epoch,
            "heartbeat_seq": obj.heartbeat_seq,
            "reported_at": obj.reported_at,
            "state": _worker_liveness_state_to_str(obj.state),
            "metadata": dict(obj.metadata),
        }
    if isinstance(obj, RemoteWorkerHeartbeatResponse):
        return {
            "success": obj.success,
            "worker_epoch": obj.worker_epoch,
            "next_heartbeat_interval_sec": obj.next_heartbeat_interval_sec,
            "error_code": obj.error_code,
            "error_message": obj.error_message,
            "server_timestamp": obj.server_timestamp,
        }
    if isinstance(obj, RemoteWorkerDepartureRequest):
        return {
            "worker_id": obj.worker_id,
            "worker_instance_id": obj.worker_instance_id,
            "worker_epoch": obj.worker_epoch,
            "reason": obj.reason,
            "metadata": dict(obj.metadata),
        }
    if isinstance(obj, RemoteWorkerDepartureResponse):
        return {
            "success": obj.success,
            "worker_epoch": obj.worker_epoch,
            "error_code": obj.error_code,
            "error_message": obj.error_message,
            "server_timestamp": obj.server_timestamp,
        }
    if isinstance(obj, RemoteWorkerJobRequest):
        return {
            "runtime_request": _runtime_request_to_dict(obj.runtime_request),
            "transport_handle_id": obj.transport_handle_id,
            "delivery_deadline": obj.delivery_deadline,
            "correlation_id": obj.correlation_id,
        }
    if isinstance(obj, RemoteWorkerJobResponse):
        return {
            "success": obj.success,
            "transport_handle_id": obj.transport_handle_id,
            "error_code": obj.error_code,
            "error_message": obj.error_message,
            "server_timestamp": obj.server_timestamp,
        }
    if isinstance(obj, RemoteWorkerResultDelivery):
        return {
            "runtime_result": _runtime_result_to_dict(obj.runtime_result),
            "transport_handle_id": obj.transport_handle_id,
            "worker_instance_id": obj.worker_instance_id,
            "worker_epoch": obj.worker_epoch,
            "correlation_id": obj.correlation_id,
        }
    if isinstance(obj, RemoteWorkerEvent):
        return {
            "event_id": obj.event_id,
            "event_type": _remote_event_type_to_str(obj.event_type),
            "timestamp": obj.timestamp,
            "execution_id": obj.execution_id,
            "worker_id": obj.worker_id,
            "worker_instance_id": obj.worker_instance_id,
            "worker_epoch": obj.worker_epoch,
            "tenant_scope": list(obj.tenant_scope),
            "correlation_id": obj.correlation_id,
            "attempt_no": obj.attempt_no,
            "task_id": obj.task_id,
            "mission_id": obj.mission_id,
            "payload": dict(obj.payload),
        }
    if isinstance(obj, RemoteWorkerQueueStatus):
        return {
            "worker_id": obj.worker_id,
            "worker_instance_id": obj.worker_instance_id,
            "worker_epoch": obj.worker_epoch,
            "current_depth": obj.current_depth,
            "max_depth": obj.max_depth,
            "is_full": obj.is_full,
            "oldest_request_age_sec": obj.oldest_request_age_sec,
            "newest_request_age_sec": obj.newest_request_age_sec,
            "total_enqueued": obj.total_enqueued,
            "total_dequeued": obj.total_dequeued,
            "total_rejected": obj.total_rejected,
            "total_evicted": obj.total_evicted,
        }
    raise TypeError(f"unsupported remote worker transport contract: {type(obj).__name__}")


def _enum_from_str(value, cls):
    if isinstance(value, cls):
        return value
    if isinstance(value, str):
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"invalid {cls.__name__} value: {value!r}") from None
    raise ValueError(f"{cls.__name__} requires string or enum member")


def _runtime_caps_from_dict(data):
    return _runtime_from_dict(data, RuntimeCapabilities)


def _worker_caps_from_dict(data):
    return _worker_from_dict(data, WorkerCapabilities)


def _worker_identity_from_dict(data):
    return _worker_from_dict(data, WorkerIdentity)


def _runtime_request_from_dict(data):
    return _runtime_from_dict(data, RuntimeRequest)


def _runtime_result_from_dict(data):
    return _runtime_from_dict(data, RuntimeResult)


def from_dict(data, obj_type):
    """Reconstruct a RemoteWorkerTransport contract from a dict with full validation."""
    if obj_type is RemoteWorkerConfig:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerConfig must be a dict")
        return RemoteWorkerConfig(
            control_plane_url=data["control_plane_url"],
            client_cert_path=data["client_cert_path"],
            client_key_path=data["client_key_path"],
            ca_cert_path=data["ca_cert_path"],
            worker_id=data["worker_id"],
            worker_instance_id=data["worker_instance_id"],
            tenant_scope=tuple(data.get("tenant_scope", ())),
            protocol_version=_enum_from_str(data.get("protocol_version", "v1"), RemoteWorkerProtocolVersion),
            connection_timeout_sec=data.get("connection_timeout_sec", 30.0),
            request_timeout_sec=data.get("request_timeout_sec", 60.0),
            heartbeat_interval_sec=data.get("heartbeat_interval_sec", 10.0),
            max_reconnect_attempts=data.get("max_reconnect_attempts", 5),
            reconnect_base_delay_sec=data.get("reconnect_base_delay_sec", 2.0),
            reconnect_max_delay_sec=data.get("reconnect_max_delay_sec", 60.0),
            max_queue_depth=data.get("max_queue_depth", 100),
            queue_full_behavior=data.get("queue_full_behavior", "reject"),
            event_buffer_size=data.get("event_buffer_size", 1000),
            event_flush_interval_sec=data.get("event_flush_interval_sec", 1.0),
            verify_hostname=data.get("verify_hostname", True),
            min_tls_version=data.get("min_tls_version", "1.2"),
        )
    if obj_type is RemoteWorkerConnection:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerConnection must be a dict")
        return RemoteWorkerConnection(
            connection_id=data["connection_id"],
            state=_enum_from_str(data["state"], RemoteWorkerTransportState),
            remote_endpoint=data["remote_endpoint"],
            worker_id=data["worker_id"],
            worker_instance_id=data["worker_instance_id"],
            worker_epoch=data.get("worker_epoch"),
            tenant_scope=tuple(data.get("tenant_scope", ())),
            established_at=data.get("established_at"),
            last_activity_at=data.get("last_activity_at"),
            bytes_sent=data.get("bytes_sent", 0),
            bytes_received=data.get("bytes_received", 0),
            request_count=data.get("request_count", 0),
            error_count=data.get("error_count", 0),
            protocol_version=_enum_from_str(data.get("protocol_version", "v1"), RemoteWorkerProtocolVersion),
            tls_cipher=data.get("tls_cipher"),
            tls_version=data.get("tls_version"),
        )
    if obj_type is RemoteWorkerRegistrationRequest:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerRegistrationRequest must be a dict")
        return RemoteWorkerRegistrationRequest(
            worker_identity=_worker_identity_from_dict(data["worker_identity"]),
            client_certificate_fingerprint=data["client_certificate_fingerprint"],
            capabilities=_runtime_caps_from_dict(data["capabilities"]),
            protocol_version=_enum_from_str(data.get("protocol_version", "v1"), RemoteWorkerProtocolVersion),
            requested_epoch=data.get("requested_epoch"),
            metadata=data.get("metadata", {}),
        )
    if obj_type is RemoteWorkerRegistrationResponse:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerRegistrationResponse must be a dict")
        return RemoteWorkerRegistrationResponse(
            success=data["success"],
            worker_epoch=data.get("worker_epoch"),
            worker_identity=_worker_identity_from_dict(data["worker_identity"]) if data.get("worker_identity") else None,
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            assigned_capabilities=_runtime_caps_from_dict(data["assigned_capabilities"]) if data.get("assigned_capabilities") else None,
            server_timestamp=data.get("server_timestamp", time.time()),
        )
    if obj_type is RemoteWorkerHeartbeatRequest:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerHeartbeatRequest must be a dict")
        return RemoteWorkerHeartbeatRequest(
            worker_id=data["worker_id"],
            worker_instance_id=data["worker_instance_id"],
            worker_epoch=data["worker_epoch"],
            heartbeat_seq=data["heartbeat_seq"],
            reported_at=data["reported_at"],
            state=_enum_from_str(data["state"], WorkerLivenessState),
            metadata=data.get("metadata", {}),
        )
    if obj_type is RemoteWorkerHeartbeatResponse:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerHeartbeatResponse must be a dict")
        return RemoteWorkerHeartbeatResponse(
            success=data["success"],
            worker_epoch=data["worker_epoch"],
            next_heartbeat_interval_sec=data.get("next_heartbeat_interval_sec"),
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            server_timestamp=data.get("server_timestamp", time.time()),
        )
    if obj_type is RemoteWorkerDepartureRequest:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerDepartureRequest must be a dict")
        return RemoteWorkerDepartureRequest(
            worker_id=data["worker_id"],
            worker_instance_id=data["worker_instance_id"],
            worker_epoch=data["worker_epoch"],
            reason=data["reason"],
            metadata=data.get("metadata", {}),
        )
    if obj_type is RemoteWorkerDepartureResponse:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerDepartureResponse must be a dict")
        return RemoteWorkerDepartureResponse(
            success=data["success"],
            worker_epoch=data["worker_epoch"],
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            server_timestamp=data.get("server_timestamp", time.time()),
        )
    if obj_type is RemoteWorkerJobRequest:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerJobRequest must be a dict")
        return RemoteWorkerJobRequest(
            runtime_request=_runtime_request_from_dict(data["runtime_request"]),
            transport_handle_id=data["transport_handle_id"],
            delivery_deadline=data.get("delivery_deadline"),
            correlation_id=data.get("correlation_id"),
        )
    if obj_type is RemoteWorkerJobResponse:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerJobResponse must be a dict")
        return RemoteWorkerJobResponse(
            success=data["success"],
            transport_handle_id=data["transport_handle_id"],
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            server_timestamp=data.get("server_timestamp", time.time()),
        )
    if obj_type is RemoteWorkerResultDelivery:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerResultDelivery must be a dict")
        return RemoteWorkerResultDelivery(
            runtime_result=_runtime_result_from_dict(data["runtime_result"]),
            transport_handle_id=data["transport_handle_id"],
            worker_instance_id=data["worker_instance_id"],
            worker_epoch=data["worker_epoch"],
            correlation_id=data.get("correlation_id"),
        )
    if obj_type is RemoteWorkerEvent:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerEvent must be a dict")
        return RemoteWorkerEvent(
            event_id=data["event_id"],
            event_type=_enum_from_str(data["event_type"], RemoteWorkerEventType),
            timestamp=data["timestamp"],
            execution_id=data.get("execution_id"),
            worker_id=data.get("worker_id"),
            worker_instance_id=data.get("worker_instance_id"),
            worker_epoch=data.get("worker_epoch"),
            tenant_scope=tuple(data.get("tenant_scope", ())),
            correlation_id=data.get("correlation_id"),
            attempt_no=data.get("attempt_no"),
            task_id=data.get("task_id"),
            mission_id=data.get("mission_id"),
            payload=data.get("payload", {}),
        )
    if obj_type is RemoteWorkerQueueStatus:
        if not isinstance(data, dict):
            raise ValueError("RemoteWorkerQueueStatus must be a dict")
        return RemoteWorkerQueueStatus(
            worker_id=data["worker_id"],
            worker_instance_id=data["worker_instance_id"],
            worker_epoch=data["worker_epoch"],
            current_depth=data["current_depth"],
            max_depth=data["max_depth"],
            is_full=data["is_full"],
            oldest_request_age_sec=data.get("oldest_request_age_sec"),
            newest_request_age_sec=data.get("newest_request_age_sec"),
            total_enqueued=data.get("total_enqueued", 0),
            total_dequeued=data.get("total_dequeued", 0),
            total_rejected=data.get("total_rejected", 0),
            total_evicted=data.get("total_evicted", 0),
        )
    raise TypeError(f"unsupported remote worker transport contract type: {obj_type!r}")


def to_json(obj):
    """Deterministic canonical JSON (sorted keys, compact separators)."""
    return json.dumps(to_dict(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def from_json(text, obj_type):
    """Reconstruct a contract from canonical JSON text."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("from_json requires a JSON string")
    return from_dict(json.loads(text), obj_type)


# ---------------------------------------------------------------------------
# Helper functions for event generation
# ---------------------------------------------------------------------------

import uuid

def new_event_id() -> str:
    """Generate a new unique event ID."""
    return f"evt_{uuid.uuid4().hex[:16]}"


def new_connection_id() -> str:
    """Generate a new unique connection ID."""
    return f"conn_{uuid.uuid4().hex[:16]}"


def new_transport_handle_id() -> str:
    """Generate a new unique transport handle ID."""
    return f"hdl_{uuid.uuid4().hex[:16]}"