# HEER_PHASE35_WORKER_FABRIC_GATE.md

**Route A — Phase 3.5 Distributed Runtime / Worker Fabric — Architecture Gate**

| | |
|---|---|
| Phase 3.1 Mission Engine | ACCEPTED — FROZEN |
| Phase 3.2 Task Graph / DAG | ACCEPTED — FROZEN |
| Phase 3.3 Parallel Execution Engine | ACCEPTED — FROZEN |
| Phase 3.4 Hermes Runtime + Contracts + Adapter | ACCEPTED — FROZEN |
| Phase 3.5 Worker Fabric | **THIS GATE — design only, no implementation** |

Status: Architecture gate document. No source code modified during this gate.

---

## 1. Current Architecture (Verified Phase 3.4 Baseline)

Re-verified from: `HEER_PHASE34_HERMES_GATE.md`, `agent/runtime_contracts.py`,
`agent/hermes_runtime.py`, `agent/hermes_adapter.py`, `agent/execution_engine.py`,
`agent/mission_engine.py`, `agent/task_graph.py`, `agent/tools.py`, `agent/approvals.py`,
`agent/audit.py`, `agent/main.py`. Full regression: 135 tests OK; `scripts/acceptance_phase32.py` ALL PASS.

```
HEER                              agent/main.py            [ control plane ]
  → Mission Engine                agent/mission_engine.py  [ control plane ]
  → Task Graph / DAG              agent/task_graph.py      [ control plane ]
  → Parallel Execution Engine     agent/execution_engine.py[ control plane: authority ]
      → RuntimeAdapter.invoke()   agent/hermes_adapter.py  [ boundary seam ]
        → HermesRuntime           agent/hermes_runtime.py  [ execution plane ]
          → tools.call_tool()     agent/tools.py           [ governed tool boundary ]
```

| Component | Plane | Owns |
|---|---|---|
| HEER (HTTP) | control | routing, API surface, request lifecycle |
| Mission Engine | control | mission states, mission_id, mission lifecycle |
| Task Graph | control | task states PENDING/READY/RUNNING/COMPLETED/FAILED/BLOCKED/CANCELLED, DAG, readiness |
| Execution Engine | control | execution_id, attempt_no, leases, retry/backoff, max-attempts, cancellation, timeout policy, final persistence, execution_events |
| Hermes Adapter | boundary | transport-agnostic mapping ONLY; zero EE writes, zero policy decisions |
| Hermes Runtime | execution | one authorized dispatch, cooperative invocation, outcome reporting, transport-local liveness |
| Tool Registry | governance | tool allowlist, sanitization, governed call boundary |
| Approvals | governance | L0–L3 approval gates before dispatch; never bypassed |
| Audit | governance | sole persistent audit trail (`audit.record` + `execution_events`) |

**Control plane = decision + state authority. Execution plane = physical execution
substrate. The Execution Engine is the sole authority over what executes, when, and
with which attempt identity.**

---

## 2. Phase 3.5 Boundary

```
Execution Engine          (control plane — authority)
  ↓  RuntimeRequest
Hermes Adapter            (boundary seam — mapping only)
  ↓  submit/start/cancel/heartbeat/status/result/terminate/recover
Runtime Transport        (Hermes gateway — transport semantics)
  ↓
Worker Fabric            (Phase 3.5: worker registry, capability matching, liveness)
  ↓
Worker                   (execution plane — runs one authorized job)
  ↓
Governed Tool Boundary   (tools.call_tool / tool allowlist / governance)
```

| Layer | Decision/State Authority |
|---|---|
| Execution Engine | execution_id, attempts, leases, retries, backoff, max-attempts, cancellation, timeouts, DAG, mission state, final persistence, audit |
| Hermes Adapter | none — pure mapping (frozen) |
| Hermes Transport / Gateway | transport semantics: queueing, dispatch, outcome finalization (one per execution_id), transport-local heartbeat, bounded handle recovery |
| Worker Fabric (proposed) | worker identity registration, capability *reporting*, placement, liveness reporting — **never** policy, never authorizes |
| Worker | executes exactly one received RuntimeJob; returns one RuntimeResult; **never** transitions task/mission state, **never** creates retries or leases |

Phase 3.4 ends where `HermesRuntime` returns terminal `RuntimeResult` to the adapter.
Phase 3.5 begins where the runtime needs to know *which worker* performed a dispatch and
*which capabilities* that worker can honor — without any of that information becoming
authorization.

