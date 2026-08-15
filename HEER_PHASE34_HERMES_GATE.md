# HEER_PHASE34_HERMES_GATE.md

**Route A — Phase 3.4 Hermes Runtime — Architecture Gate**

| | |
|---|---|
| Phase 3.1 Mission Engine | ACCEPTED — FROZEN |
| Phase 3.2 Task Graph / DAG | ACCEPTED — FROZEN |
| Phase 3.3 Execution Engine | ACCEPTED — FROZEN |
| Phase 3.4 Hermes Runtime | THIS GATE — design only, no implementation |

Status: Architecture gate document. No source code modified during this gate.

---

## 1. Current Architecture Assessment (Frozen Baseline)

Verified from reading: `agent/mission_engine.py`, `agent/task_graph.py`, `agent/execution_engine.py`, `agent/main.py`, `agent/tools.py`, `agent/approvals.py`, `agent/audit.py`, `agent/data.py`, `agent/orchestrator.py`, `agent/heer.py`, `agent/registry.py`, the three test suites, `scripts/acceptance_phase32.py`, `HEER_PHASE33_DESIGN.md`. Phase 3.3 live acceptance PASS (63/63 tests OK).

```
HEER (HTTP server)                agent/main.py
  → Mission Engine                agent/mission_engine.py   (Phase 3.1)
  → Task Graph / DAG              agent/task_graph.py       (Phase 3.2)
  → Parallel Execution Engine     agent/execution_engine.py (Phase 3.3)
      → ThreadPoolExecutor workers (in-process)
      → SQLite leases (lease_ttl, lease_owner w-*)
      → execution attempts (attempt_no, pending_retries)
      → execution_events
  → Tool invocation               agent/tools.py (call_tool via TOOLS registry)
  → Governance                    agent/approvals.py (L0–L3), agent/audit.py
```

### 1.2 Authoritative ownership (must remain true after Hermes)

| Concern | Owner (frozen) | Location | Hermes must |
|---|---|---|---|
| Mission state | mission_engine | `missions` table | read-only |
| Task state | task_graph | `tasks`; PENDING/READY/RUNNING/COMPLETED/FAILED/BLOCKED/CANCELLED | read-only |
| DAG/dependencies | task_graph | `dependencies` + `validate_graph()` | read-only |
| Task readiness | task_graph | `ready_tasks()` | never computes |
| Execution attempts | execution_engine | `executions`, `attempt_no` | never owns |
| Claims/leases | execution_engine | lease_ttl, lease_owner `w-*`, LEASE_EXPIRED | liveness only |
| Worker concurrency | execution_engine | ThreadPoolExecutor, max_concurrent | obeys; exposes caps |
| Retry policy | execution_engine | attempt_no, backoff 0.05→0.3 | none |
| Cancellation | execution_engine | stop/pause/cancel_task | cooperative stop |
| Timeouts | execution_engine | task_timeout, mission_timeout | hard-kill only |
| Recovery | execution_engine | scheduler-start sweep | orphan report |
| Audit/events | execution_engine + audit | `execution_events`, `/api/executions` | EE persistence only |
| Metrics | execution_engine | `metrics()` | feeds stage timings |
| Tool invocation | tools | `call_tool(name, args, business_id)` | governs tool substrate |
| Approvals | approvals | `approvals.sqlite3`, L0–L3 | never bypasses |
| Security | tools registry + approvals | allowlist + levels | sandbox, secrets, caps |

Key facts: single `.heer` SQLite hierarchy with single-writer assumption; scheduler thread polls `ready_tasks()` and claims leases; approvals correlate only via `request_id` (no mission/task/execution columns); agent routing (orchestrator) is a separate older flow from the mission/task/execution path; Phase 3.1 `execute_step` invokes `call_tool` directly.

Frozen: Phase 3.1/3.2/3.3 functions and state machines; all APIs (`/api/missions`, `/api/mission-engine/*`, `/api/execution/*`, `/api/orchestrate`, `/api/chat`, `/api/approvals`, `/api/executions`).

---

## 2. The Hermes Boundary

