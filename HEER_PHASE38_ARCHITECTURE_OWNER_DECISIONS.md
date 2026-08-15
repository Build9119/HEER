# HEER Phase 3.8 — Architecture Owner Decision Request

**Repository:** /Users/delit/JARVIS/jarvis  
**Document:** HEER_PHASE38_ARCHITECTURE_OWNER_DECISIONS.md  
**Derived from:** HEER_PHASE38_DECISION_REGISTER.md, HEER_PHASE38_REMOTE_WORKER_TRANSPORT_GATE.md, Phase 3.4–3.7 gates and contracts  
**Action:** 2 — Convert Decision Register into Explicit Architecture Owner Decision Request  
**Status:** BLOCKED — No Implementation Authorized  
**Mode:** READ-ONLY. No production code modified.

---

## 1. STATUS

| Item | State |
|------|-------|
| **Phase 3.8** | **BLOCKED** |
| **Implementation Authorized** | **NO** |
| **Architecture Gate Approved** | **NO** — this document IS the decision request |
| **D1–D10 Resolved** | **0/10** — All require explicit Architecture Owner decision |
| **Phase 3.6 Threat Modeling Complete** | **NO** — prerequisite for D2 |
| **Phase 3.8 Network Design Complete** | **NO** — prerequisite for D3, D6, D7 |
| **Transport Security Model Defined** | **NO** — prerequisite for D5 |
| **Production Code Changed** | **NO** |
| **Tests Changed** | **NO** |
| **Dependencies Changed** | **NO** |
| **Phase 3.7 Changed** | **NO** |
| **RuntimeTransport Changed** | **NO** |
| **Execution Engine Changed** | **NO** |

---

## 2. DECISION SUMMARY

| ID | Decision | Why It Matters | Current State | Decision Required | Blocks |
|----|----------|----------------|---------------|-------------------|--------|
| **D1** | Worker Registration Persistence | Worker identity survival across control-plane restarts | In-memory only (Phase 3.5) | Persistence model: in-memory / additive SQLite / external store | **YES** |
| **D2** | Remote Worker Attestation Depth | Prevent worker spoofing on untrusted networks | Self-claimed identity only (local registry handshake) | Attestation model: mTLS, SPIFFE, signed registration, or explicit "never" | **YES** |
| **D3** | Worker Epoch / Clock-Skew Semantics | Correct epoch ordering across distributed workers | Single-host monotonic epoch; no skew model | Clock-skew bound + epoch semantics (logical vs wall-clock) | **YES** |
| **D4** | business_id-Scoped Identity Boundary | Propagate tenant context from mission → execution → dispatch | Job tenant context OPEN; only mission has business_id | Propagation path + identity boundary definition | **YES** |
| **D5** | Transport Security Model | Secure remote channel; prevent MITM/replay/exfiltration | NO mTLS, NO auth, NO encryption, NO replay protection | Security model: mTLS/SPIFFE/alt + cert lifecycle + replay protection | **YES** |
| **D6** | Remote Registration / Heartbeat / Departure Protocol | Reliable worker lifecycle over unreliable network | Local registry ops only; no network protocol | Network protocol + heartbeat semantics + departure detection | **YES** |
| **D7** | Cross-Tenant Network Isolation | Prevent cross-tenant data leakage on shared network | Application-level tenant filter only; no network isolation | Network isolation model (VPC, mesh, per-tenant TLS, or app-only) | **YES** |
| **D8** | Capacity / Backpressure Semantics | Prevent overload, OOM, thundering herd | EE concurrency limits only; no queue depth / flow control | Queue depth limits + backpressure protocol + CAPACITY_LIMIT triggers | **YES** |
| **D9** | Observability Correlation Protocol | End-to-end traceability across remote workers | Local events carry full chain; remote protocol undefined | Remote event emission protocol + mandatory fields + ordering | **YES** |
| **D10** | Network Governance-Check Boundary | Prevent governance bypass at transport layer | Local governance_check callable; remote pattern undefined | Check location (EE-only vs transport) + protocol + latency budget | **YES** |

---

## 3. D1–D10 DECISION REQUESTS

### D1 — Worker Registration Persistence

**Existing Facts**
- Phase 3.5 `worker_registry.py`: In-memory dict + `RLock`; 8 public methods (`register`, `heartbeat`, `mark_stale`, `depart`, `get`, `list`, `list_by_capability`, `status`).
- Phase 3.5 §22 Q1: "Left open — no answer invented."
- Phase 3.8 §11 Blocker 1: "Worker registration is in-memory only. No persistence."
- `WorkerIdentity`: `worker_id`, `worker_instance_id`, `worker_epoch`, `tenant_scope` immutable per registration.
- `WorkerLiveness`: `heartbeat_seq` monotonic; states `REGISTERED/LIVE/STALE/DEPARTED`.
- Re-registration on restart = new `instance_id` + new `epoch`.