---

## 3. Worker Identity Model

| Field | Mutable? | Semantics |
|---|---|---|
| `worker_id` | immutable | canonical public identity registered once per worker (e.g. `w-*`, matching EE lease owners). Globally unique within the execution domain. |
| `worker_instance_id` | immutable per-spawn | one value per process/container spawn; regenerated on restart. Detects worker restart. |
| `worker_epoch` | immutable per-registration | monotonically increasing; a restarted worker is a NEW worker instance with a NEW epoch — the old epoch is stale. |
| `capabilities` | mutable (deployment) | descriptive attributes only — frozen `RuntimeCapabilities` derived + placement attributes (CPU, memory, arch, isolation, tool classes, tenant scope, region, network policy, compliance boundary, runtime version). |
| `transport_identity` | immutable | transport-level identity for control messaging (today: `runtime_id`; future: per-transport credential). |
| `tenant_scope` | immutable per registration | the tenant(s) a worker may serve. Ownership enforcement stays in the EE/control plane. |
| `isolation_mode` | immutable per spawn | NONE / PROCESS / CONTAINER / SANDBOX (frozen `RuntimeIsolation`). |
| `health/liveness` | mutable | registration state: REGISTERED / LIVE / STALE / DEPARTED (fabric-local; never a lease). |
| `resource_limits` | mutable at registration | what the worker reports it can honor (reports capacity; EE enforces policy). |

**Spoofing prevention (conceptual):** worker registration is signed by a fabric-level
credential bound to `worker_instance_id + epoch`; heartbeats carry the same binding; the
EE never accepts worker-claimed state — it accepts only results correlated to the
execution_id the EE itself authorized. A forged worker identity cannot claim an execution
it was never dispatched, because dispatch is EE-initiated and correlation is EE-checked
before any state write.

---

## 4. Job Dispatch Model

```
Execution Engine → RuntimeRequest → Hermes Adapter → Runtime Transport → Worker Fabric → Worker → Tool
    ↑                                                                                           ↓
    └──────────── RuntimeResult ← Hermes ← Adapter ←────────────────────────────── RuntimeResult
```

| Step | Semantics | Idempotency |
|---|---|---|
| submission | EE already claimed READY → RUNNING, incremented attempt_no, persisted execution row. Adapter builds `RuntimeRequest` (`job_id == execution_id`, `idempotency_key == execution_id`). | keyed by execution_id; duplicate submit returns same handle, never a second job |
| acceptance | transport validates request, registers handle, capability pre-check (fail-closed). | single registration per key |
| acknowledgement | transport acknowledges the request; EE continues polling/lease heartbeat. | n/a |
| dispatch | transport assigns to a worker matching *reported* capabilities (descriptive only). | one dispatch per handle |
| execution | worker runs exactly one authorized job through the governed tool boundary. | one live execution per execution_id |
| result | worker returns `RuntimeResult` (SUCCEEDED/FAILED/CANCELLED/TIMED_OUT) with full correlation. | terminal once; later results discarded |
| completion | adapter maps; EE validates, persists terminal task state + events + audit. | EE transition CAS is the single write |
| rejection | transport rejects (AUTH_DENIED, GOVERNANCE_DENIED, CAPACITY_LIMIT, TRANSPORT) → adapter reports error → EE decides (retry or FAILED). | EE policy only |

**Where idempotency applies:** every hop is deduplicated by the frozen pair
`job_id == execution_id` and `idempotency_key == execution_id`. The EE lease-claim CAS
remains the single gate that turns a READY task into a RUNNING attempt — no second live
attempt can ever be created for the same execution_id.

---

## 5. Worker Capability Matching

Placement attributes (Phase 3.6 contract proposal, additive): tool class, CPU, memory,
architecture, isolation mode, network policy, tenant scope, region, compliance boundary,
runtime version.

Rules:
- Worker capability is **descriptive** — it tells placement *where* an already-authorized
  job can run, never *whether* it may run.
- Authorization remains upstream: approvals (L0–L3), tool allowlist, EE attempt claim.
- A worker that lies about capabilities may be *selected* but never *authorized*; the
  result is validated and correlated downstream, so a lying worker cannot cause an
  unauthorized execution to appear authorized.
- Placement is a fabric-optimization concern; it must never be observable as a policy decision.

---

## 6. Lease / Heartbeat Model (Four Layers)

