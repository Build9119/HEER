# HEER PHASE 3.6 — WORKER DISPATCH & CAPABILITY MATCHING — ARCHITECTURE GATE

**Status: DESIGN ONLY — no source, test, script, contract, or dependency changes.**
**Baseline reference: 208 tests OK (19.543s) + acceptance_phase32.py ALL PASS (C1–C8).**

---

## 1. AUTHORITATIVE ARCHITECTURE READ (verified against source)

All facts below were verified by reading the actual source this session (execution_engine.py, hermes_adapter.py, hermes_runtime.py in full) plus the prior-session-verified Phase 3.5 registry/contracts.

### 1.1 Execution Engine (`agent/execution_engine.py`) — sole execution authority
- `_claim(task_id, mission_id)` creates the first-attempt execution row: `execution_id = "exe_" + uuid4().hex[:12]`, `attempt_no = 1`, `lease_owner = f"w-{uuid4().hex[:6]}"` (**synthetic random worker id — NOT a registry worker identity**), `lease_expires_at = now + ttl` (default `TTL = 300.0`, configurable `lease_ttl`).
- `_claim_retry(eid)` promotes `RETRY_SCHEDULED → CLAIMED`; `_schedule_retry(e, error, force=False)` creates a **new execution row** with `attempt_no + 1`, `RETRY_SCHEDULED`, backoff `_backoff(n) = min(base·2^(n−1), cap) · jitter`.
- `_sweep()`: expired leases → `LEASE_EXPIRED` → `RECLAIMED` → retry (idempotent, attempt < max) or `FAILED`. `_timeouts()`: `IN_PROGRESS` past `timeout_sec` → `FAILED` → retry or permanent. `_cancels()`: `CLAIMED` + cancel → `ABANDONED`.
- `_dispatch_ready()` / `_dispatch_retries()`: scheduler tick selects ready tasks, claims, and `_dispatch(eid)` → `_executor().submit(_worker, eid)`.
- `_worker(eid)`: `CLAIMED → IN_PROGRESS` CAS, then `_invoke_tool(...)`.
- `_invoke_tool`: with runtime installed → `rt.invoke(execution_id=eid, mission_id=mid, task_id=tid, attempt_no=e["attempt_no"], tool_name=..., task_input=..., timeout_sec=..., cancel_check=..., engine_heartbeat=...)`; without runtime → legacy `tools.call_tool(tool_name, task_input, business_id=biz)`.
- `install_runtime(runtime, **adapter_kw)` wraps the transport in `RuntimeAdapter(runtime, **adapter_kw)`.
- `heartbeat(eid, ttl)` renews `lease_expires_at` for `CLAIMED/IN_PROGRESS` rows.
- Terminal CAS: `_gw(eid, cur, tgt, fields)` — guarded `UPDATE ... WHERE execution_id=? AND status=cur`; late/duplicate writes emit `DUPLICATE_WRITE_REJECTED`.
- `_audit(...)` → `audit.record(request=..., intent=..., agent_id="execution_engine", tools=[intent], inputs={...}, outputs={...}, approval={"blocked": False}, success=..., lat_ms=0)`.
- **The EE contains NO worker selection, NO capability matching, NO registry interaction, NO dispatch decision beyond "which ready task to claim".** The only "worker" concept is the synthetic `lease_owner` string.

### 1.2 Hermes Adapter (`agent/hermes_adapter.py`) — pure mapping seam
- `build_request(...)`: `RuntimeJob(job_id=execution_id, execution_id=execution_id, mission_id, task_id, attempt_no, input, metadata={"tool": tool_name, ...}, timeout_sec, correlation_id=execution_id, capabilities=runtime.capabilities())`; `RuntimeRequest(job, requested_at, requested_by, capabilities_required=capabilities, idempotency_key=execution_id)`.
- `map_result(result)`: `SUCCEEDED → {ok:True, result}`, `CANCELLED → {ok:False, cancelled:True}`, `TIMED_OUT → {ok:False, timed_out:True}`, `FAILED → {ok:False, error}`.
- `RuntimeAdapter.invoke(...)`: build_request → `submit` → `start` → `_poll_result` → `map_result`. On transport stall returns `{ok:False, runtime_stalled:True}` and the EE worker exits **without touching EE state** — the lease sweep remains the single recovery authority.
- `_poll_result`: polls `result()`, calls `cancel_check → runtime.cancel`, throttled `engine_heartbeat` (renews EE lease), throttled `runtime.recover()`, deadline = `timeout_sec + hard_stop_grace (120.0)`.
- **The adapter binds to ONE runtime instance. It has NO worker selection, NO registry interaction, NO capability matching.**

### 1.3 Hermes Runtime (`agent/hermes_runtime.py`) — INPROCESS transport
- `HermesRuntime(*, transport=INPROCESS, isolation=NONE, max_concurrency=8, supports_hard_timeout=True, supports_secrets=False, supports_tenant_isolation=False, governance_check=None, event_sink=None, auto_start=False)`.
- `_runtime_id = "hrm_" + uuid4().hex[:12]`; `capabilities()` returns frozen `RuntimeCapabilities`.
- `submit(request)`: dedup by `idempotency_key`; `RuntimeHandle(handle_id="hrm_"+uuid, execution_id, runtime_id, submitted_at, worker_id=None)`.
- `_run(exec_id)`: optional `governance_check` (**fail-closed only, never grants**), `capabilities_required` feature check (**descriptive gating, never authorization**), then `tools.call_tool(tool_name, raw_input, business_id=biz)` — the governed tool boundary.
- `_finalize`: single-writer CAS; `RuntimeResult(..., runtime_id, worker_id=thread.name, correlation_id, ...)` — **worker_id is the thread name, NOT a registry worker identity**.
- `recover()`: idempotent crash recovery of RUNNING entries whose thread died → `FAILED(CRASH, retryable=True)`. `_monitor_loop`: timeout observation only.
- **No scheduler, no lease, no retry, no task-state authority.**