**Explicit Gap**
- No durability guarantees (WAL, replication, crash recovery).
- No recovery of registry state on control-plane restart.
- No schema for additive persistence.
- No TTL / GC policy for stale entries.

**Options Supported by Existing Architecture**
1. **In-memory only (current)**: Accept loss on restart; workers re-register fresh (new instance_id + epoch). EE lease/sweep composes.
2. **Additive SQLite table**: Single-writer (registry), schema mirrors `WorkerIdentity` + `WorkerLiveness` fields, WAL mode, migration path from empty.
3. **External store**: PostgreSQL/etcd/Consul — requires network dependency, not in current stdlib-only stack.

**Recommended Option**  
*Only if supported by source documents* — Phase 3.5 §22 Q1 explicitly left this open. Phase 3.8 §11 Blocker 1 identifies it as a blocker. No recommendation is pre-made in source.

**Consequences**
| Option | Pros | Cons |
|--------|------|------|
| In-memory | Zero dependencies, simple, EE sweep recovers | Identity loss on restart; duplicate re-registration races; no audit trail |
| Additive SQLite | Durable, single-writer, stdlib, audit trail | Schema migration; single-writer coordination; TTL/GC policy needed |
| External | Scale, HA, shared | New dependency; network coupling; out of scope for Phase 3 stdlib mandate |

**Architecture Owner Decision**  
`DECISION: __________`  
`RATIONALE: __________`

---

### D2 — Remote Worker Attestation Depth

**Existing Facts**
- Phase 3.5 §3: "Spoofing prevention (conceptual)" only.
- Phase 3.5 §22 Q2: "TBD by Phase 3.6 threat modeling."
- Phase 3.6 §7: "Worker-reported capabilities are potentially untrusted... The gate must not pretend attestation exists."
- Phase 3.6 §24 Q1: "Attestation model (or explicit 'never')."
- Phase 3.8 §Security/Trust Gap: "Remote: NO mutual TLS, NO transport-layer auth, NO credential model."
- Phase 3.8 §11 Blocker 2: "Remote attestation model undefined."
- `WorkerIdentity.transport_identity` field reserved for future per-transport credential (Phase 3.5).
- Capability is descriptive, never authorization (Phase 3.5 I10, Phase 3.6 I3).
- `RuntimeErrorType.AUTH_DENIED` exists (Phase 3.4).

**Explicit Gap**
- No cryptographic attestation model (mTLS, signed JWT, SPIFFE, TPM, etc.).
- No attestation depth per isolation mode (SUBPROCESS vs CONTAINER vs REMOTE vs K8S).
- No credential binding to `worker_instance_id + epoch`.
- No verification authority (who signs? CA? control plane?).
- No revocation / rotation model.
- No trust anchor distribution.

**Options Supported by Existing Architecture**
1. **mTLS with control-plane CA**: Certs issued per `worker_instance_id + epoch`; control plane is CA; rotation on re-registration.
2. **SPIFFE/SPIRE**: Workload identity standard; integrates with service mesh; requires SPIRE agent.
3. **Signed registration token**: Control plane signs `worker_id + instance_id + epoch + tenant_scope + expiry`; worker presents token at registration.
4. **Explicit "never" with compensating controls**: No attestation; rely on network segmentation + EE correlation + audit; document as accepted risk.

**Recommended Option**  
*Only if supported by source documents* — Phase 3.6 threat modeling is prerequisite and incomplete. Phase 3.6 §24 Q1 lists "Attestation model (or explicit 'never')" as open. No source pre-decides.

**Consequences**
| Option | Pros | Cons |
|--------|------|------|
| mTLS | Strong identity, stdlib `ssl`, cert rotation on epoch | CA management, cert distribution, clock skew for expiry |
| SPIFFE | Industry standard, mesh-ready | SPIRE dependency, complexity |
| Signed token | Simpler than mTLS, no TLS termination | Token replay risk, requires secure channel anyway |
| Never | No crypto complexity | Worker spoofing risk; capability forgery; no provenance proof |

**Architecture Owner Decision**  
`DECISION: __________`  
`RATIONALE: __________`

---

### D3 — Worker Epoch / Clock-Skew Semantics

**Existing Facts**
- Phase 3.5 §3: `worker_epoch` monotonically increasing per registration; new spawn = new epoch.
- Phase 3.5 §22 Q3: "Requires Phase 3.8 network design."
- Phase 3.6 §8: "Selection must bind to exact `(worker_id, instance_id, epoch)` triple; newer epoch supersedes."
- Phase 3.8 §11 Blocker 3: "Epoch semantics across network partitions undefined."
- Registry rejects duplicate epoch (Phase 3.5 `worker_registry.py`).
- `heartbeat_seq`: monotonic counter for ordering (Phase 3.5 `WorkerLiveness`).
- Deterministic ordering: first-eligible by `worker_id` (Phase 3.6 `DispatchOrdering`).