> **Hermes Runtime is the execution substrate — the physical worker/runtime layer that runs a single, already-governed, already-leased task attempt and returns a result.**

Hermes is: runtime substrate; worker/runtime abstraction; future distributed execution layer candidate. Hermes is **NOT**: a second Mission Engine, second Task Graph Engine, scheduler authority, retry authority, governance/decision engine, approvals engine, or auditor (no competing audit store).

**Where Phase 3.3 ends:** scheduler selected READY task via `ready_tasks()`, acquired lease, incremented `attempt_no`, persisted execution row RUNNING, emitted CLAIMED/STARTED events.
**Where Hermes begins:** EE submits a `RuntimeJob` for that attempt; ends when `RuntimeResult` returns and EE persists COMPLETED/FAILED/CANCELLED. Runtime lifecycle events persist only via EE.

**Boundary invariant:** Hermes never calls `transition_task`, never mutates missions/tasks/executions, never decides retries, never approves tools.

## 3. Future Execution Flow

```
Mission → Task Graph → Governance/Decision → Execution Engine → Hermes Runtime
   → Tool/Agent/Worker → Hermes Runtime → Execution Engine → Task Graph → Mission
```

Boundaries and crossing data:

| # | Boundary | Data crossing | Dir |
|---|---|---|---|
| B1 | Mission → Task Graph | mission_id, objective, metadata | down |
| B2 | Task Graph → Governance | task_id, deps, priority, tool, inputs | down |
| B3 | Governance → EE | approved runnable READY task | down |
| B4 | EE → Hermes | RuntimeJob (execution_id, mission_id, task_id, attempt_no, tool, args, business_id, timeout, caps) | down |
| B5 | Hermes → Tool | governed tool name + sanitized args | down |
| B6 | Tool → Hermes | structured output/error | up |
| B7 | Hermes → EE | RuntimeResult + lifecycle signals | up |
| B8 | EE → Task Graph | COMPLETED/FAILED transition + outputs | up |
| B9 | Task Graph → Mission | terminal state aggregation | up |

Hermes must not directly mutate Phase 3.1/3.2 state — all upward flow returns through B7 → B8.

---

## 4. Portable Runtime Seam (Design Contracts)

Phase 3.3 uses ThreadPoolExecutor + SQLite leases + execution attempts + execution_events + worker dispatch. The seam allows evolving in-process worker → Hermes Runtime → remote/containerized worker → future distributed runtime without changing Mission Engine or Task Graph semantics.

**RuntimeJob** (immutable): job_id (== execution_id, dedup key), mission_id, task_id, attempt_no, tool (allowlisted name), args (sanitized dict), business_id (future tenant_id), timeout (per-attempt hard timeout), capabilities, cancel_token (opaque), correlation_id.

**RuntimeRequest** (action envelope): action in {SUBMIT, START, CANCEL, STATUS, RESULT, HEARTBEAT, TERMINATE, RECOVER}, job_id, auth (caller identity/scopes), payload, correlation_id.

**RuntimeResult**: job_id, status in {COMPLETED, FAILED, CANCELLED, UNKNOWN}, output, error (RuntimeError|None), runtime_meta (worker_id, runtime_id, started_at, finished_at, exit_code, stage_latency_ms, resource_usage), correlation_id.

**RuntimeError**: kind in {TIMEOUT, CRASH, INVALID_RESULT, AUTH_DENIED, GOVERNANCE_DENIED, CAPACITY_LIMIT, TRANSPORT, UNKNOWN}, message, retryable (hint only — EE decides retries).

**RuntimeHandle**: job_id, runtime_id, worker_id, state in {PENDING, STARTED, RUNNING, DONE, FAILED, CANCELLED}, cancel_requested, created_at.

**RuntimeCapabilities**: transport in {INPROCESS, SUBPROCESS, CONTAINER, REMOTE, K8S}, max_concurrency, isolation in {NONE, PROCESS, CONTAINER, SANDBOX}, supports_heartbeat, supports_hard_timeout, supports_secrets, supports_tenant_isolation.

These are **design contracts only** — not implemented.

## 5. Hermes ↔ Execution Engine Contract