### 1.4 Worker Registry (`agent/worker_registry.py`) — Phase 3.5, verified
- 8 public methods: `register`, `heartbeat`, `mark_stale`, `depart`, `get`, `list`, `list_by_capability`, `status`. **No `unregister`, no dispatch/schedule/authorize/claim/lease/retry methods** (authority tests 41–44 assert absence).
- Liveness: `REGISTERED / LIVE / STALE / DEPARTED`; epoch supersede; instance binding; heartbeat seq monotonic guard; no zombie revival after DEPARTED.
- In-memory dict + `RLock`; `_entry_dict()` copy semantics; tenant-scoped `list`/`get`; `list_by_capability` is descriptive discovery.
- **Nothing in `agent/*.py` calls WorkerRegistry today — it is not wired into any execution path.**

### 1.5 Contracts (frozen, verified)
- `runtime_contracts.py`: `RuntimeRequest/RuntimeResult/RuntimeHandle/RuntimeCapabilities`; `job_id == execution_id`; `idempotency_key == execution_id`; `correlation_id == execution_id`.
- `worker_contracts.py`: `WorkerIdentity/WorkerCapabilities/WorkerLiveness`; JSON-safe; `redact=False` at worker-contract layer (the `_is_secret_key` match on `"secret"` in `"supports_secrets"` is why).

### 1.6 Governance (verified)
- `tools.call_tool(tool_name, task_input, business_id=biz)` — the governed tool boundary (allowlist + approvals L0–L3 + attempt claim).
- `audit.record(request, intent, agent_id, tools, inputs, outputs, approval, success, lat_ms)` — append-only persistent trail; EE and Hermes both call it; no competing audit system.
- `HermesRuntime.governance_check` — fail-closed only.

### 1.7 What does NOT exist today (verified absence)
- No worker selection / dispatch decision layer.
- No capability matching beyond `list_by_capability` (descriptive query, unwired).
- No scheduling semantics beyond EE's ready-task claim order (`_dispatch_ready` iterates missions/tasks in DB order).
- No capacity/resource governance.
- No worker attestation / cryptographic identity.
- No tenant_scope on missions/tasks/executions (EE has no tenant awareness).
- No cross-process worker fabric.

---

## 2. BASELINE VERIFICATION (recorded this session)

| Check | Command | Result |
|---|---|---|
| Full unit suite | `python3 -m unittest discover -s tests -p "*_test.py"` | **Ran 208 tests in 19.543s — OK** |
| Phase 3.2 acceptance | `python3 scripts/acceptance_phase32.py` | **OVERALL: ALL PASS** (C1–C8) |

Baseline is green. It is the reference point for Phase 3.6. Any Phase 3.6 implementation must keep this green.

---

## 3. PHASE 3.6 BOUNDARY

**"Worker Dispatch & Capability Matching" means:** the layer that, given an already-authorized `RuntimeRequest`, selects an eligible worker candidate from the Worker Registry's descriptive entries and hands the dispatch to the Hermes transport.

```
Execution Engine (authority: execution/attempt/lease/retry/task-state/final persistence)
    ↓ frozen RuntimeRequest (job_id == execution_id, idempotency_key == execution_id)
Hermes Adapter (mapping seam — frozen)
    ↓
Dispatch / Matching Seam (Phase 3.6 — candidate selection ONLY)
    ↓
Worker Registry (descriptive identity/capability/liveness — Phase 3.5)
    ↓
eligible worker candidate
    ↓
Hermes Transport (HermesRuntime INPROCESS today)
    ↓
Worker (executes one authorized job; never policy)
    ↓
Governed Tool Boundary (tools.call_tool / allowlist / approvals)
```

**The Dispatch layer MUST NOT become:** a scheduler, retry engine, lease authority, task-state authority, approval engine, authorization engine, policy engine, audit authority, autonomous agent, or a second execution engine.

**Distinctions (explicit):**
- **MATCHING** = evaluating descriptive worker attributes against a request's descriptive requirements. Produces a candidate list/order. Decides nothing about authority.
- **AUTHORIZATION** = the governance decision that a job may run at all (approvals L0–L3 + allowlist + attempt claim). Owned by governance + EE. MUST precede matching.
- **SCHEDULING** = deciding *when* and *which* ready task to start, respecting concurrency limits. Owned by the EE (`_dispatch_ready`/`_dispatch_retries`). NOT Phase 3.6.
- **EXECUTION** = running the authorized tool within the governed boundary. Owned by the transport + worker.

---

## 4. WORKER SELECTION PRINCIPLE

**Worker capabilities are DESCRIPTIVE. They are NOT authorization.**

A worker reporting tool class X, runtime capability Y, region Z, compliance label Q, or network capability N **never implies** "therefore this worker is authorized to execute the job."

**Correct ordering (frozen):**
1. EE establishes execution authority (claim, execution_id, attempt).
2. Existing governance/approval/allowlist logic establishes authorization.
3. `RuntimeRequest` is created (frozen, `job_id == execution_id`).
4. Dispatch layer evaluates eligible worker descriptions (Phase 3.6).
5. One candidate is selected according to frozen policy semantics (see §10 — currently OPEN).
6. Transport receives the already-authorized dispatch.
7. Worker executes only within the governed tool boundary.

**If a step does not exist today, it is NOT invented.** Current evidence: steps 1–3 and 6–7 exist and are verified. Step 4–5 do not exist (no dispatch layer, no selection). The missing mechanism is marked OPEN (§24).

---

## 5. CAPABILITY MATCHING MODEL

Purely descriptive matching. Attributes are split into **HARD ELIGIBILITY** (can eliminate a candidate) and **SOFT PREFERENCE** (can only rank). Neither is authorization.