**Explicit Gap**
- Maximum allowed clock skew between control plane and remote workers.
- Epoch comparison semantics under skew (wall-clock vs logical).
- Whether `worker_epoch` is wall-clock timestamp or logical counter.
- Stale-epoch detection window across network partitions.
- Re-registration race: two hosts claiming same `worker_id` with different epochs.

**Options Supported by Existing Architecture**
1. **Logical counter (per-registry)**: Epoch = incrementing integer per `worker_id` managed by registry. No clock dependency. Requires registry as epoch authority.
2. **Hybrid Logical Clock (HLC)**: Combines wall-clock + logical counter; bounded skew tolerance (e.g., ±100ms). Workers and registry sync via HLC.
3. **Wall-clock timestamp (NTP-synced)**: Epoch = `time.time_ns()`; requires NTP sync bound (e.g., ±50ms). Simpler but clock-dependent.
4. **Registry-authoritative epoch**: Registry assigns epoch on registration; workers cannot self-assign. Eliminates races but requires registry availability.

**Recommended Option**  
*Only if supported by source documents* — Phase 3.5 epoch is "positive int, immutable per registration" but semantics undefined. Phase 3.5 §22 Q3 explicitly requires Phase 3.8 network design. No source pre-decides.

**Consequences**
| Option | Pros | Cons |
|--------|------|------|
| Logical counter | No clock dependency, simple | Registry becomes epoch authority; partition = no new epochs |
| HLC | Bounded skew, distributed-friendly | Complexity; requires HLC library or implementation |
| Wall-clock | Simple, human-readable | NTP dependency; skew causes epoch inversion |
| Registry-authoritative | Eliminates races, single source of truth | Registry SPOF for registration; partition = blocked |

**Architecture Owner Decision**  
`DECISION: __________`  
`RATIONALE: __________`

---

### D4 — business_id-Scoped Identity Boundary

**Existing Facts**
- Phase 3.5 §22 Q7: "Open."
- Phase 3.6 §6: "Job tenant context: does not exist today... OPEN ARCHITECTURAL QUESTION."
- Phase 3.6 §17: "Job tenant scope: does not exist on missions/tasks/executions — OPEN."
- Phase 3.8 §11 Blocker 4: "business_id boundary undefined."
- `WorkerIdentity.tenant_scope`: `tuple[str]` immutable per registration (Phase 3.5).
- Registry queries tenant-scoped via `list(tenant_scope=...)` (Phase 3.5).
- `RuntimeRequest` carries no tenant field (Phase 3.4 `runtime_contracts.py`).
- `business_id` exists only at mission level via `mission_engine` (Phase 3.3).
- Tools receive `business_id` via `call_tool(..., business_id=biz)` (Phase 3.3 EE).
- Phase 3.6 §17: "Cross-tenant shared worker model: OPEN."

**Explicit Gap**
- Propagation of `business_id` / `tenant_id` from mission → execution → RuntimeRequest.
- Whether worker needs separate identity boundary for `business_id`-scoped tools beyond `tenant_scope`.
- Cross-tenant shared worker model.
- Platform tenant semantics.

**Options Supported by Existing Architecture**
1. **Propagate `business_id` as `tenant_id` in `RuntimeRequest.metadata` + `DispatchConstraints`**: Minimal change; reuses existing `tenant_scope` filter.
2. **Extend `RuntimeRequest` with explicit `tenant_id` field**: Contract change; requires Phase 3.4 contract amendment.
3. **Separate `business_id` identity boundary at worker**: Worker enforces per-business tool allowlist; requires worker-side governance.
4. **No cross-tenant shared workers**: Each worker instance bound to single `tenant_scope`; simpler isolation.

**Recommended Option**  
*Only if supported by source documents* — Phase 3.6 §6 and §17 explicitly mark as OPEN. Phase 3.4 `RuntimeRequest` has no tenant field. No source pre-decides.

**Consequences**
| Option | Pros | Cons |
|--------|------|------|
| Propagate in metadata | No contract change; minimal | Metadata is advisory; worker must honor |
| Explicit tenant_id field | Contractual, enforceable | Phase 3.4 contract amendment required |
| Worker-side boundary | Strong isolation | Worker becomes second governance authority (violates I1, I14) |
| No shared workers | Simple, no cross-tenant risk | Resource inefficiency; not multi-tenant platform |

**Architecture Owner Decision**  
`DECISION: __________`  
`RATIONALE: __________`

---

### D5 — Transport Security Model

