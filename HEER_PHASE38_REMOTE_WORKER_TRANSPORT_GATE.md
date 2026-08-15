# HEER Phase 3.8 — Remote Worker Transport Architecture Gate

## Executive Verdict

**STATUS: BLOCKED — ARCHITECTURAL DECISIONS REQUIRED**

Phase 3.7 (SubprocessTransport) is VERIFIED AND FROZEN: 330/330 regression PASS, 30/30 Phase 3.7 PASS, 13/13 Phase 3.2 acceptance PASS, service HTTP 200, clean shutdown PASS.

Phase 3.8 has **NO approved implementation gate**. This document is the discovery/architecture gate for Phase 3.8 — it does not authorize implementation.

---

## Current Architecture

```
HEER (HTTP) → Mission Engine → Task Graph → Execution Engine → Hermes Adapter → Runtime Transport
                                                                        
                                                              [INPROCESS] HermesRuntime
                                                              [SUBPROCESS] SubprocessTransport
                                                              [REMOTE] RemoteWorkerTransport (Phase 3.8)
```

**Frozen Authority Boundaries:**
- **Execution Engine**: execution_id, attempts, leases, retries/backoff/max-attempts, cancellation policy, timeout policy, final persistence, task-state transitions, DAG scheduling
- **Hermes Adapter**: transport-agnostic mapping ONLY; zero EE writes, zero policy decisions
- **Runtime Transport** (HermesRuntime / SubprocessTransport): one authorized dispatch, cooperative invocation, outcome reporting, transport-local liveness, bounded handle recovery
- **Worker Fabric** (Phase 3.5/3.6): worker identity registration, capability reporting, placement, liveness — NEVER policy, NEVER authorizes

**Phase 3.7 Status:** SubprocessTransport is implemented and frozen. It provides process isolation via JSONL stdin/stdout IPC, worker identity/epoch verification at handshake, and transport outcome reporting.

---

## Existing Transport Seam

The actual interface connecting ExecutionEngine → HermesAdapter → Runtime/Transport:

### HermesAdapter Runtime Surface (agent/hermes_adapter.py)
```python
# Transport MUST expose:
capabilities() → RuntimeCapabilities
submit(RuntimeRequest) → RuntimeHandle
start(handle_id) → {"ok": bool, "execution_id": ..., "phase": ...}
cancel(handle_id) → {"ok": bool, "cooperative": bool}
terminate() → {"ok": bool}
heartbeat(handle_id) → {"ok": bool, "alive": bool, "phase": ..., "runtime_id": ..., "worker_id": ...}
status(handle_id) → {"ok": bool, "execution_id": ..., "phase": ..., "status": ...}
result(handle_id) → RuntimeResult | None
events(limit) → list[dict]
recover() → {"ok": bool, "checked": int, "recovered": list[execution_id]}
```

### RuntimeRequest / RuntimeResult Contracts (agent/runtime_contracts.py - frozen)
- **RuntimeJob**: job_id == execution_id (canonical dedup), mission_id, task_id, attempt_no, input, metadata (tool, execution_id, mission_id, task_id, attempt_no, worker_id, worker_instance_id, worker_epoch), timeout_sec, correlation_id, capabilities, cancel_token
- **RuntimeRequest**: job, requested_at, requested_by, capabilities_required, idempotency_key (defaults to execution_id)
- **RuntimeResult**: execution_id, job_id, status (SUCCEEDED/FAILED/CANCELLED/TIMED_OUT), output, error (RuntimeError), started_at, finished_at, runtime_id, worker_id, correlation_id, metadata
- **RuntimeError**: error_type (8-category: TIMEOUT, CRASH, INVALID_RESULT, AUTH_DENIED, GOVERNANCE_DENIED, CAPACITY_LIMIT, TRANSPORT, UNKNOWN), message, retryable (descriptive only), correlation fields

### Adapter invoke() Flow (agent/hermes_adapter.py:178-224)
1. `build_request()` → frozen RuntimeRequest (idempotency_key = execution_id)
2. `runtime.submit(req)` → RuntimeHandle
3. `runtime.start(handle_id)` → QUEUED → RUNNING
4. Poll `runtime.result(handle_id)` with:
   - `cancel_check()` → runtime.cancel(handle_id) (cooperative)
   - `engine_heartbeat()` → renews EE lease (throttled)
   - `runtime.recover()` → idempotent crash escalation on stall