| Signal | Owner | Purpose | Authority? |
|---|---|---|---|
| EE lease | Execution Engine | claim on a RUNNING execution row; lease_owner `w-*`, lease_expires_at, LEASE_EXPIRED sweep | **sole lease authority** |
| runtime heartbeat | transport (Hermes) | liveness of a handle; throttled to the adapter while polling | transport-local |
| worker liveness | Worker Fabric | worker registered/alive; re-registration on restart (new epoch) | fabric-local |
| transport heartbeat | transport ↔ adapter | transport is alive and polling | transport-local |

Modeled cases:

| Case | Behavior |
|---|---|
| worker disappears | worker liveness lost; transport cannot finalize result → lease expires → EE sweep |
| network partition | heartbeats lost both ways; EE lease expires; worker eventually returns → late result discarded (terminal state wins) |
| heartbeat loss | stale signals ignored; only lease TTL drives recovery |
| stale worker | old instance reconnects with old epoch → ignored; new instance registered |
| worker restart | new instance_id + new epoch; old lease allowed to expire; fabric re-registers |
| duplicate worker | duplicate epoch rejected; dispatch goes to the live registered instance |
| delayed result | result arrives after terminal → discarded; EE state unchanged |

**Split-brain prevention:** the EE lease CAS is the only writer of RUNNING→terminal. Two
workers cannot both hold a live execution because the EE never issues a second dispatch for
a terminal execution_id, and the fabric never dispatches a job the EE has not authorized. A
partition can at most produce a *duplicate candidate* result — the EE accepts the first
validated terminal result and discards all later ones.

---

## 7. Idempotency / Duplicate Execution

Invariant: **no two live executions may ever exist for one execution_id.**

| Vector | Defense (existing + proposed) |
|---|---|
| duplicate submit | transport keyed by idempotency_key == execution_id → same handle returned |
| duplicate dispatch | fabric dispatches once per handle; re-dispatch returns the same worker/job ref |
| duplicate worker ack | ack is transport-local; EE sees only results |
| duplicate result | EE accepts one terminal result; later results discarded (terminal CAS already applied) |
| late result | discarded; newer state wins |
| worker retry | forbidden — workers never retry; retry comes only from EE `_schedule_retry` (CAS-guarded single retry row) |
| transport retry | transport-level only, deduplicated by execution_id, invisible to task semantics, never re-invokes a tool after terminal finalize |
| network retry | carrier-level; deduplicated by idempotency_key into the same transport job |

The EE invariant is never weakened: `job_id == execution_id`, `idempotency_key ==
execution_id`, EE claim-CAS is the only gate into RUNNING, and `_schedule_retry` issues
exactly one retry row per attempt under CAS.

---

## 8. Failure / Recovery Model (20 Scenarios)

