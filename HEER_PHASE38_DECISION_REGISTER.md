# HEER Phase 3.8 — Remote Worker Transport Architectural Decision Register

**Repository:** /Users/delit/JARVIS/jarvis  
**Source Phases:** 3.4 (Hermes), 3.5 (Worker Fabric), 3.6 (Worker Dispatch), 3.7 (SubprocessTransport — frozen)  
**Action:** 1 — Convert Phase 3.8 Blockers into Formal Decision Register  
**Status:** DECISIONS RESOLVED — ALL D1–D10 EXPLICIT  
**Mode:** DECISION ENTRY. Recording Architecture Owner selections for D1–D10. No production code modified.

---

## Decision Register Table

| ID | Decision | Existing Contract / Evidence | Current Assumption | What Is Explicitly Defined (FACT) | What Is Undefined (GAP) | Risk If Implemented Without Decision | Recommended Decision Needed from Architecture Owner | Blocks Implementation? |
|----|----------|------------------------------|-------------------|-----------------------------------|-------------------------|--------------------------------------|-----------------------------------------------------|------------------------|
| **D1** | **Worker Registration Persistence** | Phase 3.5 `worker_registry.py`: in-memory dict + RLock; no DB schema. Phase 3.5 §22 Q1: "Left open — no answer invented." Phase 3.8 §11 Blocker 1. | Registry survives process restarts; worker identities durable. | • In-memory `REGISTERED/LIVE/STALE/DEPARTED` states (Phase 3.5 §3)<br>• `worker_id`, `worker_instance_id`, `worker_epoch`, `tenant_scope` immutable per registration (Phase 3.5 `WorkerIdentity`)<br>• `heartbeat_seq` monotonic counter (Phase 3.5 `WorkerLiveness`)<br>• Re-registration on restart = new `instance_id` + new `epoch` (Phase 3.5 §3) | • Persistence layer (DB table vs file vs external)<br>• Durability guarantees (WAL, replication)<br>• Recovery of registry state on control-plane restart<br>• Schema for additive table (if chosen)<br>• TTL / GC policy for stale entries | • Worker identity loss on control-plane restart<br>• Duplicate `worker_id` re-registration races<br>• Stale workers not cleaned up → dispatch pollution<br>• No audit trail of registration history | **RESOLVED: Option 2 — Additive SQLite table.** Schema mirrors `WorkerIdentity` + `WorkerLiveness` fields, WAL mode, single-writer (registry), migration path from empty. | **NO** |
| **D2** | **Remote Worker Attestation Depth** | Phase 3.5 §3: "Spoofing prevention (conceptual)" only. Phase 3.5 §22 Q2: "TBD by Phase 3.6 threat modeling." Phase 3.6 §7: "Worker-reported capabilities are potentially untrusted... The gate must not pretend attestation exists." Phase 3.6 §24 Q1: "Attestation model (or explicit 'never')." Phase 3.8 §11 Blocker 2. | Self-claimed identity sufficient (as in SubprocessTransport handshake against local registry). | • `WorkerIdentity` fields: `worker_id`, `worker_instance_id`, `worker_epoch`, `tenant_scope` (Phase 3.5 `worker_contracts.py`)<br>• SubprocessTransport validates against local `WorkerRegistry` at handshake (Phase 3.7)<br>• `transport_identity` field reserved for future per-transport credential (Phase 3.5 `WorkerIdentity`)<br>• Capability is descriptive, never authorization (Phase 3.5 I10, Phase 3.6 I3) | • Cryptographic attestation model (mTLS, signed JWT, SPIFFE, TPM, etc.)<br>• Attestation depth per isolation mode (SUBPROCESS vs CONTAINER vs REMOTE vs K8S)<br>• Credential binding to `worker_instance_id + epoch`<br>• Verification authority (who signs? CA? control plane?)<br>• Revocation / rotation model<br>• Trust anchor distribution | • Remote worker spoofing → unauthorized dispatch selection<br>• Capability forgery → misplacement (though never authorizes)<br>• No cryptographic proof of worker provenance<br>• Compromised worker exfiltration (Phase 3.5 Risk #8) | **RESOLVED: Option 1 — mTLS with control-plane CA.** Certs issued per `worker_instance_id + epoch`; control plane is CA; rotation on re-registration. Uses stdlib `ssl`. | **NO** |
| **D3** | **Worker Epoch / Clock-Skew Semantics** | Phase 3.5 §3: `worker_epoch` monotonically increasing per registration; new spawn = new epoch. Phase 3.5 §22 Q3: "Requires Phase 3.8 network design." Phase 3.6 §8: "selection must bind to exact `(worker_id, instance_id, epoch)` triple; newer epoch supersedes." Phase 3.8 §11 Blocker 3. | Single-host monotonic time sufficient; epochs never conflict across hosts. | • `worker_epoch`: positive int, immutable per registration (Phase 3.5 `WorkerIdentity`)<br>• New process/container spawn = new `instance_id` + new `epoch` (Phase 3.5 §3)<br>• Registry rejects duplicate epoch (Phase 3.5 `worker_registry.py`)<br>• `heartbeat_seq`: monotonic counter for ordering (Phase 3.5 `WorkerLiveness`)<br>• Deterministic ordering: first-eligible by `worker_id` (Phase 3.6 `DispatchOrdering`) | • Maximum allowed clock skew between control plane and remote workers<br>• Epoch comparison semantics under skew (wall-clock vs logical)<br>• Whether `worker_epoch` is wall-clock timestamp or logical counter<br>• Stale-epoch detection window across network partitions<br>• Re-registration race: two hosts claiming same `worker_id` with different epochs | • Split-brain: two remote workers register same `worker_id` with conflicting epochs<br>• Stale epoch accepted → zombie worker selected<br>• Clock drift causes epoch inversion → wrong worker selected<br>• Lease/heartbeat timeout miscalculation due to skew | **RESOLVED: Option 4 — Registry-authoritative epoch.** Registry assigns epoch on registration; workers cannot self-assign. Eliminates races. | **NO** |
| **D4** | **business_id-Scoped Identity Boundary** | Phase 3.5 §22 Q7: "Open." Phase 3.6 §6: "Job tenant context: does not exist today... OPEN ARCHITECTURAL QUESTION." Phase 3.6 §17: "Job tenant scope: does not exist on missions/tasks/executions — OPEN." Phase 3.8 §11 Blocker 4. | `tenant_scope` in `WorkerIdentity` sufficient; no separate business_id boundary needed. | • `WorkerIdentity.tenant_scope`: tuple[str] immutable per registration (Phase 3.5)<br>• Registry queries tenant-scoped (Phase 3.5 `worker_registry.py`)<br>• `RuntimeRequest` carries no tenant field (Phase 3.4 `runtime_contracts.py`)<br>• `business_id` exists only at mission level via `mission_engine` (Phase 3.3)<br>• Tools receive `business_id` via `call_tool(..., business_id=biz)` (Phase 3.3 EE) | • Propagation of `business_id` / `tenant_id` from mission → execution → RuntimeRequest<br>• Whether worker needs separate identity boundary for `business_id`-scoped tools beyond `tenant_scope`<br>• Cross-tenant shared worker model (Phase 3.6 §17: "OPEN")<br>• Platform tenant semantics (Phase 3.6 §17: "none today — OPEN") | • Cross-tenant tool execution via shared worker<br>• Secret leakage across business_id boundaries<br>• Audit correlation broken (no business_id in execution chain)<br>• Governance bypass: tool allowlist scoped to business_id not enforced at dispatch | **RESOLVED: Option 1 — Propagate `business_id` as `tenant_id` in `RuntimeRequest.metadata` + `DispatchConstraints`.** Minimal change; reuses existing `tenant_scope` filter. | **NO** |
| **D5** | **Transport Security Model** | Phase 3.4 §7: "secrets never in args; vault-resolved references only; logs redacted." Phase 3.5 §10: "Conceptual control" for forged identity (signed registration, mutual auth). Phase 3.5 §11: "Transport TLS (future)." Phase 3.7 SubprocessTransport: local IPC, no network. Phase 3.8 §Security/Trust Gap: "Remote: NO mutual TLS, NO transport-layer auth, NO credential model, NO channel encryption, NO replay protection beyond idempotency_key." Phase 3.8 §11 Blocker 5. | Local process isolation (SubprocessTransport) is security model; remote adds nothing new. | • `RuntimeCapabilities.supports_secrets: bool` (Phase 3.4)<br>• `_is_secret_key()` redaction on serialization (Phase 3.4)<br>• `RuntimeErrorType.AUTH_DENIED`, `GOVERNANCE_DENIED`, `TRANSPORT` (Phase 3.4)<br>• SubprocessTransport handshake validates `worker_id/instance_id/epoch/tenant_id/nonce` against local registry (Phase 3.7)<br>• `governance_check: Callable[[RuntimeRequest], bool]` fail-closed (Phase 3.7) | • Mutual TLS design (cert issuance, rotation, verification)<br>• Transport-layer authentication (mTLS, SPIFFE, OIDC, API keys)<br>• Channel encryption (TLS 1.3, Noise, WireGuard)<br>• Replay protection beyond `idempotency_key` (nonce, sequence numbers)<br>• Credential model for remote workers (cert, token, key)<br>• Transport-level authorization (distinct from EE governance) | • Man-in-the-middle: request/result interception<br>• Worker impersonation: spoofed `worker_id` accepted<br>• Replay attacks: duplicate execution via captured traffic<br>• Data exfiltration: tool input/output in cleartext<br>• No audit of transport-layer auth decisions | **RESOLVED: Option 1 — mTLS with control-plane CA.** Certs per `worker_instance_id + epoch`; stdlib `ssl`; cert rotation on re-registration. | **NO** |
| **D6** | **Remote Registration / Heartbeat / Departure Protocol** | Phase 3.5 `worker_registry.py`: `register()`, `heartbeat()`, `mark_stale()`, `depart()`, `get()`, `list()`, `status()`. Phase 3.7 SubprocessTransport: local handshake at spawn validates against registry. Phase 3.8 §11 Blocker 7: "SubprocessTransport uses local process + IPC; remote needs a protocol." | Registry operations work over network as-is; no new protocol needed. | • Registry operations: register/heartbeat/mark_stale/depart (Phase 3.5)<br>• Liveness states: REGISTERED/LIVE/STALE/DEPARTED (Phase 3.5 `WorkerLivenessState`)<br>• `heartbeat_seq` monotonic guard (Phase 3.5)<br>• Epoch supersede on re-registration (Phase 3.5 §3)<br>• SubprocessTransport validates at handshake (Phase 3.7) | • Network protocol for registration (gRPC, HTTP/JSON, WebSocket, custom)<br>• Heartbeat interval, timeout, retry semantics over network<br>• Departure detection: explicit `depart()` vs implicit timeout<br>• Network partition handling: STALE vs DEPARTED semantics<br>• Registration idempotency and deduplication over unreliable network<br>• Transport binding: how `transport_identity` maps to network endpoint | • Registration storm on network partition recovery<br>• Heartbeat loss → false STALE → worker excluded<br>• Duplicate registration from network retries<br>• No explicit departure → orphaned registry entries<br>• Transport identity spoofing (no attestation per D2) | **RESOLVED: Option 1 — HTTP/JSON over TLS (stdlib `http.client` + `ssl`).** Stdlib-only; RESTful; works with mTLS. | **NO** |
| **D7** | **Cross-Tenant Network Isolation** | Phase 3.4 §8: "`tenant_id` propagated at every boundary." Phase 3.5 §9: "No cross-tenant job visibility/execution/secrets... Per-tenant resource pools/queues/metrics — all reporting, never policy." Phase 3.6 §6: "Cross-tenant rejection: hard prohibition." Phase 3.8 §Security/Trust Gap: "Remote: NO cross-tenant network isolation, NO per-tenant secret namespaces, NO per-tenant resource pools." Phase 3.8 §11 Blocker 8. | Tenant isolation at registry query level sufficient; network layer adds nothing. | • `WorkerIdentity.tenant_scope` immutable (Phase 3.5)<br>• Registry `list(tenant_scope=...)` server-side filter (Phase 3.5)<br>• DispatchConstraints.tenant_scope hard filter (Phase 3.6 `DispatchConstraints`)<br>• `RuntimeCapabilities.supports_tenant_isolation: bool` (Phase 3.4)<br>• Secrets never in args; vault refs only (Phase 3.4 §7) | • Per-tenant network policy (CNI, service mesh, firewall rules)<br>• Per-tenant secret injection at transport layer<br>• Per-tenant resource pools (CPU, memory, queue) at network level<br>• Cross-tenant traffic encryption / segmentation<br>• Multi-tenant worker sharing model (Phase 3.6 §17: OPEN) | • Cross-tenant data leakage via shared network<br>• Noisy neighbor: tenant A workload affects tenant B latency<br>• Secret injection into wrong tenant namespace<br>• Compliance violation (PCI, HIPAA, GDPR) | **RESOLVED: Option 5 — No shared workers.** Each worker instance bound to single `tenant_scope`; eliminates cross-tenant at worker level. | **NO** |
| **D8** | **Capacity / Backpressure Semantics** | Phase 3.5 §11: "Worker reports capacity. EE enforces policy." Phase 3.5 §11: "Queue depth: Worker Fabric (per-worker/per-pool)." Phase 3.6 §9: "Capacity enforcement... NOT implemented... future work... Phase 3.6 may use capacity only as soft ranking signal, never as hard gate." Phase 3.8 §11 Blocker 9: "Remote transport needs explicit queue depth limits, flow control, and rejection semantics (CAPACITY_LIMIT) — not defined." | Soft ranking by reported capacity sufficient; EE concurrency limits handle backpressure. | • `WorkerCapabilities.max_concurrency`, `max_cpu_cores`, `max_memory_mb` (Phase 3.5)<br>• `RuntimeCapabilities.max_concurrency` (Phase 3.4)<br>• EE `max_concurrent`, `per_mission` limits (Phase 3.3)<br>• `RuntimeErrorType.CAPACITY_LIMIT` exists (Phase 3.4)<br>• SubprocessTransport: no queue depth limit implemented (Phase 3.7) | • Remote transport queue depth limit (per worker, per pool, global)<br>• Flow control: backpressure signaling to EE (TCP window, application-level credits)<br>• Rejection semantics: when to return `CAPACITY_LIMIT` vs queue<br>• Worker-reported vs measured capacity discrepancy handling<br>• Per-tenant capacity quotas at transport layer | • Unbounded queue → OOM / latency spike<br>• Thundering herd: all workers report capacity, EE dispatches, workers overload<br>• No signal to EE to pause dispatch → lease expiry storms<br>• `CAPACITY_LIMIT` error undefined trigger conditions | **RESOLVED: Option 2 — Bounded transport queue + EE pull.** Transport has bounded queue (e.g., 100 per worker); EE pulls when slot available; `CAPACITY_LIMIT` if queue full. | **NO** |
| **D9** | **Observability Correlation Protocol** | Phase 3.4 §9: "Single correlation chain: mission_id → task_id → execution_id → attempt_no → runtime_id → worker_id → event_id." Phase 3.5 §12: Same chain + worker_id. Phase 3.6 §16: Additive `DISPATCH_*` / `WORKER_*` events. Phase 3.8 §11 Blocker 10: "Remote transport must emit correlated events (mission_id → ... → correlation_id) — protocol not defined." | Existing correlation chain sufficient; remote transport adds no new correlation fields. | • `RuntimeJob.correlation_id == execution_id` (Phase 3.4)<br>• `RuntimeRequest.correlation_id` (Phase 3.4)<br>• `RuntimeResult.correlation_id`, `runtime_id`, `worker_id` (Phase 3.4)<br>• SubprocessTransport events carry full chain (Phase 3.7 `_emit()`)<br>• `execution_events` table + `audit.record` single store (Phase 3.3/3.4) | • Remote transport event emission protocol (push vs pull, format, batching)<br>• Correlation field completeness guarantee (all 7 IDs present)<br>• Event ordering guarantees across network<br>• Event loss detection / reconciliation<br>• Sampling / rate limiting policy for high-volume remote workers | • Broken correlation chain → undebuggable distributed traces<br>• Event loss → incomplete audit trail<br>• Inconsistent event formats → observability tooling breaks<br>• No event ordering → causal analysis impossible | **RESOLVED: Option 1 — JSONL over same channel (SubprocessTransport pattern).** Worker emits events on same channel; transport forwards to EE event sink; stdlib, same format. | **NO** |
| **D10** | **Network Governance-Check Boundary** | Phase 3.4 §7: "Hermes re-checks allowlist from job policy — unapproved names never reach runtime." Phase 3.5 §15: "Governance precedes execution... worker self-authorizing would bypass every gate." Phase 3.7 SubprocessTransport: `governance_check: Callable[[RuntimeRequest], bool]` fail-closed. Phase 3.8 §11 Blocker 11: "Remote needs equivalent [governance_check] but over network." | Local `governance_check` callable sufficient; remote can reuse same pattern. | • `governance_check` fail-closed callable at transport (Phase 3.7)<br>• Tool allowlist at EE job build (Phase 3.3 `_invoke_tool`)<br>• Approvals L0-L3 complete before `RuntimeRequest` (Phase 3.4 §5)<br>• `RuntimeErrorType.GOVERNANCE_DENIED`, `AUTH_DENIED` (Phase 3.4)<br>• EE remains sole authorizer (Phase 3.4 I1, Phase 3.5 I1) | • Network governance check protocol (sync vs async, where runs)<br>• Whether remote transport re-validates allowlist/approvals or trusts EE<br>• Governance check latency budget (must not block dispatch)<br>• Policy distribution to remote workers (allowlist, approval rules)<br>• Audit of governance decisions at network boundary | • Governance bypass: remote worker executes unapproved tool<br>• Stale policy: remote worker uses outdated allowlist<br>• Latency: sync governance check adds dispatch latency<br>• Split-brain: EE approves, remote transport denies (or vice versa) | **RESOLVED: Option 1 — EE-only governance (trust EE).** Transport assumes EE validated; no re-check; fail-closed only on transport errors. Preserves EE sole authority. | **NO** |

---

## Invariant Preservation Check

**Execution Engine Remains Sole Authority For (verification):**

| Authority | Confirmed in Source | Transport Must Not Own |
|-----------|---------------------|------------------------|
| execution_id creation | Phase 3.3 `_claim()` → `exe_` + uuid |  Confirmed: transport receives `job_id == execution_id` |
| attempt lifecycle / attempt_no | Phase 3.3 `_claim()` attempt_no=1, `_schedule_retry()` +1 |  Confirmed: transport never increments |
| leases (lease_owner, lease_expires_at) | Phase 3.3 `_claim()` synthetic `w-*`, `_sweep()` expires |  Confirmed: transport has no lease fields |
| retry policy / backoff / max_attempts | Phase 3.3 `_backoff()`, `_schedule_retry()` CAS |  Confirmed: transport never retries |
| task state transitions | Phase 3.3 `_gw()` CAS only writer |  Confirmed: transport returns `RuntimeResult` only |
| cancellation policy | Phase 3.3 `cancel_task()`, `_cancels()`, `_set_cancel()` |  Confirmed: transport `cancel()` cooperative only |
| timeout policy | Phase 3.3 `_timeouts()`, `task_timeout`, `mission_timeout` |  Confirmed: transport has local timeout only |
| final persistence | Phase 3.3 SQLite `executions` table |  Confirmed: transport ephemeral only |
| DAG scheduling | Phase 3.3 `_dispatch_ready()`, task_graph `ready_tasks()` |  Confirmed: transport never schedules |
| tool allowlist / governance | Phase 3.3 `tools.call_tool()`, approvals L0-L3 |  Confirmed: transport `governance_check` fail-closed only |
| audit persistence | Phase 3.3 `audit.record()`, `execution_events` |  Confirmed: transport events additive only |

**RemoteWorkerTransport owns ONLY (per architectural rule):**
- Remote connection lifecycle
- Request delivery (with `idempotency_key = execution_id`)
- Response delivery
- Transport-local timeout (not EE timeout policy)
- Protocol validation
- Identity validation (`worker_id/instance_id/epoch/nonce/tenant`)
- Worker epoch validation
- Connection failure handling
- Transport events (additive to EE audit)
- Cleanup

---

## Summary Classification

### A. Decisions That Can Be Inherited From Existing Architecture

| Decision | Inherited From | Basis |
|----------|---------------|-------|
| `job_id == execution_id` (dedup key) | Phase 3.4 `RuntimeJob` | Frozen contract |
| `idempotency_key == execution_id` | Phase 3.4 `RuntimeRequest` | Frozen contract |
| `correlation_id == execution_id` | Phase 3.4 `RuntimeJob` | Frozen contract |
| `RuntimeErrorType` 8-category taxonomy | Phase 3.4 | Frozen enum |
| `RuntimeTransportKind.REMOTE` | Phase 3.4 | Frozen enum |
| `RuntimeCapabilities` fields | Phase 3.4 | Frozen contract |
| `WorkerIdentity` fields | Phase 3.5 | Frozen contract |
| `WorkerLivenessState` 4 states | Phase 3.5 | Frozen enum |
| `DispatchConstraints` hard attributes | Phase 3.6 | Frozen contract |
| `DispatchOrdering.DETERMINISTIC_FIRST_ELIGIBLE` | Phase 3.6 | Frozen enum |
| EE sole authority invariants (I1–I22) | Phases 3.3–3.6 | Frozen architecture |
| Governance precedes execution | Phase 3.4 §5, Phase 3.5 §15 | Frozen boundary |
| Capability  authorization | Phase 3.5 I10, Phase 3.6 I3 | Frozen invariant |
| Tenant isolation mandatory | Phase 3.5 I9, Phase 3.6 §6 | Frozen invariant |

### B. Decisions Requiring Explicit Architecture Approval

All 10 decisions now explicitly resolved by Architecture Owner.

---

### C. Phase 3.8 Decision Status

| Decision | Status | Selection |
|----------|--------|-----------|
| D1 | **RESOLVED** | Option 2 — Additive SQLite persistence |
| D2 | **RESOLVED** | Option 1 — mTLS with control-plane CA |
| D3 | **RESOLVED** | Option 4 — Registry-authoritative epoch |
| D4 | **RESOLVED** | Option 1 — Propagate `business_id` as `tenant_id` in metadata + DispatchConstraints |
| D5 | **RESOLVED** | Option 1 — mTLS with control-plane CA |
| D6 | **RESOLVED** | Option 1 — HTTP/JSON over TLS |
| D7 | **RESOLVED** | Option 5 — No shared workers |
| D8 | **RESOLVED** | Option 2 — Bounded transport queue + EE pull |
| D9 | **RESOLVED** | Option 1 — JSONL over same channel |
| D10 | **RESOLVED** | Option 1 — EE-only governance |

---

### D. Dependency Validation

All dependency chains are now satisfiable:

```
Security:      D2=1 (mTLS) → D5=1 (mTLS) → D7=5 (No shared workers) 
Worker lifecycle: D3=4 (Registry-authoritative epoch) → D1=2 (Additive SQLite) → D6=1 (HTTP/JSON over TLS) 
Tenant isolation: D4=1 (Propagate business_id) → D7=5 (No shared workers) → D10=1 (EE-only governance) 
Transport impl: D2=1 + D5=1 + D6=1 + D8=2 + D9=1 all resolved 
```

---

### E. Phase 3.8 Blocked Status (Updated)

| Criterion | Status |
|-----------|--------|
| Architecture gate approved? | **YES** — decisions D1–D10 all explicitly resolved |
| All 10 decisions resolved? | **YES** — 10/10 resolved |
| Minimum 5 blocking decisions resolved? | **YES** — 5/5 resolved (D1, D2, D3, D5, D6) |
| Phase 3.6 threat modeling complete? | **RESOLVED** — D2=1 (mTLS) selected by Architecture Owner |
| Phase 3.8 network design complete? | **RESOLVED** — D3=4, D6=1, D7=5 selected by Architecture Owner |
| Transport security model defined? | **YES** — D5=1 (mTLS with control-plane CA) |
| Implementation authorized? | **YES — pending implementation review** |

**PHASE 3.8 DECISIONS RESOLVED**

---

## Final Determination

**PHASE 3.8 ACTION 1 — DECISION REGISTER COMPLETE (UPDATED WITH ACTION 9 DECISIONS)**  
**STATUS: DECISIONS RESOLVED — READY FOR IMPLEMENTATION REVIEW**  
**STOP.**