# HEER Phase 3.8 — Architecture Owner Decision Sheet

**Repository:** /Users/delit/JARVIS/jarvis
**Action:** 9 — Architecture Owner Decision Entry
**Derived from:** HEER_PHASE38_REMOTE_WORKER_TRANSPORT_GATE.md, HEER_PHASE38_DECISION_REGISTER.md, HEER_PHASE38_ARCHITECTURE_OWNER_DECISIONS.md, HEER_PHASE34_HERMES_GATE.md, HEER_PHASE35_WORKER_FABRIC_GATE.md, HEER_PHASE36_WORKER_DISPATCH_GATE.md, HEER_PHASE36_WORKER_DISPATCH_DELIVERY.md, HEER_ROADMAP.md
**Mode:** DECISION ENTRY. Recording explicit Architecture Owner selections for D1–D10. No production code, tests, or dependencies modified.

---

## 1. DECISIONS D1–D10

All decisions have received **explicit Architecture Owner selections** (Action 8 decision form, provided by Architecture Owner).

| ID | Decision Title | Owner Decision | Dependencies | Blocks Phase 3.8 Implementation |
|----|----------------|----------------|--------------|--------------------------------|
| **D1** | Worker Registration Persistence | **RESOLVED — Option 2 (Additive SQLite table)** | D3 (Worker lifecycle: D3 → D1 → D6) | **NO** |
| **D2** | Remote Worker Attestation Depth | **RESOLVED — Option 1 (mTLS with control-plane CA)** | None upstream (Security chain start); Part of Transport implementation (D2 + D5 + D6 + D8 + D9) | **NO** |
| **D3** | Worker Epoch / Clock-Skew Semantics | **RESOLVED — Option 4 (Registry-authoritative epoch)** | None upstream (Worker lifecycle chain start) | **NO** |
| **D4** | business_id-Scoped Identity Boundary | **RESOLVED — Option 1 (Propagate `business_id` as `tenant_id` in `RuntimeRequest.metadata` + `DispatchConstraints`)** | None upstream (Tenant isolation chain start) | **NO** |
| **D5** | Transport Security Model | **RESOLVED — Option 1 (mTLS with control-plane CA)** | D2 (Security: D2 → D5 → D7) | **NO** |
| **D6** | Remote Registration / Heartbeat / Departure Protocol | **RESOLVED — Option 1 (HTTP/JSON over TLS)** | D1 (Worker lifecycle: D3 → D1 → D6) | **NO** |
| **D7** | Cross-Tenant Network Isolation | **RESOLVED — Option 5 (No shared workers)** | D5 (Security: D2 → D5 → D7); D4 (Tenant isolation: D4 → D7 → D10) | **NO** |
| **D8** | Capacity / Backpressure Semantics | **RESOLVED — Option 2 (Bounded transport queue + EE pull)** | D2, D5, D6 (Transport implementation: D2 + D5 + D6 + D8 + D9) | **NO** |
| **D9** | Observability Correlation Protocol | **RESOLVED — Option 1 (JSONL over same channel)** | D2, D5, D6 (Transport implementation: D2 + D5 + D6 + D8 + D9) | **NO** |
| **D10** | Network Governance-Check Boundary | **RESOLVED — Option 1 (EE-only governance)** | D7 (Tenant isolation: D4 → D7 → D10) | **NO** |

### D1 — Worker Registration Persistence

Options exactly as documented:
1. **In-memory only (current)**: Accept loss on restart; workers re-register fresh (new instance_id + epoch). EE lease/sweep composes.
2. **Additive SQLite table**: Single-writer (registry), schema mirrors `WorkerIdentity` + `WorkerLiveness` fields, WAL mode, migration path from empty.
3. **External store**: PostgreSQL/etcd/Consul — requires network dependency, not in current stdlib-only stack.

**Owner Decision: RESOLVED — Option 2 (Additive SQLite table)**

Selected by Architecture Owner. Schema mirrors `WorkerIdentity` + `WorkerLiveness` fields, WAL mode, single-writer (registry), migration path from empty.

### D2 — Remote Worker Attestation Depth

Options exactly as documented:
1. **mTLS with control-plane CA**: Certs issued per `worker_instance_id + epoch`; control plane is CA; rotation on re-registration.
2. **SPIFFE/SPIRE**: Workload identity standard; integrates with service mesh; requires SPIRE agent.
3. **Signed registration token**: Control plane signs `worker_id + instance_id + epoch + tenant_scope + expiry`; worker presents token at registration.
4. **Explicit "never" with compensating controls**: No attestation; rely on network segmentation + EE correlation + audit; document as accepted risk.