| Attribute | Source | Meaning | Authoritative? | Mutable? | Eliminates? | Ranks? | Security implications |
|---|---|---|---|---|---|---|---|
| `tenant_scope` | WorkerIdentity (immutable) | tenant boundary | Yes (identity) | No | **Yes** (hard) | No | Cross-tenant selection must be impossible (§6) |
| `isolation_mode` | WorkerIdentity (frozen `RuntimeIsolation`) | execution isolation | Yes (identity) | No | **Yes** (hard) | No | A job requiring isolation must not land on a non-isolated worker |
| `tool_classes` | WorkerCapabilities (reported) | which tool classes the worker can honor | **No — reported** | At (re)registration | **Yes** (hard, descriptive) | No | Forged tool_classes → worker may fail or misreport; never authorizes |
| `runtime features` | WorkerCapabilities (reported) | cancellation/heartbeat/timeout/secrets/tenant-isolation support | **No — reported** | At (re)registration | **Yes** (hard, descriptive) | No | Mirrors Hermes `capabilities_required` feature check (fail-closed) |
| `max_concurrency` | WorkerCapabilities (reported) | worker-local capacity | **No — reported** | At (re)registration | No | **Yes** (soft) | Dishonest capacity reports are a DoS/quality risk, not an authorization risk |
| `arch` / `platform` | WorkerCapabilities (reported) | binary compatibility | **No — reported** | At (re)registration | **Yes** (hard, descriptive) | No | Mismatch → runtime failure, not security breach |
| `region` | WorkerCapabilities (reported) | locality | **No — reported** | At (re)registration | Optional (policy) | **Yes** (soft) | Data-residency is a policy concern; enforcement is future work |
| `network` / `compliance` labels | WorkerCapabilities (reported) | descriptive labels | **No — reported** | At (re)registration | Optional (policy) | **Yes** (soft) | Labels are claims; no attestation exists (§7) |
| liveness state | Registry (fabric-local) | REGISTERED/LIVE/STALE/DEPARTED | Yes (fabric) | Via heartbeat/mark_stale/depart | **Yes** (hard — see §8) | No | STALE/DEPARTED must never be selected |
| `worker_epoch` | WorkerIdentity (monotonic) | identity generation | Yes (identity) | Via re-registration | **Yes** (hard) | No | Prevents zombie identity selection |

**Rule:** hard attributes filter; soft attributes rank. Filtering is deterministic and tenant-scoped. Ranking is currently OPEN (§10, §24).

---

## 6. TENANT ISOLATION

- Worker `tenant_scope` is immutable in `WorkerIdentity`; registry queries are tenant-scoped server-side; identity cannot override scope (Phase 3.5 verified).
- Job tenant context: **does not exist today** — missions/tasks/executions carry no `tenant_scope` field (verified: EE has no tenant awareness). This is an **OPEN ARCHITECTURAL QUESTION** (§24): tenant context must be propagated from the job to the dispatch layer before tenant-scoped matching can be enforced.
- Candidate filtering: dispatch must filter `list(tenant_scope=job_tenant)` — only same-tenant workers are candidates.
- Cross-tenant rejection: a Tenant A job must never select a Tenant B worker. Until a controlled cross-tenant execution model is explicitly designed (future), this is a hard prohibition.
- Platform/system tenant semantics: none exist today. If a platform tenant is introduced later, it must be explicit and documented; not invented now.
- Tenant identity propagation: the frozen `RuntimeRequest` carries no tenant field. Adding tenant propagation to the request is a **contract change** — must be gated separately, not in Phase 3.6.

---

## 7. CAPABILITY SPOOFING

Worker-reported capabilities are **potentially untrusted**. The gate must not pretend attestation exists.

| Threat | Analysis | Posture |
|---|---|---|
| Forged capabilities | Worker claims tool/region/compliance it lacks | Descriptive only; selection may pick a worker that then fails at the governed boundary. Never authorizes. |
| Stale capabilities | Capabilities changed after registration | Capabilities mutable only at (re)registration; a re-register supersedes. Stale entries are descriptive noise. |
| Downgraded/upgraded capabilities | Worker reports less/more than truth | Same as forged — descriptive only. |
| Worker identity spoofing | `worker_id` is self-claimed | Identity is never authority. EE correlates results to `execution_id` it authorized (gate §3). |
| Worker epoch spoofing | Re-register with new epoch | Epoch is fabric-local monotonic; a newer epoch supersedes. No authority is granted by epoch. |
| Stale worker instances | Old instance+epoch lingers | Instance+epoch binding + DEPARTED terminality + seq guard (Phase 3.5 verified). |
| Compromised workers | Worker executes maliciously | Governed tool boundary (allowlist + approvals) is the control; worker selection adds no authority. |
| Dishonest capacity reports | Over/under-report load | Soft preference only; never eliminates; never authorizes. |

**Explicit distinctions:**
- **IDENTITY** = `worker_id`/`worker_instance_id`/`worker_epoch`/`tenant_scope` — fabric-local, self-claimed, descriptive.
- **CAPABILITY** = reported attributes — descriptive, mutable at registration, never authorization.
- **ATTESTATION** = cryptographic proof of identity/capability — **DOES NOT EXIST**. Preserved as an open question (§24).
- **AUTHORIZATION** = governance decision — owned by approvals/allowlist/EE. Never derived from identity or capability.

---

## 8. WORKER EPOCH AND LIVENESS

Matching interacts with the registry liveness state machine (Phase 3.5, verified):

| State | Eligibility semantics (architectural) | Frozen/Proposed |
|---|---|---|
| `LIVE` | Eligible candidate (subject to hard/soft attributes) | **Proposed** (no dispatch layer exists to consume it) |
| `REGISTERED` | Eligible only if a minimum-liveness policy is defined; otherwise excluded | **Proposed** — default: exclude until first heartbeat promotes to LIVE |
| `STALE` | **Excluded** from candidate selection | **Proposed** — a stale worker must not be selected |
| `DEPARTED` | **Excluded** — terminal per instance+epoch; no zombie revival | **Proposed** — registry already enforces terminality |

- A worker must **not** be selected merely because it exists in the registry.
- Minimum liveness requirement (proposed): candidate must be `LIVE` at selection time. `REGISTERED` may be eligible only if a future policy defines a grace window — not invented now.
- `worker_epoch` correctness: selection must bind to the exact `(worker_id, worker_instance_id, worker_epoch)` triple; a newer epoch supersedes and the old triple is never selected.
- **Frozen:** the registry's state machine itself (Phase 3.5). **Proposed:** the eligibility semantics that consume it (Phase 3.6+).

---

## 9. CAPACITY AND RESOURCE REPORTING

**Preserved principle: Worker reports capacity. Execution/control plane enforces policy.**