| Op | Caller | Input | Output | Idempotency | Auth | Timeout | Failure | Retry | Persistence |
|---|---|---|---|---|---|---|---|---|---|
| submit() | EE scheduler | RuntimeJob | RuntimeHandle | keyed execution_id; dup → same handle | EE principal only | connect timeout | TRANSPORT error → EE keeps attempt | EE | Hermes ephemeral; truth in EE |
| start() | EE scheduler | job_id | handle | no-op if STARTED | same | connect timeout | crash → FAILED handle | EE | EE RUNNING row pre-persisted |
| cancel() | EE stop/pause/cancel_task | job_id | ack | idempotent | same | n/a | terminal → ack | EE | EE task state + events |
| heartbeat() | Hermes worker → EE | job_id, worker_id, seq | ack | monotonic seq; stale ignored | worker token | n/a | loss → lease logic | EE (lease authority) | EE lease fields |
| status() | EE metrics/scheduler | job_id | RuntimeHandle | n/a | same | n/a | unknown → error | n/a | n/a |
| result() | EE collect | job_id | RuntimeResult | once; cancel-bounded | same | collect timeout | malformed → INVALID_RESULT | EE | validated transition only |
| terminate() | EE hard timeout/stop | job_id | ack | idempotent | same | kill grace → SIGKILL | dead → ack | n/a | EE events |
| recover() | EE boot/sweep | job_id | RuntimeResult/orphan | n/a | same | probe timeout | orphan → LEASE_EXPIRED | EE | EE sweep |

- EE remains authoritative for execution attempts — Hermes never increments attempt_no, never transitions task state.
- Hermes never independently retries a task. Only transport-level retries (deduplicated by execution_id, invisible to task semantics) are allowed — never re-invoke a side-effecting tool without a new EE-authorized attempt.

---

## 6. Failure and Recovery Model

Exactly **one authoritative state-transition path**: the EE scheduler (claims, leases, attempts); task_graph the only task-state writer; mission_engine the only mission-state writer. Hermes signals are advisory; EE performs the authoritative transition after validation.

| # | Failure | Detection | Authority | Recovery | Persistence | Retry | Final task state |
|---|---|---|---|---|---|---|---|
| 1 | Hermes unavailable | EE tick / submit error | EE | re-probe; mark blocked; FAILED if unrecoverable | event RUNTIME_UNAVAILABLE | EE backoff 0.05→0.3 | FAILED or later COMPLETED |
| 2 | Hermes crashes mid-job | join/timeout, handle gone | EE | lease expiry → LEASE_EXPIRED → re-dispatch or FAILED | executions + events | EE if attempts remain | RUNNING → LEASE_EXPIRED → retry/FAILED |
| 3 | Worker crashes | heartbeat loss, exit | EE (lease authority) | reclaim lease, redispatch | same | same | same chain |
| 4 | Network interruption | lost heartbeats | EE | lease TTL expiry recovery | NETWORK_LOST event | EE only | LEASE_EXPIRED → retry/FAILED |
| 5 | Runtime timeout | EE timer | EE + terminate() | hard kill SIGTERM→SIGKILL | TIMEOUT event | EE may retry | FAILED(timeout) |
| 6 | Duplicate submission | EE claims READY only; job_id==execution_id | EE | reject / same handle; never double-execute | no new row | n/a | unchanged |
| 7 | Stale lease | lease_ttl exceeded (default 300s) | EE | sweep → LEASE_EXPIRED → re-claim | execution row | EE may respawn | LEASE_EXPIRED → retry |
| 8 | Lost heartbeat | worker not reporting | EE | terminate → reclaim | events | same as 3 | LEASE_EXPIRED chain |
| 9 | Partial result | result() missing output/error | EE | validate → INVALID_RESULT → FAILED | INVALID_RESULT event | EE decides | FAILED |
| 10 | Malformed result | schema/type/JSON mismatch | EE | same as 9 | same | same | FAILED |
| 11 | Cancellation race | result after cancel | EE | cancel wins; result discarded | CANCELLED event | no retry | CANCELLED |
| 12 | Scheduler restart | scheduler thread died | EE boot | scheduler_start() re-sweeps | sweep events | EE re-dispatch | recovered |
| 13 | Process restart | server boot | EE boot | startup sweep: orphaned RUNNING → LEASE_EXPIRED; pending_retries preserved | audit | EE re-dispatch | consistent |
| 14 | Machine restart | same + fsck | EE boot | same; leases carry owner identity so foreign RUNNING rows expire | audit | same | consistent |