**Existing Facts**
- Phase 3.4 §7: "secrets never in args; vault-resolved references only; logs redacted."
- Phase 3.5 §10: "Conceptual control" for forged identity (signed registration, mutual auth).
- Phase 3.5 §11: "Transport TLS (future)."
- Phase 3.7 SubprocessTransport: local IPC, no network.
- Phase 3.8 §Security/Trust Gap: "Remote: NO mutual TLS, NO transport-layer auth, NO credential model, NO channel encryption, NO replay protection beyond idempotency_key."
- Phase 3.8 §11 Blocker 5: "Transport security model undefined."
- `RuntimeCapabilities.supports_secrets: bool` (Phase 3.4).
- `_is_secret_key()` redaction on serialization (Phase 3.4).
- `RuntimeErrorType.AUTH_DENIED`, `GOVERNANCE_DENIED`, `TRANSPORT` (Phase 3.4).
- SubprocessTransport handshake validates `worker_id/instance_id/epoch/tenant_id/nonce` against local registry (Phase 3.7).
- `governance_check: Callable[[RuntimeRequest], bool]` fail-closed (Phase 3.7).

**Explicit Gap**
- Mutual TLS design (cert issuance, rotation, verification).
- Transport-layer authentication (mTLS, SPIFFE, OIDC, API keys).
- Channel encryption (TLS 1.3, Noise, WireGuard).
- Replay protection beyond `idempotency_key` (nonce, sequence numbers).
- Credential model for remote workers (cert, token, key).
- Transport-level authorization (must not become second authority).

**Options Supported by Existing Architecture**
1. **mTLS with control-plane CA**: Certs per `worker_instance_id + epoch`; stdlib `ssl`; cert rotation on re-registration (new epoch = new cert).
2. **SPIFFE/SPIRE**: Workload identity; integrates with mesh; requires SPIRE agent deployment.
3. **TLS + API Key**: Server TLS + client API key in header; simpler; key rotation on epoch.
4. **Noise Protocol / WireGuard**: Modern crypto; kernel/userspace; non-stdlib dependency.
5. **Application-layer only (no transport encryption)**: Rely on network segmentation (VPC, mesh); document as accepted risk.

**Recommended Option**  
*Only if supported by source documents* — Phase 3.5 §11 "Transport TLS (future)" implies TLS expected. Phase 3.8 §Security/Trust Gap lists all as missing. No source pre-decides mTLS vs SPIFFE vs other.

**Consequences**
| Option | Pros | Cons |
|--------|------|------|
| mTLS | Strong mutual auth, stdlib, cert per epoch | CA ops, cert distribution, clock skew for expiry |
| SPIFFE | Standard, mesh-native, auto-rotation | SPIRE dependency, operational complexity |
| TLS + API Key | Simpler, stdlib | Key management, no mutual auth without client cert |
| Noise/WireGuard | Modern, fast | Non-stdlib; kernel dependency for WireGuard |
| App-layer only | No crypto code | MITM, replay, exfiltration risk; compliance gap |

**Architecture Owner Decision**  
`DECISION: __________`  
`RATIONALE: __________`

---

### D6 — Remote Registration / Heartbeat / Departure Protocol

**Existing Facts**
- Phase 3.5 `worker_registry.py`: `register()`, `heartbeat()`, `mark_stale()`, `depart()`, `get()`, `list()`, `status()`.
- Phase 3.7 SubprocessTransport: local handshake at spawn validates against registry.
- Phase 3.8 §11 Blocker 7: "SubprocessTransport uses local process + IPC; remote needs a protocol."
- Liveness states: `REGISTERED/LIVE/STALE/DEPARTED` (Phase 3.5 `WorkerLivenessState`).
- `heartbeat_seq` monotonic guard (Phase 3.5).
- Epoch supersede on re-registration (Phase 3.5 §3).

**Explicit Gap**
- Network protocol for registration (gRPC, HTTP/JSON, WebSocket, custom).
- Heartbeat interval, timeout, retry semantics over network.
- Departure detection: explicit `depart()` vs implicit timeout.
- Network partition handling: STALE vs DEPARTED semantics.
- Registration idempotency and deduplication over unreliable network.
- Transport binding: how `transport_identity` maps to network endpoint.

**Options Supported by Existing Architecture**
1. **HTTP/JSON over TLS (stdlib `http.client` + `ssl`)**: Stdlib-only; RESTful; simple; works with mTLS.
2. **gRPC (requires grpcio dependency)**: Efficient, streaming, codegen; non-stdlib.
3. **WebSocket (stdlib `http.client` upgrade + custom framing)**: Bidirectional; good for heartbeats; more complex.
4. **Custom TCP + JSONL (like SubprocessTransport IPC)**: Familiar pattern; stdlib; no framing standard.

**Recommended Option**  
*Only if supported by existing architecture* — Phase 3.7 SubprocessTransport uses JSONL over stdin/stdout (stdlib only). Phase 3.8 gate §Security mandates stdlib-only. HTTP/JSON over TLS is stdlib-compatible.