- `max_concurrency`, CPU, memory, queue depth, tool capacity, runtime capacity, isolation capacity, rate limits — all are **reported** attributes (soft preference at most).
- **No second resource-governance engine.** The EE's `max_concurrent`/`per_mission` limits are the only concurrency governance that exists today (verified).
- Capacity enforcement (rejecting dispatch because a worker is over capacity) is **NOT implemented** and is **future work** — marked OPEN (§24). Phase 3.6 may use capacity only as a soft ranking signal, never as a hard gate, and never as authority.

---

## 10. SCHEDULING SEMANTICS — MAJOR OPEN QUESTION

**Do NOT silently invent scheduling semantics.** The EE today selects ready tasks in DB iteration order (`_dispatch_ready`); there is no worker-level scheduling at all.

| Approach | Determinism | Fairness | Starvation | Reproducibility | Tenant isolation | Capacity | Failure behavior | Observability | Attack surface | Complexity |
|---|---|---|---|---|---|---|---|---|---|---|
| A. Deterministic first eligible (sorted by worker_id) | High | Low | Possible | High | Easy (tenant filter) | Ignored | Simple (next candidate) | High | Low | Low |
| B. Stable weighted ranking | High (stable tie-break) | Medium | Possible | High | Easy | Soft | Simple | High | Low | Medium |
| C. Least-loaded worker | Low (load varies) | High | Low | Low | Easy | Direct | Medium | Medium | Medium (load spoofing) | Medium |
| D. Capability score | Medium | Medium | Possible | Medium | Easy | Soft | Medium | Medium | Medium (score gaming) | Medium |
| E. Round-robin | Medium | High | Low | Medium | Easy | Ignored | Medium | Medium | Low | Low |
| F. Tenant-aware ordering | High | Medium | Possible | High | Strong | Ignored | Simple | High | Low | Low |
| G. Policy-driven scheduler | Low (policy-dependent) | Policy | Policy | Low | Policy | Policy | Complex | Low | High | High |
| H. Future external scheduler | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Very high |

**Recommendation:** the current architecture can safely support **A (deterministic first eligible)** as the only frozen default — it is reproducible, tenant-safe, low-complexity, and introduces zero new authority. B (stable weighted ranking) is a safe future extension. C–H are **OPEN** and must not be implemented without explicit requirements. **Scheduling order is therefore marked OPEN for anything beyond deterministic-first-eligible.**

---

## 11. DISPATCH AUTHORITY MATRIX

| Authority | Owner (frozen) | Phase 3.6 must NOT change |
|---|---|---|
| Choose candidate | **Dispatch layer (proposed)** — candidate matching only | Must not choose *whether* to run |
| Reject candidate | **Dispatch layer (proposed)** — descriptive hard-attribute filter only | Must not reject the *job* |
| Authorize execution | **Governance** (approvals L0–L3 + allowlist) | Frozen |
| Submit runtime request | **Hermes Adapter** (build_request/submit) | Frozen |
| Claim execution | **Execution Engine** (`_claim`/`_claim_retry`) | Frozen |
| Create attempt | **Execution Engine** (`_claim` attempt_no=1; `_schedule_retry` attempt_no+1) | Frozen |
| Create lease | **Execution Engine** (`_claim` lease_owner/lease_expires_at) | Frozen |
| Retry | **Execution Engine** (`_schedule_retry`, `_handle_failure`, `_sweep`, `_timeouts`) | Frozen |
| Cancel | **Execution Engine** (`cancel_task`, `stop_mission`, `_cancels`, `_finish_cancelled`) | Frozen |
| Finalize | **Execution Engine** (`_gw` terminal CAS) | Frozen |
| Identity/capability/liveness info | **Worker Registry** (descriptive) | Frozen |
| Transport/runtime substrate | **Hermes** (HermesRuntime) | Frozen |
| Authorized execution | **Worker** (governed tool boundary) | Frozen |

**Conflict check:** this matrix matches the actual source (verified §1). No conflict found. No code changes made.

---

## 12. IDEMPOTENCY

Frozen invariants preserved: `job_id == execution_id`, `idempotency_key == execution_id`, `correlation_id == execution_id`.

| Duplicate-dispatch scenario | Behavior (frozen) |
|---|---|
| Duplicate dispatch request | Hermes `submit` dedups by `idempotency_key`; returns existing handle; `TRANSPORT_DUPLICATE_SUBMIT` event |
| Duplicate candidate selection | Same `execution_id` → same `idempotency_key` → dedup at transport |
| Same worker selected twice | Same `execution_id` → dedup; a second execution identity is never created |
| Worker crash after dispatch | Hermes `recover()` → `FAILED(CRASH, retryable=True)`; EE `_sweep`/`_schedule_retry` drives recovery |
| Transport retry | `recover()` is idempotent; bounded to identifiable handles |
| Delayed result | EE `_gw` terminal CAS rejects late writes (`DUPLICATE_WRITE_REJECTED`) |
| Stale worker result | Same terminal-CAS rejection |
| Duplicate callback | `_finalize` single-writer CAS in Hermes; `_gw` CAS in EE |
| Duplicate runtime submission | `submit` dedup + conflicting-identity ValueError |

**The Worker Dispatch layer must never create a second execution identity.** It has no execution_id generation authority.

---

## 13. LEASE INTERACTION

**Explicit:**
- Worker Dispatch does **NOT** own, create, renew, or reclaim leases.
- Worker liveness is **NOT** execution liveness.
- The EE lease/sweep remains authoritative.

| Race scenario | Behavior (frozen) |
|---|---|
| Dispatch + lease expiry | EE `_sweep` marks `LEASE_EXPIRED`; dispatch result later rejected by terminal CAS |
| Worker becomes stale | Registry marks STALE (fabric-local); EE lease unaffected; EE sweep still drives execution recovery |
| Worker disappears | Registry liveness loss + EE lease expiry → `_sweep` → retry or FAILED |
| Late worker result | Terminal CAS rejects; `DUPLICATE_WRITE_REJECTED` |
| New worker takes over after EE recovery | EE `_schedule_retry` creates a new execution row (new `execution_id`); old row terminal |

**No new recovery mechanisms are invented.**

---

## 14. FAILURE MODEL (20+ scenarios)

Each row: scenario / detection / dispatch / registry / Hermes / EE authority / persistence / retry / final task state / security risk / observability.