## 7. Security / Governance Boundary

Hermes must not bypass HEER governance.

| Control | Today (frozen) | Hermes requirement |
|---|---|---|
| Tool allowlisting | TOOLS registry presence | EE refuses unlisted tools at job build; Hermes re-checks allowlist from job policy — unapproved names never reach runtime |
| Approval gates | approvals.check(level, action, agent_id, request_id) | check completes **before** RuntimeJob; job carries approval/correlation evidence |
| Identity | agent_id / created_by | job carries agent_id + execution_id; Hermes principal is EE-only |
| Mission authorization | mission_engine created_by | stop/cancel validated via EE mission methods; Hermes never self-cancels |
| Tenant isolation | single business, single `.heer` DB | future tenant_id (business_id) propagated; secret/resource namespaces keyed by tenant |
| Secret handling | vault / business config | secrets never in args; vault-resolved references only; logs redacted |
| Input validation | — | EE sanitizes args per tool schema before submit; Hermes re-validates envelope |
| Output validation | — | EE validates RuntimeResult.output; malformed → INVALID_RESULT (no transition) |
| Audit correlation | audit + execution_events (request_id only) | every Hermes event carries execution_id + event_id; approvals gain mission/task/execution correlation |
| Capability restrictions | EE max_concurrent/per_mission | Hermes enforces caps at transport and rejects jobs above caps |
| Sandboxing | none (in-process) | transport-level sandbox per staged evolution |
| Resource limits | — | per-job cpu/mem/timeout enforced by runtime |

**Bypass paths designed against:** unregistered tool submission (blocked at EE + Hermes); orchestrator payload tools called directly without business_id (legacy; Hermes accepts only allowlisted tool names routed via call_tool); approval-free tool execution (approval precedes job); audit escape (all runtime events via EE persist); secret leakage via args/logs (sanitizer + redaction).

---

## 8. Multi-Tenancy / Future Scale

Design for future multiple missions/agents/workers/runtimes/machines/containers/K8s **without prematurely implementing distributed infrastructure today**.

Identifiers propagated at every boundary: `tenant_id` (business_id today, from mission context), `mission_id`, `task_id`, `execution_id` (attempt identity + dedup == job_id), `attempt_no`, `runtime_id` (runtime instance), `worker_id` (worker instance, today `w-*`), `correlation_id` (end-to-end trace).