**Owner Decision: RESOLVED — Option 1 (mTLS with control-plane CA)**

Selected by Architecture Owner. Certs issued per `worker_instance_id + epoch`; control plane is CA; rotation on re-registration. Uses stdlib `ssl`.

### D3 — Worker Epoch / Clock-Skew Semantics

Options exactly as documented:
1. **Logical counter (per-registry)**: Epoch = incrementing integer per `worker_id` managed by registry. No clock dependency. Requires registry as epoch authority.
2. **Hybrid Logical Clock (HLC)**: Combines wall-clock + logical counter; bounded skew tolerance (e.g., ±100ms). Workers and registry sync via HLC.
3. **Wall-clock timestamp (NTP-synced)**: Epoch = `time.time_ns()`; requires NTP sync bound (e.g., ±50ms). Simpler but clock-dependent.
4. **Registry-authoritative epoch**: Registry assigns epoch on registration; workers cannot self-assign. Eliminates races but requires registry availability.

**Owner Decision: RESOLVED — Option 4 (Registry-authoritative epoch)**

Selected by Architecture Owner. Registry assigns epoch on registration; workers cannot self-assign. Eliminates races.

### D4 — business_id-Scoped Identity Boundary

Options exactly as documented:
1. **Propagate `business_id` as `tenant_id` in `RuntimeRequest.metadata` + `DispatchConstraints`**: Minimal change; reuses existing `tenant_scope` filter.
2. **Extend `RuntimeRequest` with explicit `tenant_id` field**: Contract change; requires Phase 3.4 contract amendment.
3. **Separate `business_id` identity boundary at worker**: Worker enforces per-business tool allowlist; requires worker-side governance.
4. **No cross-tenant shared workers**: Each worker instance bound to single `tenant_scope`; simpler isolation.

**Owner Decision: RESOLVED — Option 1 (Propagate `business_id` as `tenant_id` in `RuntimeRequest.metadata` + `DispatchConstraints`)**

Selected by Architecture Owner. Minimal change; reuses existing `tenant_scope` filter.

### D5 — Transport Security Model

Options exactly as documented:
1. **mTLS with control-plane CA**: Certs per `worker_instance_id + epoch`; stdlib `ssl`; cert rotation on re-registration (new epoch = new cert).
2. **SPIFFE/SPIRE**: Workload identity; integrates with mesh; requires SPIRE agent deployment.
3. **TLS + API Key**: Server TLS + client API key in header; simpler; key rotation on epoch.
4. **Noise Protocol / WireGuard**: Modern crypto; kernel/userspace; non-stdlib dependency.
5. **Application-layer only (no transport encryption)**: Rely on network segmentation (VPC, mesh); document as accepted risk.

**Owner Decision: RESOLVED — Option 1 (mTLS with control-plane CA)**

Selected by Architecture Owner. Certs per `worker_instance_id + epoch`; stdlib `ssl`; cert rotation on re-registration.

### D6 — Remote Registration / Heartbeat / Departure Protocol

Options exactly as documented:
1. **HTTP/JSON over TLS (stdlib `http.client` + `ssl`)**: Stdlib-only; RESTful; simple; works with mTLS.
2. **gRPC (requires grpcio dependency)**: Efficient, streaming, codegen; non-stdlib.
3. **WebSocket (stdlib `http.client` upgrade + custom framing)**: Bidirectional; good for heartbeats; more complex.
4. **Custom TCP + JSONL (like SubprocessTransport IPC)**: Familiar pattern; stdlib; no framing standard.

**Owner Decision: RESOLVED — Option 1 (HTTP/JSON over TLS)**

Selected by Architecture Owner. Stdlib-only (`http.client` + `ssl`); RESTful; works with mTLS.

### D7 — Cross-Tenant Network Isolation

Options exactly as documented:
1. **Application-level only (current)**: Tenant filter at registry + dispatch; no network isolation; rely on worker process isolation.
2. **Per-tenant TLS**: Each tenant gets distinct CA/cert; workers present tenant-scoped cert; transport validates.
3. **Service mesh (Istio/Linkerd/Cilium)**: Mesh enforces per-tenant mTZ, authorization policies; requires mesh deployment.
4. **VPC / Network segmentation**: Separate VPCs/subnets per tenant; firewall rules; infrastructure-level.
5. **No shared workers**: Each worker instance bound to single tenant; eliminates cross-tenant at worker level.

**Owner Decision: RESOLVED — Option 5 (No shared workers)**