| # | Scenario | Detection | Dispatch | Registry | Hermes | EE authority | Persistence | Retry | Final state | Security risk | Observability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | No eligible worker | `list_by_capability` empty | No candidate; dispatch deferred | Unchanged | Unchanged | EE decides (lease/sweep) | Unchanged | EE retry policy | Task stays RUNNING until EE timeout/lease | None (no selection) | `NO_ELIGIBLE_WORKER` event (proposed) |
| 2 | All workers stale | Registry status | No LIVE candidate | STALE set | Unchanged | EE lease/sweep | Unchanged | EE retry | FAILED/retry per EE | None | `status()` stale ratio |
| 3 | Worker departs during matching | `depart()` | Candidate invalidated; re-select | DEPARTED | Unchanged | EE | Unchanged | EE | Per EE | None | `DEPARTED` event |
| 4 | Worker stale after selection | `mark_stale()` | Selection re-validated at dispatch | STALE | Unchanged | EE | Unchanged | EE | Per EE | Stale worker execution | `STALE` event |
| 5 | Worker epoch changes | `register()` supersede | Old triple never selected | New epoch | Unchanged | EE | Unchanged | EE | Per EE | Zombie identity | `REGISTERED` (new epoch) |
| 6 | Duplicate registration | `register()` idempotent | Same instance+epoch → duplicate | Duplicate rejected | Unchanged | EE | Unchanged | EE | Per EE | None | `DUPLICATE_REGISTRATION` |
| 7 | Forged capability | None (no attestation) | Worker may be selected then fail | Descriptive | Governed boundary rejects | EE | Unchanged | EE | FAILED | Capability spoofing (descriptive only) | `TOOL_FAILED` |
| 8 | Stale capability | None | Mis-selection possible | Capabilities at registration | Governed boundary | EE | Unchanged | EE | FAILED | Stale claims | `TOOL_FAILED` |
| 9 | Capacity over-report | None | Overloaded worker selected | Descriptive | Worker slow/fails | EE | Unchanged | EE | Per EE | DoS (soft) | `TOOL_FAILED`/latency |
| 10 | Capacity under-report | None | Worker underused | Descriptive | Unchanged | EE | Unchanged | EE | Per EE | None | metrics |
| 11 | Tenant mismatch | Registry tenant filter | Cross-tenant selection impossible | Tenant-scoped | Unchanged | EE | Unchanged | EE | Per EE | **Tenant leakage** | `TENANT_MISMATCH_REJECTED` |
| 12 | Authorization missing | Governance | Dispatch must not proceed | Unchanged | `governance_check` fail-closed | EE | Unchanged | EE | FAILED(GOVERNANCE_DENIED) | Unauthorized execution | `GOVERNANCE_DENIED` |
| 13 | Approval missing | Approvals L0–L3 | Dispatch blocked | Unchanged | Fail-closed | EE | Unchanged | EE | Per EE | Unauthorized execution | audit |
| 14 | Tool unavailable | `tools.call_tool` | Worker lacks tool | Descriptive | `TOOL_FAILED` | EE | Unchanged | EE retry | FAILED/retry | None | `TOOL_FAILED` |
| 15 | Transport unavailable | `submit`/`start` error | Dispatch fails | Unchanged | Adapter returns error | EE | Unchanged | EE | Per EE | None | `RUNTIME_STALLED` |
| 16 | Worker crash | Hermes `recover()` | Unchanged | Liveness loss | `FAILED(CRASH)` | EE `_sweep` | Unchanged | EE | Retry/FAILED | None | `RECLAIMED` |
| 17 | Late result | Terminal CAS | Unchanged | Unchanged | Result delivered | `_gw` rejects | Unchanged | None | Terminal preserved | Result injection (rejected) | `DUPLICATE_WRITE_REJECTED` |
| 18 | Duplicate result | `_finalize` CAS | Unchanged | Unchanged | Single-writer | `_gw` | Unchanged | None | Terminal preserved | Duplicate write (rejected) | `DUPLICATE_WRITE_REJECTED` |
| 19 | Dispatch timeout | Adapter deadline | Dispatch abandoned | Unchanged | `runtime_stalled` | EE lease/sweep | Unchanged | EE | Per EE | None | `RUNTIME_STALLED` |
| 20 | EE lease expiry during dispatch | `_sweep` | Result later rejected | Unchanged | Unchanged | `LEASE_EXPIRED` | Unchanged | EE | Retry/FAILED | None | `LEASE_EXPIRED` |
| 21 | Worker identity spoof | None (no attestation) | Descriptive only | Self-claimed | Governed boundary | EE correlation | Unchanged | EE | Per EE | Spoofed identity (no authority) | audit correlation |
| 22 | Correlation-ID substitution | `correlation_id == execution_id` | Unchanged | Unchanged | Frozen contract | EE validates | Unchanged | None | Terminal preserved | Result injection (rejected) | `DUPLICATE_WRITE_REJECTED` |

---

## 15. SECURITY MODEL

| Threat | Control |
|---|---|
| Capability spoofing | Descriptive-only; governed boundary fail-closed; never authorization |
| Worker identity spoofing | Identity never authority; EE correlates results to authorized `execution_id` |
| Cross-tenant selection | Tenant-scoped registry + tenant-scoped matching (hard filter) |
| Confused deputy | Dispatch layer has no authority to grant; only filters descriptive attributes |
| Stale worker selection | LIVE-only eligibility (proposed) + instance/epoch binding |
| Malicious/compromised worker | Governed tool boundary (allowlist + approvals); worker selection adds no authority |
| Capability escalation | Capabilities mutable only at (re)registration; never grant authority |
| Replay | `idempotency_key == execution_id` dedup; terminal CAS |
| Duplicate dispatch | Transport dedup + EE terminal CAS |
| Result injection | `correlation_id == execution_id`; EE validates result against authorized execution |
| Metadata tampering | JSON-safe copies; `_entry_dict` copy semantics; no internal state exposure |
| Correlation-ID substitution | Frozen contract `correlation_id == execution_id`; EE CAS |
| Unauthorized tool execution | `tools.call_tool` allowlist + approvals L0–L3 + attempt claim |