**Consequences**
| Option | Pros | Cons |
|--------|------|------|
| HTTP/JSON + TLS | Stdlib, firewall-friendly, mTLS compatible | Request/response only; polling for heartbeats |
| gRPC | Streaming, efficient, contract-first | Non-stdlib dependency (violates stdlib mandate) |
| WebSocket | Native push, bidirectional | Stdlib upgrade complex; framing non-standard |
| Custom TCP + JSONL | Familiar (SubprocessTransport pattern) | No standard framing; firewall issues; custom protocol |

**Architecture Owner Decision**  
`DECISION: __________`  
`RATIONALE: __________`

---

### D7 — Cross-Tenant Network Isolation

**Existing Facts**
- Phase 3.4 §8: "`tenant_id` propagated at every boundary."
- Phase 3.5 §9: "No cross-tenant job visibility/execution/secrets... Per-tenant resource pools/queues/metrics — all reporting, never policy."
- Phase 3.6 §6: "Cross-tenant rejection: hard prohibition."
- Phase 3.8 §Security/Trust Gap: "Remote: NO cross-tenant network isolation, NO per-tenant secret namespaces, NO per-tenant resource pools."
- Phase 3.8 §11 Blocker 8: "Cross-tenant network isolation undefined."
- `WorkerIdentity.tenant_scope` immutable (Phase 3.5).
- Registry `list(tenant_scope=...)` server-side filter (Phase 3.5).
- `DispatchConstraints.tenant_scope` hard filter (Phase 3.6).
- `RuntimeCapabilities.supports_tenant_isolation: bool` (Phase 3.4).
- Secrets never in args; vault refs only (Phase 3.4 §7).
- Phase 3.6 §17: "Multi-tenant worker sharing model: OPEN."

**Explicit Gap**
- Per-tenant network policy (CNI, service mesh, firewall rules).
- Per-tenant secret injection at transport layer.
- Per-tenant resource pools (CPU, memory, queue) at network level.
- Cross-tenant traffic encryption / segmentation.
- Multi-tenant worker sharing model.

**Options Supported by Existing Architecture**
1. **Application-level only (current)**: Tenant filter at registry + dispatch; no network isolation; rely on worker process isolation.
2. **Per-tenant TLS**: Each tenant gets distinct CA/cert; workers present tenant-scoped cert; transport validates.
3. **Service mesh (Istio/Linkerd/Cilium)**: Mesh enforces per-tenant mTZ, authorization policies; requires mesh deployment.
4. **VPC / Network segmentation**: Separate VPCs/subnets per tenant; firewall rules; infrastructure-level.
5. **No shared workers**: Each worker instance bound to single tenant; eliminates cross-tenant at worker level.

**Recommended Option**  
*Only if supported by existing architecture* — Phase 3.5 §9 "reporting, never policy" and Phase 3.6 §17 "multi-tenant worker sharing: OPEN" imply no pre-decision. Phase 3.8 gate has no network infrastructure.

**Consequences**
| Option | Pros | Cons |
|--------|------|------|
| App-level only | No infra, simple | No network enforcement; compliance risk |
| Per-tenant TLS | Crypto-enforced, transport-native | Cert management per tenant; complex |
| Service mesh | Rich policies, observability | Mesh dependency; operational burden |
| VPC segmentation | Strong isolation, compliance | Infra cost; not portable |
| No shared workers | Eliminates problem | Resource inefficiency; not multi-tenant |

**Architecture Owner Decision**  
`DECISION: __________`  
`RATIONALE: __________`

---

### D8 — Capacity / Backpressure Semantics

**Existing Facts**
- Phase 3.5 §11: "Worker reports capacity. EE enforces policy."
- Phase 3.5 §11: "Queue depth: Worker Fabric (per-worker/per-pool)."
- Phase 3.6 §9: "Capacity enforcement... NOT implemented... future work... Phase 3.6 may use capacity only as soft ranking signal, never as hard gate."
- Phase 3.8 §11 Blocker 9: "Remote transport needs explicit queue depth limits, flow control, and rejection semantics (CAPACITY_LIMIT) — not defined."
- `WorkerCapabilities.max_concurrency`, `max_cpu_cores`, `max_memory_mb` (Phase 3.5).
- `RuntimeCapabilities.max_concurrency` (Phase 3.4).
- EE `max_concurrent`, `per_mission` limits (Phase 3.3).
- `RuntimeErrorType.CAPACITY_LIMIT` exists (Phase 3.4).
- SubprocessTransport: no queue depth limit implemented (Phase 3.7).

**Explicit Gap**
- Remote transport queue depth limit (per worker, per pool, global).
- Flow control: backpressure signaling to EE (TCP window, application-level credits).
- Rejection semantics: when to return `CAPACITY_LIMIT` vs queue.
- Worker-reported vs measured capacity discrepancy handling.
- Per-tenant capacity quotas at transport layer.