5. `map_result()` → tools.call_tool-shaped dict for EE worker CAS logic

**Critical invariant:** If transport never finalizes within timeout + hard_stop_grace, adapter returns `{"ok": False, "runtime_stalled": True}` and EE worker treats it as "do NOT touch EE state" — EE lease sweep remains single recovery authority.

---

## Worker Identity

Actual fields currently used (from agent/worker_contracts.py, worker_registry.py, subprocess_transport.py):

| Field | Source | Mutability | Semantics |
|-------|--------|------------|-----------|
| `worker_id` | WorkerIdentity | immutable | Canonical public identity (e.g., `w-*`, matching EE lease owners). Globally unique. |
| `worker_instance_id` | WorkerIdentity | immutable per-spawn | One value per process/container spawn; regenerated on restart. Detects worker restart. |
| `worker_epoch` | WorkerIdentity | immutable per-registration | Monotonically increasing; restarted worker = NEW instance + NEW epoch. Old epoch is stale. |
| `tenant_scope` | WorkerIdentity | immutable per registration | List of tenant IDs the worker may serve. Ownership enforcement stays in EE/control plane. |
| `capabilities` | WorkerIdentity.capabilities (WorkerCapabilities) | mutable at registration | Descriptive only: `tool_classes`, `runtime_capabilities` (RuntimeCapabilities), `architecture`, `isolation_mode`, `resource_limits`. NEVER authorization. |
| `isolation_mode` | WorkerIdentity | immutable per spawn | NONE / PROCESS / CONTAINER / SANDBOX (RuntimeIsolation enum) |
| `transport_identity` | WorkerIdentity | immutable | Transport-level identity for control messaging (today: runtime_id; future: per-transport credential) |
| `liveness/state` | WorkerRegistry | mutable (fabric-local) | REGISTERED / LIVE / STALE / DEPARTED — fabric-local, NEVER an EE lease |
| `heartbeat_seq` | WorkerRegistry | monotonic counter | Ordering guard for heartbeats; timestamps recorded, not used for ordering |

**Registry operations (worker_registry.py):** `register()`, `heartbeat()`, `mark_stale()`, `depart()`, `get()`, `list()`, `list_by_capability()`, `status()`. All tenant-scoped. Single RLock. In-memory only — no persistence.

---

## Remote Transport Requirements

**ONLY requirements explicitly supported by existing Phase 3.4/3.5/3.6 documents:**

From **HEER_PHASE34_HERMES_GATE.md §11 (Deployment Options Evaluation)**:
- Remote worker service (Option E): network + OS isolation, high latency, moderate reliability, good security (mTLS), higher complexity, mid-high cost, good observability, network complexity for recovery, horizontal scalability, moderate DX
- **Staged evolution recommendation**: A (in-process) → B/C (subprocess/container) → D/E (remote/K8s) **only when real fleet scale or multi-host HA is required**
- Premature K8s/remote is rejected: "HEER is a single-machine SQLite app; distributed infrastructure now adds more failure modes than value"

From **HEER_PHASE35_WORKER_FABRIC_GATE.md §13 (Deployment Evolution)**:
- Stage D (Remote worker): network + OS, high latency, network partitions, higher ops complexity, good (mTLS), horizontal scalability, mid-high cost, transport switch; **no EE change**
- **Recommended path: A → B → C → D → E → F → G, gated on evidence**
- Premature Kubernetes/remote rejected explicitly

From **HEER_PHASE35_WORKER_FABRIC_GATE.md §14 (Transport Abstraction)**:
- All deployment stages (A–G) preserve frozen contracts: `RuntimeRequest`, `RuntimeResult`, `RuntimeHandle`, `RuntimeCapabilities` already carry required fields (`transport`, `isolation`, `runtime_id`, `worker_id`, `features`, eight `RuntimeErrorType` values)
- **Verification**: "no incompatibility found. The seam is transport-agnostic by design"