**Preserved:** Capability ≠ authorization. Worker identity ≠ authorization. Worker selection ≠ authorization.

---

## 16. OBSERVABILITY

Correlation chain preserved:
```
mission_id → task_id → execution_id → attempt_no → runtime/job → worker_id → worker_instance_id → worker_epoch → transport → worker event
```

**Proposed additive events only (NOT implemented):**
- `DISPATCH_CANDIDATES` (eligible set, deterministic order)
- `DISPATCH_SELECTED` (worker_id/instance/epoch + reason)
- `DISPATCH_NO_ELIGIBLE` (no candidate)
- `DISPATCH_TENANT_REJECTED` (cross-tenant attempt blocked)
- `WORKER_REGISTERED` / `WORKER_HEARTBEAT` / `WORKER_STALE` / `WORKER_DEPARTED` (fabric liveness)

**Rules:** additive into existing stores (`execution_events` + `audit.record`); no competing audit system; audit remains authoritative where defined (EE + Hermes `_audit`).

---

## 17. MULTI-TENANCY

- Tenant-scoped registry: exists (Phase 3.5, verified).
- Tenant-scoped matching: proposed (Phase 3.6) — hard filter on `tenant_scope`.
- Platform tenant: none today — OPEN.
- Worker tenant scope: immutable in `WorkerIdentity`.
- Job tenant scope: **does not exist** on missions/tasks/executions — OPEN (§24).
- Cross-tenant prohibition: hard rule; no controlled cross-tenant model invented.
- Future shared-worker model: **OPEN ARCHITECTURAL QUESTION** — a shared worker serving multiple tenants would require explicit tenant-context propagation and isolation guarantees; not designed now.

---

## 18. REMOTE / FUTURE WORKERS

The dispatch abstraction must evolve `InProcess → Subprocess → Container → Remote Worker → Kubernetes/distributed fabric` **without changing** `RuntimeRequest`, `RuntimeResult`, `RuntimeHandle`, execution identity, EE authority, or governance authority.

- The frozen Hermes public surface (`submit/start/cancel/heartbeat/status/result/recover/terminate`) already enables future transports with zero EE changes (verified: adapter is transport-agnostic).
- Phase 3.6's dispatch seam must be transport-agnostic: it selects a **worker candidate** (a registry entry with a `transport_identity`), and the transport binding is a later concern.
- **No future transport is implemented.** SubprocessTransport remains Phase 3.7, gated on evidence.

---

## 19. ARCHITECTURE OPTIONS (six designs compared)

| Criterion | A. Registry-only matching | B. Dispatch service inside EE | C. Independent Dispatch Engine | D. Hermes-owned dispatch | E. External scheduler | F. Policy-driven worker broker |
|---|---|---|---|---|---|---|
| Authority leakage | None | Low (EE already owns scheduling) | Medium (new authority) | Low (Hermes is transport) | High (new authority) | High (policy engine) |
| Complexity | Low | Low | High | Low | Very high | High |
| Scalability | Single-process | Single-process | Multi-process | Single-process | Distributed | Distributed |
| Deterministic behavior | High | High | Medium | High | Low | Low |
| Tenant isolation | Strong (registry filter) | Strong | Strong | Strong | Policy-dependent | Policy-dependent |
| Security | High (no new authority) | High | Medium | High | Medium | Medium |
| Observability | High | High | Medium | High | Medium | Medium |
| Failure recovery | EE lease/sweep | EE lease/sweep | New recovery needed | EE lease/sweep | New recovery needed | New recovery needed |
| Compatibility with current architecture | **High** (registry exists, unwired) | High (EE is the caller) | Low (new process) | Medium (Hermes is transport-only) | Low | Low |
| Migration cost | Low | Low | High | Medium | Very high | High |

**Recommendation: A — Registry-only matching**, implemented as a thin selection function that queries the registry (tenant-scoped, LIVE-only, hard-attribute filter, deterministic order) and returns a candidate. It is the smallest architecture that preserves every frozen authority boundary. B is the fallback if the selection must be embedded in the EE call path, but A keeps the EE untouched. C–F are rejected for Phase 3.6.

---

## 20. API / CONTRACT DESIGN (DESIGN ONLY — no files created)

**Existing contracts are sufficient for the request/result path** (`RuntimeRequest`/`RuntimeResult`/`RuntimeHandle`/`RuntimeCapabilities` — frozen). The dispatch seam needs **no new runtime contract**.

**Proposed conceptual contracts (documented only, NOT created):**

| Concept | Identity | Inputs | Outputs | Immutability | JSON safety | Tenant propagation | Correlation | Failure semantics | Authority limitations |
|---|---|---|---|---|---|---|---|---|---|
| `WorkerCandidate` | `(worker_id, worker_instance_id, worker_epoch)` | registry entry snapshot | candidate dict | immutable snapshot | yes | `tenant_scope` carried | `worker_id` lineage | None (descriptive) | No execution authority |
| `CapabilityMatch` | candidate + matched attributes | candidate caps + request requirements | matched hard/soft attributes | immutable | yes | tenant-scoped | `execution_id` | None (descriptive) | No authorization |
| `DispatchDecision` | `execution_id` + candidate | request + candidate | selected candidate or none | immutable | yes | tenant-scoped | `execution_id` | `NO_ELIGIBLE` | **No claim/lease/retry/authorize** |
| `DispatchConstraints` | policy inputs | tenant, hard attrs, liveness | filter set | immutable | yes | tenant-scoped | n/a | fail-closed | No policy authority |
| `DispatchPolicy` | policy id | ranking rules | order | immutable | yes | tenant-scoped | n/a | fail-closed | No policy authority |

**If existing contracts are sufficient: they are** for the transport path. The dispatch seam may be a pure function over registry entries + request metadata — no new frozen contract required.

---

## 21. TEST STRATEGY (at least 20 areas — NO tests created this phase)