| # | Scenario | Detection | Authority | Worker behavior | Transport behavior | EE behavior | Persistence | Retry behavior | Final task state | Risk |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Worker crash mid-tool | worker thread gone; result never arrives | EE | — | recover() reports crashed handle (FAILED/CRASH) | lease expiry → LEASE_EXPIRED → re-claim or FAILED | execution_events | EE, if attempts remain | LEASE_EXPIRED → COMPLETED or FAILED | unacknowledged tool side effects |
| 2 | Worker process kill | liveness loss + heartbeat loss | EE | process dead | recover() identifies orphan | lease sweep | events + audit | EE backoff | LEASE_EXPIRED → retry/FAILED | same as #1 |
| 3 | Machine failure | all workers silent; partition | EE | — | transport reports TRANSPORT error | lease TTL expiry | events | EE | LEASE_EXPIRED → FAILED | worker-local data loss (no EE loss) |
| 4 | Network partition | bidirectional heartbeat loss | EE | cannot return result | cancels/terminates local job | lease expiry recovers | events | EE | LEASE_EXPIRED → retry/FAILED | double-dispatch candidate (discarded) |
| 5 | Transport crash | handle gone; submit/status fails | EE | — | — | RUNTIME_UNAVAILABLE event; re-probe | events | EE | FAILED or later COMPLETED | runtime unavailability |
| 6 | Hermes crash | process restarts; in-memory jobs lost | EE | — | no recover(); ephemeral state lost | startup sweep: orphaned RUNNING → LEASE_EXPIRED | executions + events | EE re-dispatch | consistent | ephemeral vs EE truth mismatch |
| 7 | Duplicate dispatch | two workers report same execution_id | EE | second result discarded | dedup at dispatch | first validated terminal wins | no second row | n/a | unchanged | duplicate execution cost |
| 8 | Duplicate result | two terminal results for one execution_id | EE | — | `_finalize` single-writer CAS (first terminal wins) | first terminal persists; second discarded | one row | n/a | unchanged | double tool invocation |
| 9 | Stale heartbeat | worker reports after terminal | EE | — | old signals ignored | no state mutation | none | n/a | unchanged | log noise only |
| 10 | Expired lease | lease_ttl exceeded (default 300s) | EE | — | local job cancelled by transport | sweep → LEASE_EXPIRED → re-claim | execution row | EE may respawn | LEASE_EXPIRED → retry | worker/sweep race (bounded by CAS) |
| 11 | Worker restart | new instance_id/epoch | fabric | re-registers | new handle lifecycle | old lease expires; new dispatches proceed | events | EE | consistent | old-worker late result (discarded) |
| 12 | Scheduler restart | scheduler thread recovered at boot | EE | — | — | scheduler_start() re-sweeps orphaned RUNNING → LEASE_EXPIRED; pending_retries preserved | audit + events | EE re-dispatch | recovered | none |
| 13 | Result timeout | worker exceeds result window after tool return | EE | — | hard-stop grace → runtime_stalled | lease sweep recovers | events | EE | LEASE_EXPIRED chain | post-timeout tool side effects |
| 14 | Cancellation race | cancel requested while RUNNING | EE | cooperative stop; worker returns after tool | cancel_event set; finalizes CANCELLED (or terminal result first) | cancel wins; result-after-cancel discarded | CANCELLED event | no retry | CANCELLED | tool side effect still completed |
| 15 | Timeout/cancel race | monitor fires same tick as cancel | EE | — | `_finalize` CAS — first terminal wins, second discarded | terminal outcome as recorded | one terminal event | per terminal state | TIMED_OUT or CANCELLED (first) | ambiguous outcome (resolved by CAS ordering) |
| 16 | Authorization rejection | non-EE principal attempts dispatch | governance | craft fail | transport rejects AUTH_DENIED | no EE state change | audit (denial) | n/a | unchanged | authz bypass attempts |
| 17 | Capability mismatch | required capabilities unsupported | EE | — | fail-closed at transport (GOVERNANCE_DENIED/TRANSPORT) | FAILED (no retry) or re-dispatch to capable worker | events | EE policy | FAILED | mis-placement |
| 18 | Resource exhaustion | worker at capacity | fabric/worker | queues or rejects CAPACITY_LIMIT | reports capacity rejection | EE holds back or FAILs the attempt | events | EE backoff | FAILED or retried | capacity thundering herd |
| 19 | Malformed result | schema/type/JSON violation | EE | — | transport validates; passes INVALID_RESULT | EE re-validates → INVALID_RESULT → no transition | INVALID_RESULT event | EE decides | FAILED | poisoned state |
| 20 | Poisoned/invalid worker | worker misbehaves repeatedly | fabric | quarantined | stops dispatching to it | only validated results accepted | audit | EE | FAILED or re-dispatch | malicious worker |

---

## 9. Multi-Tenancy

Propagation chain (frozen + future fabric fields):
`tenant_id` (business_id today, from mission context) → `mission_id` → `task_id` →
`execution_id` → `attempt_no` → `runtime_id` → `worker_id` → `correlation_id`.

Isolation boundaries (conceptual, Phase 3.6+):
- No cross-tenant job visibility: workers serve only tenants within `tenant_scope`.
- No cross-tenant execution: EE authorizes per-tenant; fabric placement is tenant-scoped.
- No cross-tenant secrets: secret isolation at the governed tool boundary; secrets never
  in args (vault-resolved references only); logs redacted (frozen `_json_safe_copy` redaction).
- Per-tenant resource pools, per-tenant queues, per-tenant metrics — all *reporting*, never policy.

---

## 10. Security Model