From **HEER_PHASE35_WORKER_FABRIC_GATE.md §17 (Architecture Options)**:
- Option D (Centralized remote worker service): "requires a network service; carries auth/mTLS/HA complexity; no EE change" — **deferred (3.8) until multi-host needed**
- Option E (Queue-based worker fabric): "adds a queue/broker dependency; HEER is single-writer SQLite; queue adds more failure modes than value now" — **rejected for now**
- Option F (Kubernetes-native): "best fleet management but highest ops burden; premature for current single-machine scale" — **rejected for now**

From **HEER_PHASE36_WORKER_DISPATCH_GATE.md** (worker identity/epoch verification):
- SubprocessTransport handshake validates: `worker_id`, `worker_instance_id`, `worker_epoch`, `tenant_id`, `nonce` against WorkerRegistry — **fail closed**

**Explicitly REQUIRED for remote (from gates):**
1. Same `RuntimeTransport` surface as SubprocessTransport (submit/start/cancel/heartbeat/status/result/terminate/recover)
2. `RuntimeCapabilities.transport = RuntimeTransportKind.REMOTE`
3. Identity/epoch/nonce verification at handshake (like SubprocessTransport)
4. Tenant scope validation against WorkerRegistry
5. Cooperative cancellation via transport channel
6. Transport-local heartbeat (not EE lease)
7. Idempotency via `execution_id` (job_id == idempotency_key)
8. Terminal result correlation to EE-authorized execution_id

---

## Security / Trust Gap

| Capability | Currently EXISTS | Currently MISSING |
|------------|------------------|-------------------|
| **Authentication** | SubprocessTransport: handshake validates worker_id/instance_id/epoch/nonce against WorkerRegistry | Remote: NO mutual TLS, NO transport-layer auth, NO credential model for remote workers, NO attestation depth defined (§22 Q2 open) |
| **Authorization** | EE is sole authorizer (approvals L0-L3, tool allowlist, attempt claim); transport is fail-closed (GOVERNANCE_DENIED) | Remote: NO additional authz boundary defined; transport must not bypass HEER governance |
| **Worker Identity** | WorkerIdentity (worker_id, instance_id, epoch, tenant_scope, capabilities) registered in WorkerRegistry | Remote: NO signed registration, NO credential binding to instance_id+epoch, NO spoofing prevention implemented |
| **Attestation/Trust** | Conceptual only (§3 "Spoofing prevention (conceptual)") | Remote: NO implementation, NO threat model for remote, NO clock-skew bounds for epoch across hosts (§22 Q3 open) |
| **Tenant Isolation** | WorkerRegistry queries are tenant-scoped; SubprocessTransport validates tenant_id at handshake | Remote: NO cross-tenant network isolation, NO per-tenant secret namespaces, NO per-tenant resource pools implemented |
| **Transport Security** | SubprocessTransport: local process, no network | Remote: NO mTLS, NO channel encryption, NO replay protection beyond idempotency_key, NO transport-level auth |
| **Replay Protection** | idempotency_key == execution_id at transport level; EE claim-CAS is single gate into RUNNING | Remote: NO explicit nonce/challenge beyond SubprocessTransport's transport_nonce; NO carrier-level dedup defined |
| **Result Validation** | EE validates RuntimeResult.output; malformed → INVALID_RESULT (no transition) | Remote: Same contract applies, but NO transport-layer integrity/checksum defined |

**Critical Gaps (from HEER_PHASE35_WORKER_FABRIC_GATE.md §22 Open Questions):**
1. Worker registration state persistence: in-memory vs future additive table (left open)
2. Attestation depth for subprocess vs container vs remote (TBD Phase 3.6 threat modeling)
3. Clock-skew bounds for worker_epoch across hosts (requires Phase 3.8 network design)
4. Remote transport identity boundary for business_id-scoped tools beyond tenant_scope (open)

---

## Execution Authority

**MUST remain exclusively owned by ExecutionEngine (invariants I1–I17, frozen):**