1. Deterministic matching (same input → same candidate order)
2. No eligible worker (empty result, `NO_ELIGIBLE`)
3. Stale worker exclusion (STALE never selected)
4. Departed worker exclusion (DEPARTED never selected)
5. Epoch correctness (old triple never selected; new epoch supersedes)
6. Tenant isolation (cross-tenant selection impossible)
7. Capability matching (hard filter + soft ranking)
8. Capability spoofing (forged caps → descriptive only, no authority)
9. Capability ≠ authorization (selection grants nothing)
10. Duplicate dispatch (same `execution_id` → dedup)
11. Idempotency (`job_id == execution_id`, `idempotency_key == execution_id`)
12. Lease race (dispatch + lease expiry → EE sweep wins)
13. Worker crash (Hermes `recover` + EE `_sweep`)
14. Late result (terminal CAS rejects)
15. Transport failure (`runtime_stalled` → EE lease/sweep)
16. Capacity behavior (soft ranking only; no hard gate)
17. Observability correlation (mission→task→execution→attempt→worker lineage)
18. Legacy compatibility (no-runtime path byte-for-byte)
19. Hermes compatibility (frozen seam untouched)
20. Full regression (208-test baseline stays green)
21. Authority absence (dispatch seam has no claim/lease/retry/authorize methods)
22. Liveness eligibility (REGISTERED excluded by default; LIVE only)

---

## 22. RISKS (at least 20)

| # | Risk | Likelihood | Impact | Mitigation | Owner | Phase |
|---|---|---|---|---|---|---|
| 1 | Scheduler creep (dispatch becomes a scheduler) | Medium | High | Authority tests assert no schedule/claim/lease methods; EE remains sole scheduler | EE owner | 3.6 |
| 2 | Authorization creep (capability treated as authorization) | Medium | High | I3/I10 tests; descriptive-only posture; governed boundary fail-closed | Governance | 3.6+ |
| 3 | Capability trust (forged caps) | High | Medium | Descriptive only; no attestation claimed; governed boundary is the control | Security | 3.6+ |
| 4 | Tenant leakage | Low | High | Tenant-scoped hard filter; identity immutable; cross-tenant rejection test | Platform | 3.6 |
| 5 | Worker spoofing | Medium | Medium | Identity never authority; EE correlation to authorized `execution_id` | Security | 3.6+ |
| 6 | Nondeterministic selection | Low | Medium | Deterministic-first-eligible default; stable tie-break | Dispatch | 3.6 |
| 7 | Starvation | Medium | Medium | Deterministic order + EE concurrency limits; fairness is future work | Dispatch | 3.6+ |
| 8 | Duplicate dispatch | Low | High | `idempotency_key == execution_id`; transport dedup; terminal CAS | EE | 3.6 |
| 9 | Split brain (two dispatch authorities) | Low | High | Single dispatch seam; no second writer; EE sole authority | EE | 3.6 |
| 10 | Stale registry | Medium | Medium | LIVE-only eligibility; heartbeat seq guard; epoch supersede | Registry | 3.6 |
| 11 | Capacity deception | Medium | Low | Soft ranking only; no hard gate; no authority | Dispatch | 3.6+ |
| 12 | Observability gaps | Medium | Medium | Additive `DISPATCH_*`/`WORKER_*` events; audit remains authoritative | Observability | 3.6+ |
| 13 | Remote-worker security | Low (future) | High | Transport-agnostic seam; governed boundary; attestation OPEN | Security | 3.7+ |
| 14 | Policy duplication | Medium | Medium | No policy engine; EE + governance remain sole policy owners | Governance | 3.6+ |
| 15 | Job tenant context missing | High | High | Marked OPEN; no tenant matching until context exists | Platform | 3.6+ |
| 16 | Attestation absence | High | Medium | Explicitly documented; no fake attestation | Security | 3.6+ |
| 17 | Dispatch seam unwired | High | Low | Registry not called today; wiring is a separate gated step | Dispatch | 3.6+ |
| 18 | Contract drift | Low | High | Frozen contracts untouched; mtime/hash verification | All | 3.6 |
| 19 | In-memory registry loss on restart | Medium | Low | Re-register fresh instance+epoch; EE lease/sweep composes | Registry | 3.6 |
| 20 | Late result after terminal | Low | High | Terminal CAS rejects; `DUPLICATE_WRITE_REJECTED` | EE | 3.6 |
| 21 | Cross-process contention | Low (none introduced) | Medium | Zero schema writes; single-writer untouched | EE | 3.6 |
| 22 | Selection re-validation gap | Medium | Medium | Re-validate candidate at dispatch (liveness + epoch) | Dispatch | 3.6 |

---

## 23. ARCHITECTURAL INVARIANTS (18+)

- **I1** EE remains sole execution authority.
- **I2** Worker Registry remains descriptive.
- **I3** Capability never implies authorization.
- **I4** Worker Dispatch never owns leases.
- **I5** Worker Dispatch never owns retries.
- **I6** Worker Dispatch never owns task state.
- **I7** `job_id == execution_id`.
- **I8** `idempotency_key == execution_id`.
- **I9** Tenant isolation is mandatory.
- **I10** Worker epoch prevents zombie identity.
- **I11** Liveness is distinct from execution lease.
- **I12** Late results cannot overwrite terminal EE state.
- **I13** No second audit authority.
- **I14** No autonomous worker policy.
- **I15** Hermes remains transport abstraction.
- **I16** Legacy execution remains compatible.
- **I17** Frozen Phase 3.1–3.5 contracts remain compatible.
- **I18** Worker selection cannot bypass governance.
- **I19** Dispatch creates no second execution identity (new, derived from I7/I8).
- **I20** Dispatch selection is deterministic and tenant-scoped (new, derived from I9).
- **I21** Dispatch re-validates candidate liveness/epoch at dispatch time (new, derived from I10/I11).
- **I22** Worker-reported capacity is never a hard gate (new, derived from I2/I3).

---

## 24. OPEN ARCHITECTURAL QUESTIONS