**Options Supported by Existing Architecture**
1. **EE-only limits (current)**: EE concurrency limits are hard gate; transport has no queue; `CAPACITY_LIMIT` never returned by transport.
2. **Transport queue depth + EE pull**: Transport has bounded queue (e.g., 100 per worker); EE pulls when slot available; `CAPACITY_LIMIT` if queue full.
3. **Application-level credits**: Transport issues credits to EE; EE spends credit per dispatch; refill on completion; `CAPACITY_LIMIT` if no credit.
4. **TCP backpressure**: Rely on TCP window; transport accepts until socket buffer full; `CAPACITY_LIMIT` on connection refusal.

**Recommended Option**  
*Only if supported by existing architecture* — Phase 3.6 §9 "capacity only as soft ranking signal, never as hard gate" and Phase 3.5 §11 "EE enforces policy" suggest EE is authority. Transport queue depth not defined.

**Consequences**
| Option | Pros | Cons |
|--------|------|------|
| EE-only | Simple, EE authority preserved | No transport backpressure; thundering herd possible |
| Transport queue + EE pull | Explicit flow control, bounded memory | EE must poll/pull; added complexity |
| Application credits | Explicit, rate-based | Credit protocol complexity; sync needed |
| TCP backpressure | Zero app logic | Coarse; no per-tenant; connection refusal = hard failure |

**Architecture Owner Decision**  
`DECISION: __________`  
`RATIONALE: __________`

---

### D9 — Observability Correlation Protocol

**Existing Facts**
- Phase 3.4 §9: "Single correlation chain: mission_id → task_id → execution_id → attempt_no → runtime_id → worker_id → event_id."
- Phase 3.5 §12: Same chain + worker_id.
- Phase 3.6 §16: Additive `DISPATCH_*` / `WORKER_*` events.
- Phase 3.8 §11 Blocker 10: "Remote transport must emit correlated events — protocol not defined."
- `RuntimeJob.correlation_id == execution_id` (Phase 3.4).
- `RuntimeRequest.correlation_id` (Phase 3.4).
- `RuntimeResult.correlation_id`, `runtime_id`, `worker_id` (Phase 3.4).
- SubprocessTransport events carry full chain (Phase 3.7 `_emit()`).
- `execution_events` table + `audit.record` single store (Phase 3.3/3.4).

**Explicit Gap**
- Remote transport event emission protocol (push vs pull, format, batching).
- Correlation field completeness guarantee (all 7 IDs present).
- Event ordering guarantees across network.
- Event loss detection / reconciliation.
- Sampling / rate limiting policy for high-volume remote workers.

**Options Supported by Existing Architecture**
1. **JSONL over same channel (SubprocessTransport pattern)**: Worker emits events on stdout; transport forwards to EE event sink; stdlib, same format.
2. **Sidecar event stream (HTTP/gRPC)**: Separate event channel; transport pushes batched events; decoupled from request/response.
3. **Polling from EE**: EE pulls events from transport; EE controls rate; transport buffers.
4. **Structured logging to shared sink**: Both EE and transport write to shared log sink (stdout, file, syslog); correlation via fields.

**Recommended Option**  
*Only if supported by existing architecture* — Phase 3.7 SubprocessTransport emits events via `_event_sink` callback (in-process). Phase 3.4 §9 mandates single correlation chain. JSONL over same channel preserves format.

**Consequences**
| Option | Pros | Cons |
|--------|------|------|
| JSONL same channel | Consistent format, stdlib, correlation native | Couples event flow to request channel; backpressure risk |
| Sidecar stream | Decoupled, batchable, rate-controlled | Extra channel; protocol complexity |
| EE polling | EE controls rate, simple transport | Latency; polling overhead; transport must buffer |
| Shared log sink | Decoupled, infrastructure-native | Requires log infra; correlation via parsing |

**Architecture Owner Decision**  
`DECISION: __________`  
`RATIONALE: __________`

---

### D10 — Network Governance-Check Boundary

**Existing Facts**
- Phase 3.4 §7: "Hermes re-checks allowlist from job policy — unapproved names never reach runtime."
- Phase 3.5 §15: "Governance precedes execution... worker self-authorizing would bypass every gate."
- Phase 3.7 SubprocessTransport: `governance_check: Callable[[RuntimeRequest], bool]` fail-closed.
- Phase 3.8 §11 Blocker 11: "Remote needs equivalent [governance_check] but over network."
- Tool allowlist at EE job build (Phase 3.3 `_invoke_tool`).
- Approvals L0-L3 complete before `RuntimeRequest` (Phase 3.4 §5).
- `RuntimeErrorType.GOVERNANCE_DENIED`, `AUTH_DENIED` (Phase 3.4).
- EE remains sole authorizer (Phase 3.4 I1, Phase 3.5 I1).