| Authority | Owner | Must NOT Move To Transport |
|-----------|-------|---------------------------|
| execution_id creation | EE | — |
| attempt lifecycle / attempt_no | EE | — |
| leases (lease_owner, lease_expires_at, claim/reclaim) | EE | — |
| retry policy / backoff / max_attempts / `_schedule_retry` CAS | EE | — |
| task state transitions (READY/RUNNING/COMPLETED/FAILED/BLOCKED/CANCELLED) | EE | — |
| cancellation policy / `cancel_requested` | EE | — |
| timeout policy (task_timeout, mission_timeout, hard kill) | EE | — |
| final execution persistence (SQLite executions table) | EE | — |
| DAG scheduling / `ready_tasks()` / mission state | EE + Task Graph + Mission Engine | — |
| tool allowlist / governance / approvals L0-L3 | EE + Tools + Approvals | — |
| audit persistence (`audit.record` + `execution_events`) | EE | — |

**RemoteWorkerTransport owns ONLY (per architectural rule):**
- Remote connection lifecycle
- Request delivery (with idempotency_key = execution_id)
- Response delivery
- Transport-local timeout (not EE timeout policy)
- Protocol validation
- Identity validation (worker_id/instance_id/epoch/nonce/tenant)
- Worker epoch validation
- Connection failure handling
- Transport events (additive to EE audit)
- Cleanup

**MUST NOT introduce:** distributed scheduler, retry engine, lease engine, second execution state machine, new authorization framework, message broker, Kubernetes, containers, service mesh, new event store.

---

## Phase 3.8 Blockers

**Every unresolved architectural question that must be answered before implementation:**

1. **Worker Registration Persistence** (HEER_PHASE35 §22 Q1): Where does worker registration state live long-term? In-memory fabric registry vs future additive table — no answer invented.

2. **Attestation Depth** (HEER_PHASE35 §22 Q2): What attestation depth is required for remote workers? TBD by Phase 3.6 threat modeling — not done.

3. **Clock-Skew Bounds** (HEER_PHASE35 §22 Q3): What are the exact clock-skew bounds for `worker_epoch` across hosts in remote stages? Requires Phase 3.8 network design — not done.

4. **Remote Identity Boundary** (HEER_PHASE35 §22 Q7): Do future remote transports require a separate worker-side identity boundary for `business_id`-scoped tools beyond `tenant_scope`? Open.

5. **Transport Security Model**: No mTLS design, no credential model, no channel encryption, no mutual auth defined for remote transport.

6. **Network Failure Semantics**: Phase 3.5 §8 models network partition (lease expiry drives recovery), but no remote-specific timeout/retry/backoff policy defined for the transport layer.

7. **Remote Worker Lifecycle**: How does a remote worker register, heartbeat, and depart across network boundaries? SubprocessTransport uses local process + IPC; remote needs a protocol.

8. **Tenant Isolation at Network Layer**: No per-tenant network policy, no cross-tenant traffic isolation, no per-tenant secret injection model for remote.

9. **Capacity/Backpressure**: Remote transport needs explicit queue depth limits, flow control, and rejection semantics (CAPACITY_LIMIT) — not defined.

10. **Observability Correlation**: Remote transport must emit correlated events (mission_id → task_id → execution_id → attempt_no → runtime_id → worker_id → correlation_id) — protocol not defined.

11. **Governance Check Hook**: SubprocessTransport has `governance_check: Callable[[RuntimeRequest], bool]` — remote needs equivalent but over network.

---

## Decision

**BLOCKED — ARCHITECTURAL DECISIONS REQUIRED**

Phase 3.8 cannot proceed to design or implementation until the blockers above are resolved. Specifically:

- No approved Phase 3.8 architecture gate exists (this document IS the gate discovery)
- Critical security/trust primitives for remote workers are missing (attestation, mTLS, credential model)
- Network failure semantics, clock-skew bounds, and remote worker lifecycle are undefined
- Tenant isolation at network layer is not designed
- Worker registration persistence question (Phase 3.5 §22 Q1) remains open

**Required before Phase 3.8 design can begin:**
1. Phase 3.6 threat modeling to define attestation depth for remote workers
2. Phase 3.8 network design to establish clock-skew bounds for epoch
3. Explicit decision on worker registration persistence (in-memory vs DB)
4. Transport security model (mTLS, credentials, channel encryption)
5. Remote worker registration/heartbeat/depart protocol design
6. Cross-tenant network isolation policy

---

PHASE 3.8 ACTION 0C — COMPLETE
STATUS: BLOCKED — ARCHITECTURAL DECISIONS REQUIRED