Constraints: single DB writer today (frozen); distributed later needs a lease-arbitrated writer shard (out of scope, but identifiers are designed now so contracts won't change); multiple runtimes per host via runtime_id namespacing; containers/K8s isolated behind the RuntimeTransport trait; lease TTL remains the single coordination primitive — no distributed consensus now.

## 9. Observability

**Single correlation chain:** `mission_id → task_id → execution_id → attempt_no → runtime_id → worker_id → event_id`.

Existing events (CLAIMED, STARTED, TOOL_OUTPUT, COMPLETED) gain additive types in the same `execution_events` store: RUNTIME_SUBMITTED, RUNTIME_ASSIGNED, HEARTBEAT, TERMINATED, TIMEOUT, INVALID_RESULT, RUNTIME_UNAVAILABLE. Audit payloads (`/api/executions`) remain the single audit surface; every Hermes log/metric carries correlation_id. **No competing audit system.**

## 10. Phase 3.3 Known Risks — Disposition

| Risk | Description | Decision | Rationale |
|---|---|---|---|
| R1 | Cross-process scheduler contention on same SQLite DB (gate tests flaky with live server racing) | **fix during Hermes** — keep as-is now | 3.3 frozen; recovery/leases tolerate it. Hermes adds a runtime/instance layer where a singleticker lease or dispatch broker lives without touching Mission/Task Graph semantics |
| R2 | avg_success_lat_ms null — metrics JSON path (`output ->> '$.lat_ms'`) doesn't match stored output shape | **fix before Hermes** | Hermes needs meaningful stage-latency baselines to prove transport improvements; additive metrics fix only |
| R3 | Manual retry limited to RUNNING tasks with pending retry state | **keep as-is** | Frozen 3.3 semantics; single-authority transition rule. Revisit only via a NEW additive retry API if Hermes flows need it |

---

## 11. Hermes Deployment Options — Evaluation

| Option | Isolation | Latency | Reliability | Security | Complexity | Cost | Observability | Recovery | Scalability | DX |
|---|---|---|---|---|---|---|---|---|---|---|
| A. In-process runtime abstraction | none | lowest | high | registry-level | lowest | ~0 | native (EE) | trivial | 1 process | best |
| B. Thread/process worker runtime | OS threads → subprocess edges | low | high | moderate | low | low | good | good | multi-thread/process | good |
| C. Subprocess sandbox | OS process | moderate | high | good (seccomp optional) | moderate | low–mid | good | good | several/host | good |
| D. Container runtime | container | moderate–high | high | good (cgroups, secrets) | higher | mid | good | good | many/host | moderate |
| E. Remote worker service | network + OS | high | moderate | good (mTLS) | higher | mid–high | good | network complexity | horizontal | moderate |
| F. Kubernetes runtime | pod/namespace | high | high | excellent (RBAC) | highest | high | excellent | strong | fleet-scale | harder ops |

**Recommendation: staged evolution — A → B/C → D → E → F, gated on evidence.**

- Stage 0 (post-gate): in-process ThreadPoolExecutor as default RuntimeTransport — zero behavior change; the seam is the only addition.
- Stage 1: subprocess transport when governance/sandboxing or crashing tools justify isolation.
- Stage 2: container transport when multiple workers/tenants or resource guarantees are needed.
- Stage 3+: remote / K8s **only** when real fleet scale or multi-host HA is required. Premature K8s is rejected: HEER is a single-machine SQLite app; distributed infrastructure now adds more failure modes than value.

---

## 12. API Design — Proposal Only (Additive)

```
GET   /api/runtime/status                # runtime health, transport, capabilities
GET   /api/runtime/jobs                  # active/terminal jobs (bounded, filterable)
GET   /api/runtime/jobs/{job_id}         # RuntimeHandle detail
POST  /api/runtime/jobs/{job_id}/cancel  # cooperative cancel (delegates to EE cancel_task)
GET   /api/runtime/workers               # worker registrations, liveness
GET   /api/runtime/capabilities          # RuntimeCapabilities per transport
```

**Non-goals:** submitting new executions, altering retry policy, changing scheduler config, mutating mission/task state. Inspection + cancel-forwarding only. Does not duplicate `/api/execution/*` or `/api/mission-engine/*` control plane.

## 13. Test Strategy (Hermes Boundary)

**Mandatory:** existing suites stay green after any Hermes work:

```
python3 -m unittest tests.mission_engine_test tests.task_graph_test tests.execution_engine_test   # 63 tests, isolated
python3 scripts/acceptance_phase32.py
```

| Test area | Covers |
|---|---|
| Contract tests | fake inproc + subprocess transports both satisfy RuntimeTransport (interface conformance) |
| Duplicate submission | same execution_id twice → single job, single handle |
| Timeout | hard timeout → RuntimeError TIMEOUT → EE FAILED(timeout); no orphan |
| Cancellation | cancel before/while running; result-after-cancel discarded |
| Crash recovery | kill worker mid-run → heartbeat loss → lease expiry → redispatch |
| Heartbeat loss | stale heartbeats ignored; TTL expiry drives recovery |
| Malformed result | INVALID_RESULT → no task transition; audit event recorded |
| Authorization failure | non-EE principal rejected at runtime boundary |
| Tool governance enforcement | unregistered tool never reaches runtime (rejected at job build) |
| Execution correlation | event chain: mission/task/execution/attempt/runtime/worker/event ids |
| Runtime replacement | swap inproc → subprocess; all lifecycle tests re-run green |
| Backward compatibility | all 63 tests + acceptance_phase32 stay green |

---

## 14. Architecture Decision

**Recommended: Transport-gated Runtime Gateway.** Add a `RuntimeTransport` interface inside the Execution Engine dispatch path. Default implementation is the current in-process ThreadPoolExecutor worker (behavior-preserving). The gateway owns `submit/start/cancel/heartbeat/status/result/terminate/recover` and maps `RuntimeJob`/`RuntimeResult` between the EE and the transport. Later stages add subprocess/container/remote implementations behind the same interface. Stage progression is gated on real scale/stability evidence (R2 metrics first).

**Why it fits HEER:** preserves the single-authority monotonic state model (EE leases/attempts; task_graph the only task-state writer); keeps Phase 3.1/3.2/3.3 contracts and all APIs untouched (additive only); gives Hermes a precise, testable seam without distributed infrastructure; nothing can regress the 63 green tests.

**What remains frozen:** `agent/mission_engine.py`, `agent/task_graph.py`, `agent/execution_engine.py`, `agent/main.py`, all 63 tests, `scripts/acceptance_phase32.py`, all public APIs.

**What Hermes owns:** physical execution substrate (transport choice, worker lifecycle); sandboxing/isolation/capability limits; hard timeout kill enforcement; runtime observability events (via EE persistence); secret/capability injection at the runtime boundary.

**What Hermes must NEVER own:** scheduler authority (claims/leases); retry policy/attempt numbering; task/mission state transitions; governance/approvals/decision authority; audit authority (no competing store).

**Migration path:** (1) add `RuntimeTransport` seam + inproc default (all 63 + acceptance stay green); (2) fix R2 latency metrics; (3) subprocess → container transport as evidence justifies; (4) only then evaluate remote/K8s.

**Risks:** R1 cross-process contention (needs singleticker lease in Hermes stage); R3 retry limiter; governance bypass via legacy orchestrator payload tools (must route through allowlist before Hermes); secret leakage if args/logs unsanitized; premature distribution.

**Open questions:** (1) promote legacy `heer.*` payload tools into TOOLS registry? (2) business_id → tenant_id mapping? (3) approvals gain mission/task/execution columns? (4) single-writer scheduler or multi-process contention tolerance? (5) whole-agent (multi-step) Hermes jobs vs single tools? (6) include resource usage in RuntimeResult.runtime_meta from day one?

**Exact prerequisites for Phase 3.4 implementation:**
1. This architecture gate **approved**.
2. Fix R2 (latency metrics JSON path) — additive, non-contract change.
3. Additive `RuntimeTransport` seam with default inproc transport; all 63 tests + acceptance_phase32 stay green.
4. `/api/runtime/*` endpoints are read/cancel-only.
5. No distributed infrastructure until staged-evolution gating criteria are met.

> **NO HERMES RUNTIME CODE SHOULD BE IMPLEMENTED UNTIL THIS ARCHITECTURE GATE IS APPROVED.**

---

## 15. Final Report (Gate)

- **Files changed:** only `HEER_PHASE34_HERMES_GATE.md` created. No source code modified.
- **Files verified:** mission_engine.py, task_graph.py, execution_engine.py, main.py, tools.py, approvals.py, audit.py, data.py, orchestrator.py, heer.py, registry.py, the three test suites, acceptance_phase32.py, HEER_PHASE33_DESIGN.md; Phase 3.3 live acceptance PASS (63/63 tests OK).
- **Frozen contracts confirmed:** Phase 3.1, 3.2, 3.3 untouched.
- **Hermes boundary:** execution substrate only — between EE dispatch and governed tool execution; never a scheduler/retry/governance/audit authority.
- **Recommended architecture:** transport-gated Runtime Gateway; in-process default; staged evolution to subprocess/container/remote/K8s only on evidence.
- **Risks:** R1 contention; R2 latency metrics gap; R3 retry limiter; governance bypass via legacy payload tools; secret leakage; premature distribution.
- **Open questions:** as listed in §14.

STOP. Do not proceed to Phase 3.4 implementation without explicit approval.