**Explicit Gap**
- Network governance check protocol (sync vs async, where runs).
- Whether remote transport re-validates allowlist/approvals or trusts EE.
- Governance check latency budget (must not block dispatch).
- Policy distribution to remote workers (allowlist, approval rules).
- Audit of governance decisions at network boundary.

**Options Supported by Existing Architecture**
1. **EE-only governance (trust EE)**: Transport assumes EE validated; no re-check; fail-closed only on transport errors. Simplest; preserves EE sole authority.
2. **Transport re-check (sync RPC)**: Transport calls EE governance service before execution; adds latency; EE remains authorizer.
3. **Policy sync + local check**: EE pushes allowlist/policy to transport; transport checks locally; cache invalidation on policy change.
4. **Async validation**: Transport executes optimistically; EE validates asynchronously; rollback on violation (complex, violates "precedes execution").

**Recommended Option**  
*Only if supported by existing architecture* — Phase 3.4 §7 "Hermes re-checks allowlist" implies transport re-check. Phase 3.5 §15 "governance precedes execution" mandates check before execution. Phase 3.7 has local `governance_check` callable. EE sole authority (I1, I14) must be preserved.

**Consequences**
| Option | Pros | Cons |
|--------|------|------|
| EE-only | Zero latency, simple, EE sole authority | Stale policy risk if EE/transport decoupled |
| Sync RPC | Fresh policy, EE authorizes | Latency per dispatch; EE availability required |
| Policy sync + local | Low latency, fresh-ish policy | Cache invalidation complexity; policy drift window |
| Async | Zero latency | Violates "precedes execution"; rollback complex |

**Architecture Owner Decision**  
`DECISION: __________`  
`RATIONALE: __________`

---

## 4. NON-NEGOTIABLE INVARIANTS

The following invariants are **frozen** from Phases 3.1–3.7 and **must not be violated** by any Phase 3.8 decision:

| # | Invariant | Source |
|---|-----------|--------|
| **I1** | Execution Engine remains sole authority for: task state, claims, leases, attempts, retries, timeouts, cancellation intent, terminal execution state | Phase 3.3, 3.4 I1, 3.5 I1 |
| **I2** | Transport does not own execution state | Phase 3.4, 3.7 |
| **I3** | Transport does not own retries | Phase 3.3, 3.6 I5 |
| **I4** | Transport does not own leases | Phase 3.3, 3.6 I4 |
| **I5** | Transport does not own DAG scheduling | Phase 3.2, 3.6 I6 |
| **I6** | Transport does not become a second governance authority | Phase 3.4 §7, 3.5 §15, 3.5 I14 |
| **I7** | Transport does not persist execution state | Phase 3.3, 3.6 §6 |
| **I8** | RuntimeTransport remains transport-agnostic (contracts unchanged) | Phase 3.4 |
| **I9** | Existing Phase 3.7 SubprocessTransport remains frozen | Phase 3.7 gate |
| **I10** | `job_id == execution_id` (dedup identity) | Phase 3.4 |
| **I11** | `idempotency_key == execution_id` | Phase 3.4 |
| **I12** | `correlation_id == execution_id` | Phase 3.4 |
| **I13** | Capability is descriptive, never authorization | Phase 3.5 I10, 3.6 I3 |
| **I14** | Tenant isolation mandatory (hard filter) | Phase 3.5 I9, 3.6 §6 |
| **I15** | Governance precedes execution | Phase 3.4 §5, 3.5 §15 |
| **I16** | Secrets never in args; vault refs only | Phase 3.4 §7 |
| **I17** | No attestation claimed without explicit decision | Phase 3.6 §7, 3.6 §24 Q1 |
| **I18** | Worker epoch prevents zombie identity | Phase 3.5 I10 |
| **I19** | Liveness  lease | Phase 3.5 I11 |
| **I20** | No second execution identity minted | Phase 3.6 I19 |
| **I21** | Selection re-validates liveness/epoch at call time | Phase 3.6 I21 |
| **I22** | Capacity never a hard gate | Phase 3.6 I22 |

---

## 5. DEPENDENCY ORDER

Explicit dependencies derived from source documents (no invented dependencies):

```
D2 (Attestation) ──────
                        ├──→ D5 (Transport Security) ──────
D3 (Clock-Skew) ───────                                   │
                                                           ├──→ D6 (Registration Protocol)
D5 (Security Model) ───────────────────────────────────────        │
D6 (Registration Protocol) ────────────────────────────────────────
                                                                       ├──→ D8 (Capacity/Backpressure)
D4 (business_id Boundary) ──────────────────────────────────────      │
                                                                ├──→ D7 (Network Isolation)
D5 (Security Model) ────────────────────────────────────────────      │
                                                                        ├──→ D9 (Observability)
D4 (business_id Boundary) ──────────────────────────────────────────  │
                                                                     ├──→ D10 (Governance Boundary)
D5 (Security Model) ────────────────────────────────────────────────
```

**Minimum Resolution Sequence (must resolve in order):**