| # | Question | Why it matters | Current evidence | Known | Unknown | Decision required | Phase |
|---|---|---|---|---|---|---|---|
| 1 | Worker attestation / cryptographic identity | Without it, identity/capability are self-claimed | No attestation exists; identity is descriptive | Identity is never authority | Whether attestation is needed for remote workers | Attestation model (or explicit "never") | 3.7+ |
| 2 | Scheduling-order semantics | Selection order affects fairness/starvation | EE claims ready tasks in DB order; no worker scheduling | Deterministic-first-eligible is safe | Whether weighted/least-loaded is required | Freeze deterministic-first-eligible; defer others | 3.6 |
| 3 | L4 remote-policy entity semantics | Remote workers need policy identity | No L4 entity exists | Transport-agnostic seam | Remote policy model | Define L4 entity or defer | 3.7+ |
| 4 | Capability trust (signed vs reported) | Trust level determines selection risk | Capabilities are reported, mutable at registration | Descriptive only | Whether signing is required | Trust model | 3.6+ |
| 5 | Capacity enforcement model | Overloaded workers degrade quality | Capacity is reported; no enforcement | Soft ranking only | Enforcement mechanism | Enforcement model or defer | 3.6+ |
| 6 | Shared-worker / platform-worker semantics | Multi-tenant shared workers need isolation | No platform tenant; no job tenant context | Cross-tenant prohibition | Shared-worker model | Shared-worker design or defer | 3.6+ |
| 7 | Deterministic selection requirements | Reproducibility of dispatch | Registry `list` is sorted; no selection exists | Deterministic-first-eligible is safe | Whether stronger determinism is required | Freeze determinism requirement | 3.6 |
| 8 | Job tenant context propagation | Tenant-scoped matching needs job tenant | Missions/tasks/executions carry no tenant_scope | Registry is tenant-scoped | How job tenant is established | Tenant-context design | 3.6+ |

---

## 25. FINAL ARCHITECTURE DECISION

**FROZEN (cannot change):**
- EE sole execution/attempt/lease/retry/task-state/final-persistence authority.
- Governance (approvals L0–L3 + allowlist) sole authorization authority.
- `job_id == execution_id`, `idempotency_key == execution_id`, `correlation_id == execution_id`.
- Hermes transport seam (submit/start/cancel/heartbeat/status/result/recover/terminate).
- Worker Registry descriptive identity/capability/liveness (Phase 3.5).
- Governed tool boundary (`tools.call_tool`).

**PROPOSED (Phase 3.6 recommends):**
- A thin, transport-agnostic **dispatch/matching seam** (Registry-only matching, option A) that:
  - queries the registry tenant-scoped,
  - filters to LIVE candidates with matching hard attributes (tool classes, runtime features, isolation, arch/platform, epoch),
  - orders deterministically (first-eligible by `worker_id`),
  - re-validates liveness/epoch at dispatch time,
  - returns a candidate or `NO_ELIGIBLE` — and nothing else.
- No new frozen runtime contract; dispatch is a pure function over registry entries + request metadata.
- Additive `DISPATCH_*`/`WORKER_*` observability events into existing stores.

**OPEN (requires future decision):**
- Scheduling order beyond deterministic-first-eligible.
- Worker attestation / cryptographic identity.
- Job tenant context propagation.
- Capacity enforcement.
- Shared-worker / platform-worker semantics.
- L4 remote-policy entity.
- Capability trust (signed vs reported).

**MUST NOT IMPLEMENT (this phase):**
- No dispatcher logic, no worker assignment, no capability enforcement.
- No subprocess/container/remote/K8s workers.
- No scheduling semantics beyond the proposed deterministic filter.
- No `WorkerCandidate`/`DispatchDecision` code files.
- No modification to WorkerRegistry, Hermes, Execution Engine, or any contract.
- No new dependencies, no new APIs, no runtime behavior change.

**PREREQUISITES (before Phase 3.6 implementation begins):**
1. Explicit approval of this gate.
2. Decision on scheduling order (freeze deterministic-first-eligible or accept OPEN).
3. Decision on whether job tenant context is required before tenant-scoped matching (else matching is tenant-agnostic until context exists).
4. Wiring decision: where the dispatch seam is invoked (adapter call path vs EE call path) — without touching frozen contracts.

**Recommended architecture (smallest safe extension):**
```
EE → Hermes Adapter → [Dispatch/Matching Seam (pure function over registry)] → Worker Registry → Hermes Transport
```
No distributed scheduler. No new authority. No contract change.

---

## 26. VERIFICATION / FILE INTEGRITY

- **Exactly ONE file created/modified this phase:** `HEER_PHASE36_WORKER_DISPATCH_GATE.md`.
- No `agent/*.py` modified.
- No `tests/*` modified.
- No `scripts/*` modified.
- No dependencies added (stdlib-only).
- No APIs added.
- No runtime behavior changed.
- This directory is **not a git repository** (verified previously: `git status` → `fatal: not a git repository`), so filesystem metadata/mtime is the verification method. The only file written in this phase is this gate document.

---

## 27. FINAL REPORT

- **Document created:** `HEER_PHASE36_WORKER_DISPATCH_GATE.md` (this file).
- **Sections completed:** 1–27 (authoritative read, baseline, boundary, selection principle, matching model, tenant isolation, spoofing, epoch/liveness, capacity, scheduling, authority matrix, idempotency, lease interaction, 22-scenario failure model, security model, observability, multi-tenancy, remote workers, 6 architecture options, contract design, 22 test areas, 22 risks, 22 invariants, 8 open questions, final decision, verification, report).
- **Baseline test result:** `python3 -m unittest discover -s tests -p "*_test.py"` → **Ran 208 tests in 19.543s — OK**.
- **Acceptance result:** `python3 scripts/acceptance_phase32.py` → **OVERALL: ALL PASS** (C1–C8).
- **Files changed:** 1 — `HEER_PHASE36_WORKER_DISPATCH_GATE.md`.
- **Files untouched:** all `agent/*.py`, all `tests/*_test.py`, all `scripts/*`, all contracts, all dependencies.
- **Open architectural questions:** 8 (attestation, scheduling order, L4 entity, capability trust, capacity enforcement, shared-worker, determinism, job tenant context).
- **Recommended next phase:** Phase 3.6 implementation (dispatch/matching seam, Registry-only matching, deterministic-first-eligible) — gated on the prerequisites in §25 — or Phase 3.7 (SubprocessTransport) if dispatch is deferred.
- **Explicit STOP:** No implementation of Phase 3.6 was performed. No source, test, script, contract, or dependency was modified. No further changes will be made without explicit approval.

---

PHASE 3.6 STATUS: DESIGN COMPLETE — IMPLEMENTATION BLOCKED