Selected by Architecture Owner. Each worker instance bound to single `tenant_scope`; eliminates cross-tenant at worker level.

### D8 — Capacity / Backpressure Semantics

Options exactly as documented:
1. **EE-only limits (current)**: EE concurrency limits are hard gate; transport has no queue; `CAPACITY_LIMIT` never returned by transport.
2. **Transport queue depth + EE pull**: Transport has bounded queue (e.g., 100 per worker); EE pulls when slot available; `CAPACITY_LIMIT` if queue full.
3. **Application-level credits**: Transport issues credits to EE; EE spends credit per dispatch; refill on completion; `CAPACITY_LIMIT` if no credit.
4. **TCP backpressure**: Rely on TCP window; transport accepts until socket buffer full; `CAPACITY_LIMIT` on connection refusal.

**Owner Decision: RESOLVED — Option 2 (Bounded transport queue + EE pull)**

Selected by Architecture Owner. Transport has bounded queue (e.g., 100 per worker); EE pulls when slot available; `CAPACITY_LIMIT` if queue full.

### D9 — Observability Correlation Protocol

Options exactly as documented:
1. **JSONL over same channel (SubprocessTransport pattern)**: Worker emits events on stdout; transport forwards to EE event sink; stdlib, same format.
2. **Sidecar event stream (HTTP/gRPC)**: Separate event channel; transport pushes batched events; decoupled from request/response.
3. **Polling from EE**: EE pulls events from transport; EE controls rate; transport buffers.
4. **Structured logging to shared sink**: Both EE and transport write to shared log sink (stdout, file, syslog); correlation via fields.

**Owner Decision: RESOLVED — Option 1 (JSONL over same channel)**

Selected by Architecture Owner. Worker emits events over same channel; transport forwards to EE event sink; stdlib, same format as SubprocessTransport.

### D10 — Network Governance-Check Boundary

Options exactly as documented:
1. **EE-only governance (trust EE)**: Transport assumes EE validated; no re-check; fail-closed only on transport errors. Simplest; preserves EE sole authority.
2. **Transport re-check (sync RPC)**: Transport calls EE governance service before execution; adds latency; EE remains authorizer.
3. **Policy sync + local check**: EE pushes allowlist/policy to transport; transport checks locally; cache invalidation on policy change.
4. **Async validation**: Transport executes optimistically; EE validates asynchronously; rollback on violation (complex, violates "precedes execution").

**Owner Decision: RESOLVED — Option 1 (EE-only governance)**

Selected by Architecture Owner. Transport assumes EE validated; no re-check; fail-closed only on transport errors. Preserves EE sole authority.

---

## 2. DEPENDENCY MAP

```
Security:
D2 (Attestation Depth) → D5 (Transport Security) → D7 (Cross-Tenant Network Isolation)

Worker lifecycle:
D3 (Clock-Skew Semantics) → D1 (Registration Persistence) → D6 (Registration/Heartbeat/Departure Protocol)

Tenant isolation:
D4 (business_id-Scoped Identity Boundary) → D7 (Cross-Tenant Network Isolation) → D10 (Network Governance-Check Boundary)

Transport implementation:
D2 (Attestation Depth) + D5 (Transport Security) + D6 (Registration Protocol) + D8 (Capacity/Backpressure) + D9 (Observability Correlation)
```

All dependency chains are now satisfiable:
- **Security:** D2=1 (mTLS with control-plane CA) → D5=1 (mTLS) → D7=5 (No shared workers) ✔
- **Worker lifecycle:** D3=4 (Registry-authoritative epoch) → D1=2 (Additive SQLite) → D6=1 (HTTP/JSON over TLS) ✔
- **Tenant isolation:** D4=1 (propagate business_id as tenant_id) → D7=5 (No shared workers) → D10=1 (EE-only governance) ✔
- **Transport implementation:** D2=1 + D5=1 + D6=1 + D8=2 + D9=1 all resolved ✔

---

## 3. ARCHITECTURAL INVARIANTS — CONFIRMED PRESERVED

The following frozen architectural invariants are preserved by the selected options:

- Execution Engine remains sole authority for **execution_id**. ✔
- Execution Engine remains sole authority for **attempt lifecycle**. ✔
- Execution Engine remains sole authority for **leases**. ✔
- Execution Engine remains sole authority for **retry/backoff policy**. ✔
- Execution Engine remains sole authority for **task state transitions**. ✔
- Execution Engine remains sole authority for **cancellation policy**. ✔
- Execution Engine remains sole authority for **execution/task timeout policy**. ✔
- Execution Engine remains sole authority for **DAG scheduling**. ✔
- Execution Engine remains sole authority for **tool governance/authorization**. ✔ (D10=1 — EE-only governance)
- Execution Engine remains sole authority for **final persistence**. ✔
- **RemoteWorkerTransport must not become a second execution engine.** ✔ (D10=1 preserves EE sole authority)
- **Worker capabilities remain descriptive and must never become authorization.** ✔ (unchanged)
- **Worker-side governance must not create a second authorization authority.** ✔ (D10=1 — no worker-side governance)
- **tenant_scope must remain a hard isolation boundary.** ✔ (D4=1 reuses existing `tenant_scope` filter; D7=5 eliminates cross-tenant workers)

**Consequences of selected options on invariants:**

| Option | Invariant Impact | Assessment |
|--------|------------------|------------|
| D1=2 (Additive SQLite) | Persists `WorkerIdentity` + `WorkerLiveness`; registry remains single-writer; no EE state persisted | **SAFE** — durability additive only |
| D2=1 (mTLS) | Control plane is CA; certs bound to `worker_instance_id + epoch`; no new authorization authority | **SAFE** — attestation only, capability remains descriptive |
| D3=4 (Registry-authoritative epoch) | Registry assigns epoch; workers cannot self-assign; eliminates split-brain | **SAFE** — registry is epoch authority, not EE authority |
| D4=1 (business_id as tenant_id in metadata) | Reuses existing `tenant_scope` filter; no contract change; no worker-side governance | **SAFE** — preserves EE sole authority |
| D5=1 (mTLS) | Transport encryption + mutual auth; no second authorization authority | **SAFE** — security layer only |
| D6=1 (HTTP/JSON over TLS) | Registration/heartbeat/departure over HTTP; registry operations only; no execution state | **SAFE** — lifecycle protocol only |
| D7=5 (No shared workers) | Each worker bound to single `tenant_scope`; strengthens tenant_scope hard boundary | **SAFE** — strengthens I14 |
| D8=2 (Bounded queue + EE pull) | Transport queue is transport-local; EE pulls when slot available; EE remains capacity authority | **SAFE** — backpressure is transport-local; note: Phase 3.6 I22 "capacity never a hard gate" applies to worker-reported capacity, not transport queue |
| D9=1 (JSONL same channel) | Same format as SubprocessTransport; correlation chain preserved | **SAFE** — observability only |
| D10=1 (EE-only governance) | Transport trusts EE validation; fail-closed on transport errors; no second governance authority | **SAFE** — preserves I6, I15 |

---

## 4. STATUS

```
PHASE 3.8 STATUS:
DECISIONS RESOLVED — READY FOR IMPLEMENTATION REVIEW
```

| Item | Status |
|------|--------|
| D1–D10 owner decisions | **10/10 RESOLVED — ALL EXPLICIT** |
| Production code changed | **NO** |
| Tests changed | **NO** |
| Dependencies added/changed | **NO** |
| Phase 3.7 changed | **NO** |
| RemoteWorkerTransport created | **NO** |
| RuntimeTransport modified | **NO** |
| ExecutionEngine modified | **NO** |
| WorkerRegistry modified | **NO** |
| WorkerMatcher modified | **NO** |
| Hermes modified | **NO** |
| Implementation authorized | **YES — pending implementation review** |

**All D1–D10 have explicit Architecture Owner selections recorded in this document. Phase 3.8 is no longer blocked on architectural decisions.**

---

## 5. ARCHITECTURE OWNER DECISION RECORD

Explicit selections provided by Architecture Owner (Action 8 decision form):

| Decision | Selection | Option Name |
|----------|-----------|-------------|
| D1 | **2** | Additive SQLite persistence |
| D2 | **1** | mTLS with control-plane CA |
| D3 | **4** | Registry-authoritative epoch |
| D4 | **1** | Propagate `business_id` as `tenant_id` in metadata + DispatchConstraints |
| D5 | **1** | mTLS with control-plane CA |
| D6 | **1** | HTTP/JSON over TLS |
| D7 | **5** | No shared workers |
| D8 | **2** | Bounded transport queue + EE pull |
| D9 | **1** | JSONL over same channel |
| D10 | **1** | EE-only governance |

**Next step:** Phase 3.8 implementation review (Action 10) — verify implementation readiness against the newly resolved decisions. No implementation occurs in this action.

---

**PHASE 3.8 ACTION 9 — COMPLETE.**
**STATUS: DECISIONS RESOLVED — READY FOR IMPLEMENTATION REVIEW.**