| Tier | Decisions | Prerequisite For |
|------|-----------|------------------|
| **Tier 1 (Foundational)** | **D2, D3, D5** | D6, D7, D8, D9, D10 |
| **Tier 2 (Protocol)** | **D6** | D8, D9 |
| **Tier 3 (Boundary)** | **D4** | D7, D10 |
| **Tier 4 (Operational)** | **D7, D8, D9, D10** | Implementation |

**Critical Path:** D2 → D5 → D6 → D8/D9/D10 and D3 → D6 and D4 → D7/D10

**D1 (Persistence)** is independent but required before implementation (durability prerequisite).

---

## 6. IMPLEMENTATION GATE

**Phase 3.8 implementation remains BLOCKED until all mandatory architectural decisions are explicitly resolved.**

| Gate Criterion | Status | Required |
|----------------|--------|----------|
| D1: Persistence model decided | PENDING | YES |
| D2: Attestation model decided | PENDING | YES |
| D3: Clock-skew bound decided | PENDING | YES |
| D4: business_id boundary decided | PENDING | YES |
| D5: Transport security model decided | PENDING | YES |
| D6: Registration protocol decided | PENDING | YES |
| D7: Network isolation model decided | PENDING | YES |
| D8: Capacity/backpressure decided | PENDING | YES |
| D9: Observability protocol decided | PENDING | YES |
| D10: Governance boundary decided | PENDING | YES |
| Phase 3.6 threat modeling complete | PENDING | For D2 |
| Phase 3.8 network design complete | PENDING | For D3, D6, D7 |
| All invariants preserved | VERIFIED | Mandatory |
| Zero production code changes | VERIFIED | Mandatory |

**No implementation work (RemoteWorkerTransport, network layer, mTLS, gRPC, persistence, queues, etc.) shall commence until ALL Tier 1–4 decisions are explicitly recorded with Architecture Owner signature.**

---

## 7. CHANGE CONTROL

The following are **prohibited** without explicit Architecture Owner approval beyond this decision request:

-  No production code changes
-  No test changes
-  No dependency changes (stdlib-only mandate preserved)
-  No Phase 3.7 SubprocessTransport changes
-  No RuntimeTransport implementation changes
-  No Execution Engine changes
-  No HermesAdapter changes
-  No WorkerRegistry changes
-  No dispatch_contracts/worker_matcher changes
-  No RuntimeRequest/RuntimeResult/RuntimeHandle contract changes
-  No WorkerIdentity/WorkerLiveness contract changes
-  No SQLite schema changes
-  No networking code (mTLS, gRPC, HTTP, WebSocket, TCP)
-  No remote worker implementation
-  No retry logic additions
-  No queue/backpressure implementation
-  No Kubernetes/container orchestration
-  No database persistence layer
-  No secret injection at transport layer
-  No second governance authority creation

---

## 8. ACCEPTANCE CONDITION FOR ACTION 2

**Action 2 is complete only when:**

- [x] D1–D10 are formally presented for owner decision with explicit facts, gaps, options, consequences
- [x] No decision is silently assumed or pre-filled
- [x] No implementation occurs
- [x] Document is internally consistent with Phases 3.4–3.7 source documents
- [x] All non-negotiable invariants explicitly listed and preserved
- [x] Dependency order explicitly mapped from source evidence
- [x] Implementation gate states Phase 3.8 remains BLOCKED
- [x] Change control prohibits all Phase 3.8 implementation vectors
- [x] Document produced: `HEER_PHASE38_ARCHITECTURE_OWNER_DECISIONS.md`

---

## FINAL DETERMINATION

**PHASE 3.8 ACTION 2 — COMPLETE**

**Document:** HEER_PHASE38_ARCHITECTURE_OWNER_DECISIONS.md

| Checklist | Status |
|-----------|--------|
| Production code changed | **NO** |
| Tests changed | **NO** |
| Dependencies changed | **NO** |
| Phase 3.7 changed | **NO** |

| Decision | Status |
|----------|--------|
| **D1** | **PENDING ARCHITECTURE OWNER DECISION** |
| **D2** | **PENDING ARCHITECTURE OWNER DECISION** |
| **D3** | **PENDING ARCHITECTURE OWNER DECISION** |
| **D4** | **PENDING ARCHITECTURE OWNER DECISION** |
| **D5** | **PENDING ARCHITECTURE OWNER DECISION** |
| **D6** | **PENDING ARCHITECTURE OWNER DECISION** |
| **D7** | **PENDING ARCHITECTURE OWNER DECISION** |
| **D8** | **PENDING ARCHITECTURE OWNER DECISION** |
| **D9** | **PENDING ARCHITECTURE OWNER DECISION** |
| **D10** | **PENDING ARCHITECTURE OWNER DECISION** |

**STATUS:**  
**PHASE 3.8 BLOCKED**

**STOP.**