| Threat | Conceptual control |
|---|---|
| Rogue worker (unregistered) | registration + attestation; EE accepts only fabric-routed, correlated results |
| Compromised worker | least privilege; no secrets in args; result validation; quarantine on repeated INVALID_RESULT |
| Forged worker identity | signed registration bound to instance_id + epoch; mutual auth at transport boundary |
| Unauthorized job submission | EE-only dispatch; transport rejects non-EE principals (AUTH_DENIED) |
| Job replay | idempotency_key == execution_id; terminal CAS discards replays |
| Result forgery | correlation (execution_id/job_id/attempt_no) re-validated by EE before any state write; output schema validation |
| Capability spoofing | capability is descriptive; a lying worker may be selected but never authorized |
| Secret leakage | redaction at serialization; vault-resolved references; never pass secrets in args; audit redaction |
| Malicious tool input | EE sanitization at job build; transport re-validates envelope (frozen `_json_safe_copy`) |
| Malicious tool output | EE output validation → INVALID_RESULT; no transition on malformed output |
| Tenant escape | tenant_scope per registration; tenant-scoped placement and secrets; cross-tenant checks in EE |
| Transport interception | mutually authenticated transport channel (future); correlation binding prevents injection |
| Worker impersonation | credential bound to instance_id + epoch; heartbeat binding; EE never accepts worker-claimed identity as authority |

All controls are conceptual for Phase 3.5; none are implemented in this gate.

---

## 11. Resource Governance

| Limit | Enforced by | Reported by |
|---|---|---|
| Global concurrency | Execution Engine (EE `max_concurrent`) | — |
| Per-mission concurrency | Execution Engine (`start_mission(max_concurrent=...)`) | — |
| Per-tenant concurrency | Execution Engine (future, per-tenant policy) | Worker Fabric (usage report) |
| Per-worker concurrency | Worker Fabric (local queue) | Worker (report) |
| CPU / memory | Worker Fabric (cgroup/limits) — capacity report only | Worker |
| Execution duration | Execution Engine (task_timeout, mission_timeout) + transport hard-timeout | transport |
| Queue depth | Worker Fabric (per-worker/per-pool) | Worker Fabric |
| Payload size | EE at job build (input limit) | transport validates |
| Output size | EE at result validation (output limit) | transport validates |

**Principle: the Execution Engine enforces policy; the Worker Fabric and workers only
report capacity.** A worker reporting more capacity than physically available never
increases the amount of authorized work.

---

## 12. Observability

Correlation chain (preserved end-to-end):
`mission_id → task_id → execution_id → attempt_no → runtime_id → worker_id → tool → event`

- Existing: `execution_events` (CLAIMED, STARTED, TOOL_OUTPUT, COMPLETED, RETRY_SCHEDULED,
  RUNTIME_*, LEASE_EXPIRED, TIMED_OUT, CANCELLED) + `audit.record`.
- Future worker events (additive, same stores — **no competing audit system**): WORKER_REGISTERED,
  WORKER_LIVE, WORKER_STALE, WORKER_DEPARTED, DISPATCH_ASSIGNED, DISPATCH_ACKED, WORKER_RECOVERED.
- Metrics (fabric-reported, EE-calculated): worker availability, queue depth, dispatch
  latency, execution latency, worker utilization, retry rate, lease recovery, duplicate
  dispatch, stale workers, capacity rejection, tenant utilization.
- Every worker event carries the full correlation chain; payload redaction frozen.

---

## 13. Deployment Evolution (Stages A–G)

| Stage | Isolation | Latency | Failure model | Ops complexity | Security | Scalability | Cost | Migration impact |
|---|---|---|---|---|---|---|---|---|
| A. In-process | none | lowest | process-coupled | lowest | registry-level | 1 process | ~0 | none (today's Hermes) |
| B. Subprocess | OS process | low–moderate | worker death contained | low | good (process + seccomp optional) | several per host | low | seam only; worker runtime behind transport |
| C. Local container | container | moderate | container restart | moderate | good (cgroups, secrets) | many per host | mid | transport switch; worker packaged as image |
| D. Remote worker | network + OS | high | network partitions | higher | good (mTLS) | horizontal | mid–high | transport switch; no EE change |
| E. Worker pool | network + OS | high | partition/scale-out | higher | good (mTLS, pools) | horizontal + pools | mid–high | fabric registry; EE unchanged |
| F. Kubernetes | pod/namespace | high | cluster-level | highest | excellent (RBAC) | fleet-scale | high | fabric registry on K8s; EE unchanged |
| G. Multi-region | regional pods | regional latency | regional partition | highest | excellent + geo-policy | multi-region | highest | geo-aware placement; EE unchanged |

**Recommended staged path: A (today) → B → C → D → E → F → G, gated on evidence.**
Premature Kubernetes is rejected: HEER is a single-machine SQLite application today;
distributed infrastructure now adds more failure modes than value. Each stage is justified
only by demonstrated need (isolation for crashing tools → B/C; scale or HA → D/E; fleet
management → F; geo → G).

---

## 14. Transport Abstraction

All deployment stages (A–G) preserve the frozen contracts: `RuntimeRequest`,
`RuntimeResult`, `RuntimeHandle`, `RuntimeCapabilities` already carry the required fields
(`transport`, `isolation`, `runtime_id`, `worker_id`, `features`, eight `RuntimeErrorType` values).

**Verification:** no incompatibility found. The seam is transport-agnostic by design;
`HermesRuntime` currently implements INPROCESS, and future transports (SUBPROCESS,
CONTAINER, REMOTE, K8S) implement the same public surface without changing EE semantics.

**If an extension is ever needed** (e.g., worker capabilities beyond the frozen enum),
it must be **additive** — a new Phase 3.6 contract file (`worker_fabric_contracts.py`) that
*references* the frozen contracts, never mutates `agent/runtime_contracts.py` or any frozen source.

---

## 15. Control-Plane / Data-Plane Security Boundary

```
CONTROL PLANE (authority):
  Execution Engine + Task Graph + Mission Engine + Approvals + Tool Governance + Audit + Persistence

DATA / EXECUTION PLANE (substrate):
  Hermes Runtime + (future) Worker Fabric + Workers + Tools
```

Why workers cannot become autonomous agents:
- **Single monotonic authority**: task/mission state is written by exactly one path
  (EE CAS transitions). Autonomous workers would introduce a second writer and break
  atomicity, idempotency, and audit correlation.
- **Governance precedes execution**: approvals (L0–L3), allowlist, and EE attempt claims
  complete upstream. A worker self-authorizing would bypass every gate by construction.
- **Correlation integrity**: the audit trail is only meaningful if every terminal event
  descends from an EE-authorized execution_id. Workers producing independent "decisions"
  would create untraceable state.
- **Recovery determinism**: restarts rely on leases + sweep + retry policy owned by EE.
  Autonomous workers would make recovery non-deterministic.

---

## 16. Future Hermes Runtime Model

```
Execution Engine (transport-agnostic — unchanged)
        ↓  frozen RuntimeRequest / RuntimeResult / RuntimeHandle / RuntimeCapabilities
Hermes Runtime Gateway
├── InProcessTransport    (today: HermesRuntime INPROCESS)
├── SubprocessTransport   (Phase 3.7)
├── ContainerTransport    (Phase 3.7+)
└── RemoteWorkerTransport (Phase 3.8)
```

All transports implement the same runtime semantics: submit/start/cancel/heartbeat/status/
result/terminate/recover; single-writer terminal finalization; cooperative cancellation;
fail-closed governance; transport-local events; no policy authority. The Execution Engine
never needs to know which transport is installed.

---

## 17. Architecture Options

| Option | Alignment with HEER | Verdict |
|---|---|---|
| A. In-process worker pool | perfect — today's HermesRuntime ThreadPoolExecutor; zero behavior change | **basis** |
| B. Subprocess workers | strong — isolation for crashing/misbehaving tools; seam supports it; no EE change | **recommended next stage (3.7)** |
| C. Container workers | strong — resource guarantees + tenant isolation; requires worker image + runtime mgmt | accepted when B evidence justifies |
| D. Centralized remote worker service | requires a network service; carries auth/mTLS/HA complexity; no EE change | deferred (3.8) until multi-host needed |
| E. Queue-based worker fabric | adds a queue/broker dependency; HEER is single-writer SQLite; queue adds more failure modes than value now | **rejected for now** — evaluate only with multi-EE scale evidence |
| F. Kubernetes-native workers | best fleet management but highest ops burden; premature for current single-machine scale | **rejected for now** — revisit at fleet scale |

**Recommendation: extend the transport seam** — keep the Execution Engine and all frozen
contracts untouched; add the Worker Fabric as a Phase 3.6 contract/registry layer on the
execution plane (worker identity, capability reporting, placement, liveness). Implement
SubprocessTransport (Phase 3.7) as the first new transport, then RemoteWorkerTransport
(Phase 3.8). Queue-based and K8s fabrics are explicitly deferred until scale/HA evidence
exists.

---

## 18. Migration Plan (Design-Only)

| Phase | Scope | Design gate status |
|---|---|---|
| Phase 3.5 | Worker Fabric architecture (THIS document) | gate only — no implementation |
| Phase 3.6 | Worker identity/capability contracts (additive `worker_fabric_contracts.py`); worker registry, capability matching, liveness model | proposed — design only |
| Phase 3.7 | Local isolated worker (SubprocessTransport/CONTAINER); resource limits; local worker pool | proposed — design only |
| Phase 3.8 | Remote transport (RemoteWorkerTransport); remote worker registry; transport auth | proposed — design only |
| Future | Distributed worker fabric (queue-based or K8s) — only with scale/HA evidence | open |

No implementation in any future phase without its own architecture gate.

---

## 19. Test Strategy (Design)

Mandatory after any future implementation begins: all existing suites remain green
(`python3 -m unittest discover -s tests -p "*_test.py"` = 135 tests, `scripts/acceptance_phase32.py`).

| Area | Covers |
|---|---|
| Capability matching | placement picks capable worker; never authorizes |
| Duplicate submission | same execution_id twice → one job/one handle |
| Duplicate result | first terminal wins; second discarded |
| Worker crash | lease expiry → recovery/redispatch |
| Network partition | lease expiry; late result discarded |
| Stale worker | old epoch ignored; new instance registered |
| Lease recovery | sweep recovers orphaned RUNNING deterministically |
| Tenant isolation | no cross-tenant dispatch/visibility/secrets |
| Authorization | non-EE principal rejected at transport boundary |
| Malformed results | INVALID_RESULT; no state transition |
| Worker restart | new instance_id/epoch; old lease expires |
| Transport replacement | swap transports; all lifecycle tests re-run green |
| Backward compatibility | frozen 3.1–3.4 suites stay green |
| Deterministic recovery | restart → sweep → pending_retries preserved |
| Concurrency limits | per-mission/per-tenant/per-worker caps enforced |

---

## 20. Risks (≥15)

| # | Risk | Likelihood | Impact | Mitigation | Owner | Phase |
|---|---|---|---|---|---|---|
| 1 | Premature distributed infrastructure | medium | high | staged path gated on evidence | architect | 3.5 |
| 2 | Worker fabric becomes a second scheduler | medium | critical | enforce §15 boundary; EE sole authority invariant I16 | EE + fabric | 3.6+ |
| 3 | Capability spoofing | low | high | capability descriptive; result validation downstream | fabric + EE | 3.6+ |
| 4 | Secret leakage across workers/tenants | medium | critical | never pass secrets in args; vault refs; redaction frozen | governance | 3.7+ |
| 5 | Late results overwrite newer state | medium | high | terminal CAS discards; invariant I8 | EE | 3.6+ |
| 6 | Split-brain double dispatch | low | high | EE single gate into RUNNING; epoch dedup; I7 | EE + fabric | 3.6+ |
| 7 | Unbounded queue depth | medium | medium | queue depth limits (§11) | fabric | 3.7+ |
| 8 | Compromised worker exfiltrating data | medium | high | least privilege; no cross-tenant scope; attestation | security | 3.7+ |
| 9 | Subprocess/container escape | low | critical | OS/container isolation; seccomp/cgroups | security | 3.7 |
| 10 | Transport replacement regressions | medium | medium | transport-conformance suite (§19) | delivery | 3.7+ |
| 11 | Worker restart storms | low | medium | backoff on re-registration; fabric rate limits | fabric | 3.7+ |
| 12 | Cross-process SQLite contention (R1) | medium | high | keep single-writer; fabric never writes EE schema | EE | 3.6+ |
| 13 | Governance bypass via legacy payload tools | medium | high | route all tools through allowlist before dispatch | governance | 3.6 |
| 14 | Resource exhaustion thundering herd | medium | medium | EE holds back per caps; fabric reports capacity only | EE + fabric | 3.7+ |
| 15 | Observability fragmentation (competing audit) | medium | medium | additive events into existing stores; snapshot invariant | delivery | 3.6+ |
| 16 | Worker identity spoofing | low | critical | signed registration bound to instance_id + epoch | security | 3.6+ |
| 17 | Premature locking of contracts (frozen 3.4) | low | high | no mutation; additive 3.6 contract file only | architect | 3.5 |
| 18 | Unplanned multi-EE/multi-writer | low | critical | single-writer until distributed consensus evidence; else new gate | architect | future |
| 19 | Cancellation/timeout races on remote workers | medium | medium | single-writer CAS at EE; transport cancel idempotent | EE + fabric | 3.8+ |
| 20 | Worker job replay of side-effecting tools | low | high | idempotency_key binding; EE retry-only authority | EE | 3.6+ |

---

## 21. Architecture Invariants (I1–I17)

- **I1** — Execution Engine remains the execution authority: it alone creates execution_id, claims attempts, sets leases, decides retries, and persists final state.
- **I2** — A worker cannot mutate task state: no task_graph/mission/execution writes from the execution plane.
- **I3** — A worker cannot create retries: retry issuance is EE-only (`_schedule_retry` CAS).
- **I4** — A worker cannot create leases: lease fields are EE-owned and EE-written.
- **I5** — `execution_id` remains globally unique within the execution domain; `job_id == execution_id`.
- **I6** — `idempotency_key == execution_id` everywhere a request is deduplicated or replayed.
- **I7** — Duplicate dispatch cannot create two live attempts: EE claim-CAS is the single gate into RUNNING.
- **I8** — Late results cannot overwrite newer state: terminal CAS is the only writer; later results are discarded.
- **I9** — Tenant isolation is mandatory: no cross-tenant job visibility, execution, or secrets.
- **I10** — Capability is descriptive, never authorization: workers are selected, never authorized, by capability.
- **I11** — Worker heartbeat/liveness is NOT an EE lease: only the EE lease drives recovery.
- **I12** — Audit correlation remains intact: every event carries mission/task/execution/attempt/runtime/worker/correlation ids; single audit store.
- **I13** — Legacy path remains functional: `tools.call_tool` legacy branch and `handle()` unchanged; installing a runtime is opt-in.
- **I14** — Hermes transport remains replaceable: any transport implementing the frozen surface is swappable without EE/contract changes.
- **I15** — Worker failure remains recoverable by EE: lease expiry + sweep + retry policy fully recover worker loss.
- **I16** — No autonomous worker policy authority: workers decide nothing about what, when, or whether work runs.
- **I17** — No frozen Phase 3.1/3.2/3.3/3.4 contract mutation: any extension is additive (Phase 3.6 file), never a modification of existing contracts/source.

---

## 22. Open Architectural Questions

1. Where does worker registration state live long-term (in-memory fabric registry vs a future additive table)? Left open — no answer invented.
2. What attestation depth is required for subprocess vs container vs remote workers? TBD by Phase 3.6 threat modeling.
3. What are the exact clock-skew bounds for `worker_epoch` across hosts in remote stages? Requires Phase 3.8 network design.
4. Should whole-agent (multi-step) jobs ever be executed by a worker, or does a worker always execute exactly one tool call? Currently single-tool scope; open for Phase 3.6.
5. Does the single-writer Execution Engine need a lease-arbitrated writer shard before any multi-EE scale? Open; explicitly not addressed here.
6. What is the precise resource-reporting contract (CPU/memory units, sampling cadence) for workers? TBD in Phase 3.6 capability schema.
7. Do future remote transports require a separate worker-side identity boundary for `business_id`-scoped tools beyond `tenant_scope`? Open.

---

## 23. Final Architecture Decision

- **Frozen:** Phase 3.1–3.4 contracts, all `agent/*.py` source, all tests, all public APIs. Not modified by this gate.
- **Proposed:** Phase 3.5 Worker Fabric design as documented here (identity model, capability matching, lease/heartbeat layering, idempotency invariants, failure/recovery, multi-tenancy, security, resource governance, observability, deployment evolution A→G, transport-seam extension).
- **Architecture decision:** extend the transport seam — Execution Engine and frozen contracts untouched; Worker Fabric lives on the execution plane as a future additive registry/capability/liveness layer; first new transport is SubprocessTransport (Phase 3.7); queue-based and K8s fabrics explicitly deferred.
- **Remains open:** §22 questions — none resolved by invention in this gate.
- **Must NOT be implemented yet:** no worker fabric code, no new transports, no registry, no capability matching, no worker events, no new dependencies, no new APIs.
- **Exact prerequisites for Phase 3.6 (worker identity/capability contracts):**
  1. This architecture gate approved.
  2. Design-only Phase 3.6 contract file (`worker_fabric_contracts.py` proposal) — additive; frozen files untouched.
  3. Proof that the EE remains the sole authority (invariants I1–I17) under the proposed 3.6 contracts.
  4. Explicit approval to begin Phase 3.6 design with no implementation.

---

## 24. Final Gate

**PHASE 3.5 STATUS: DESIGN COMPLETE — IMPLEMENTATION BLOCKED**

No source code modified.

STOP. Do not proceed to any Phase 3.5/3.6 implementation without explicit approval.