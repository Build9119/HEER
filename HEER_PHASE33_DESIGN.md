# HEER Phase 3.3 — Parallel Execution Engine (Architecture Design Specification)

> **Status:** DESIGN ONLY — documentation artifact. No source code modified, no runtime behavior introduced.
> Phase 3.1 (Mission Engine) and Phase 3.2 (Task Graph/DAG) are treated as frozen, accepted contracts.
> This document proposes interfaces only. Implementation awaits explicit approval.

---

## 1. CURRENT ARCHITECTURE ASSESSMENT

### 1.1 What exists today (as-built, verified)

| Layer | Module | State storage | Execution coupling |
|---|---|---|---|
| Mission Engine (Phase 3.1) | `agent/mission_engine.py` | `.heer/mission_engine.sqlite3` — `missions` table | Pure state machine + CRUD. **No execution.** |
| Task Graph / DAG (Phase 3.2) | `agent/task_graph.py` | `.heer/task_graph.sqlite3` — `tasks` table | Pure DAG validation + readiness resolution + transitions. **No execution.** |
| Tool dispatch (Phase 3.8) | `agent/tools.py` | — | `call_tool(name, args, business_id) -> dict` — single, synchronous, **never-raises** dispatch surface. Registry-driven. |
| Audit (Phase 1) | `agent/audit.py` | `.heer/executions.sqlite3` — `agent_executions` | `audit.record(...)` — single audit trail, reused by both Phase 3.1 and 3.2. |
| HTTP server | `agent/main.py` | — | `ThreadingHTTPServer` — **already thread-per-request**. |
| Legacy pipeline | `agent/orchestrator.py` `handle()`, `agent/mission.py` | `.heer/missions.sqlite3` | Self-contained legacy mission/DAG system, lowercase statuses, separate DB. Left untouched by 3.1/3.2. |

### 1.2 Key observations that drive the design

1. **Three separate SQLite files with no cross-DB transactions.** 3.1 `mission_engine.sqlite3`, 3.2 `task_graph.sqlite3`, legacy `missions.sqlite3`. Phase 3.3 must follow the same "one file per concern" pattern and compensate across files (no cross-DB foreign keys).
2. **`task_graph.transition_task()` is the authoritative state writer** for tasks; Phase 3.2 already enforces the exact state machine `PENDING → READY → RUNNING → COMPLETED/FAILED`, plus `BLOCKED`/`CANCELLED`. Phase 3.3 must *drive* this API — not bypass it.
3. **`_refresh_readiness()` already implements dependency-aware promotion** (PENDING → READY on dependency completion; PENDING → BLOCKED on FAILED/CANCELLED dependency). Phase 3.3 reuses this for scheduling decisions; no change required to Phase 3.2.
4. **`tools.call_tool()` is the only side-effect boundary** (Phase 3.8 design). The parallel engine must only ever execute tasks by calling `call_tool`; it must never eval/exec strings, spawn shells, or interpret task `input` as code.
5. **The server is already threaded** (`ThreadingHTTPServer`). A `ThreadPoolExecutor` scheduler fits the existing concurrency model and stdlib-only constraint (no asyncio refactor, no Celery/Redis).
6. **Audit is best-effort and single** (`_audit()` wrappers never break the engine). Phase 3.3 follows the identical pattern.
7. **Backward-compat acceptance (C5–C8 in `scripts/acceptance_phase32.py`)** requires legacy endpoints and `orchestrator.handle()` to keep working. Phase 3.3 is a **new opt-in layer** — `handle()` unchanged.
8. **Existing task lifecycle headers already match the required Phase 3.3 states exactly** (`PENDING/READY/RUNNING/COMPLETED/FAILED/BLOCKED/CANCELLED`). Phase 3.3 adds *attempt-level* concepts (execution ID, lease, retry) *around* these states, without changing them.

### 1.3 Gap being filled by Phase 3.3

Phase 3.1 and 3.2 model missions and DAGs but **nothing executes tasks**. Today a human must manually call `transition_task(..., "RUNNING")` then `"COMPLETED"` via the API. Phase 3.3 adds the missing **scheduler + workers + lease/retry/recovery layer** between the DAG and the future Hermes Runtime:

```
HEER
  ↓
Mission Engine (3.1)          ← frozen
  ↓
Task Graph / DAG (3.2)        ← frozen
  ↓
[Phase 3.3 Parallel Execution Engine]   ← NEW (this design)
  ↓
Future Hermes Runtime
```

---

## 2. PROPOSED PHASE 3.3 ARCHITECTURE

### 2.1 High-level concept

A **single-process, stdlib-only, in-process parallel scheduler** (`agent/execution_engine.py`) built on `concurrent.futures.ThreadPoolExecutor`, a **SQLite-backed lease/claim model**, and **poll-driven dependency-aware scheduling** that layers on top of Phase 3.2's existing readiness semantics.

### 2.2 Design principles

1. **Zero changes to Phase 3.1/3.2 modules.** 3.3 *calls* `task_graph.transition_task()`, `task_graph.ready_tasks()`, `mission_engine.transition()` — it never modifies them.
2. **One new module + one new SQLite file.** `agent/execution_engine.py` + `.heer/execution_engine.sqlite3` (tables: `executions`, `execution_events`, `scheduler_config`).
3. **Tasks are units of work; executions are units of retry.** One task → possibly multiple execution attempts, each with a unique `execution_id`.
4. **Claim, don't mutex.** Workers *claim* RUNNING status in SQLite atomically; the lease (`lease_expires_at`) provides crash-detection without a distributed lock.
5. **All failures are scheduled, not swallowed.** Worker crash, timeout, dependency failure → deterministic transitions via the existing state machine.
6. **Backward compatible.** `orchestrator.handle()` / `/api/chat` / legacy endpoints untouched. Phase 3.3 is opt-in via new API routes.

### 2.3 Module responsibilities

| Component | Responsibility |
|---|---|
| `Scheduler` | Main loop: discover READY tasks → claim → dispatch to executor. Manage global + per-mission concurrency. Handle recovery sweep. |
| `Worker` | Execute one claimed execution: call `tools.call_tool()`, write result, transition task, resolve dependencies. |
| `LeaseManager` | Insert/refresh/expire execution leases; detect orphaned RUNNING tasks; prevent duplicate execution. |
| `RetryPolicy` | Backoff/max-attempts logic; decision: retry vs permanent FAILED. |
| `CancellationCoordinator` | Cooperative cancel: set `cancel_requested`, worker checks between tool calls; cascades to dependents. |
| `TimeoutGuard` | Task-level timeout enforcement; mission-level timeout; heartbeat staleness check. |
| `MetricsCollector` | Execution counters, durations, per-status aggregates; feeds observability + audit. |
| `RecoveryEngine` | Startup sweep: reclaim expired leases, orphaned RUNNING tasks, resume/FAIL missions. |

---

## 3. COMPONENT DIAGRAM

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            HTTP Layer (main.py — extended)                │
│   /api/mission-engine/missions/{id}/execute        POST  (start mission)   │
│   /api/execution-engine/executions                GET   (list)             │
│   /api/execution-engine/executions/{exec_id}      GET   (detail)           │
│   /api/execution-engine/executions/{exec_id}/cancel  POST                  │
│   /api/mission-engine/missions/{id}/execute/cancel  POST                   │
│   /api/execution-engine/metrics                   GET                      │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼────────────────────────────────────────────┐
│                    execution_engine.Scheduler (new)                        │
│   ┌─────────────┐   ┌──────────────┐   ┌───────────────────────────────┐  │
│   │  Scheduler  │──▶│  WorkerPool  │──▶│  Worker (per execution_id)    │  │
│   │  loop       │   │ ThreadPool   │   │  claim → call_tool → write    │  │
│   │             │   │ Executor     │   │  result → transition_task     │  │
│   └──────┬──────┘   └──────────────┘   └───────────────┬───────────────┘  │
│          │                                             │                  │
│   ┌──────▼─────────────────────────────────────────────▼──────────────┐   │
│   │  LeaseManager │ RetryPolicy │ CancellationCoordinator │           │   │
│   │  TimeoutGuard │ RecoveryEngine │ MetricsCollector                  │   │
│   └──────┬────────────────────────────────────────────────────────────┘   │
└──────────┼────────────────────────────────────────────────────────────────┘
           │  calls (read-only + transitions; zero modification)
┌──────────▼───────────────────────────────────────────┐   ┌────────────────┐
│ Phase 3.1 mission_engine (missions table)            │   │ audit.record   │
│ Phase 3.2 task_graph (tasks + _refresh_readiness)    │   │ (single audit) │
└──────────┬───────────────────────────────────────────┘   └───────┬────────┘
           │                                                       │
┌──────────▼───────────────────────────────────────────┐           │
│             tools.call_tool(name, args, business_id) │◀──────────┘  (audit per
│             ── ONLY side-effect boundary ──          │             execution
└──────────┬───────────────────────────────────────────┘
           ▼
   vault / missions / developer / github / n8n / deploy / terminal
```

---

## 4. STATE TRANSITIONS

### 4.1 Task states (Phase 3.2 — unchanged, authoritative)

```
            (deps complete)             (worker claims)
 PENDING ─────────────────▶ READY ─────────────────▶ RUNNING ──────▶ COMPLETED
     │                          │                        │              ▲
     │  (dep failed/cancelled)  │  cancel                 │ fail         │
     ▼                          ▼                         ▼              │
  BLOCKED ──────────▶ CANCELLED                    (retries left?)        │
                           ▲                           │                  │
                           │                          YES  NO            │
                           └──────────────────────────┴────┴──────────────┘
                                       (back to READY via PENDING)
```

**Phase 3.3 adds semantics ON TOP (no new task states):**

| Trigger | Preconditions | Action |
|---|---|---|
| READY → RUNNING | execution lease acquired, `execution_id` created | `transition_task(READY→RUNNING)` + insert `executions` row |
| RUNNING → COMPLETED | worker finished `call_tool` with `ok=True`, `execution_id` matches current lease | `transition_task(RUNNING→COMPLETED, output=...)` + update execution row |
| RUNNING → FAILED (permanent) | tool failed or `call_tool` raised, retries exhausted | `transition_task(RUNNING→FAILED, error=...)` |
| Retry | tool failed, retries remain | New execution attempt (fresh `execution_id`, `attempt_no+1`) via `RETRY_SCHEDULED`; task stays RUNNING between attempts (no illegal RUNNING→READY transition) |
| RUNNING → CANCELLED | cooperative cancel received, worker observed `cancel_requested` | `transition_task(RUNNING→CANCELLED)` |
| FAILED / CANCELLED cascade | mission cancelled or task FAILED permanently | Phase 3.2 `_refresh_readiness()` promotes dependents PENDING → BLOCKED (existing behavior) |

### 4.2 Execution attempt states (new, in `executions` table)

```
      CLAIMED ──▶ IN_PROGRESS ──▶ COMPLETED
          │             │
          ▼             ▼
      LEASE_EXPIRED  FAILED (permanent or retrying)
          │             │
          ▼             ▼
      RECLAIMED      RETRY_SCHEDULED ─▶ CLAIMED (next attempt)
```

### 4.3 Mission states (Phase 3.1 — unchanged)

`RUNNING → PAUSED → RUNNING` remains legal; Phase 3.3 must respect pause: scheduler pauses claiming when mission is PAUSED; resume re-enters claiming loop. Mission `CANCELLED` cascades task cancellation (§8).

---

## 5. EXECUTION ALGORITHM

### 5.1 Scheduling loop (poll-based, deterministic)

```
loop every SCHEDULER_POLL_INTERVAL (default 0.5s), while scheduler_running:
  1. sweep_expired_leases()                 # lease/worker-crash reclaim
  2. enforce_timeouts()                     # task/mission timeout guard
  3. honor_cancellations()                  # propagate cancel flags
  4. for each mission in active_missions()  # mission_engine status in RUNNING/READY:
        if mission is PAUSED → skip
        if per_mission_active(mission) >= per_mission_limit → skip
        ready = task_graph.ready_tasks(mission_id).ready   # deterministic order
        for task in ready (in order, respecting priority):
            if global_active >= max_concurrent_tasks → break
            claim_and_dispatch(task)        # returns execution_id
  5. idle-sleep until next poll
```

### 5.2 Claim-and-dispatch (the atomic unit)

```
def claim_and_dispatch(task, mission_id):
    # Single SQLite transaction on execution_engine.sqlite3 (WAL, BEGIN IMMEDIATE)
    with immediate_tx():
        cur = task_graph.get_task(mission_id, task_id)      # re-read
        if cur.status != READY: return ("skipped", None)    # claimed by someone else
        execution_id = "exe_" + uuid.hex[:12]
        attempt_no = next_attempt(task_id)
        insert executions (execution_id, task_id, mission_id, status='CLAIMED',
                           attempt_no, lease_owner, lease_expires_at=now+LEASE_TTL,
                           max_attempts, input_snapshot=task.input)
        # Transition READY → RUNNING through Phase 3.2's OWN state machine
    r = task_graph.transition_task(mission_id, task_id, "RUNNING")
    if not r.ok:
        rollback execution row (mark ABANDONED)            # lost race
        return ("lost_race", None)
    executor.submit(worker, execution_id)                  # non-blocking
    return ("dispatched", execution_id)
```

**Duplicate-execution prevention:** claim-insert before `READY→RUNNING` transition; `transition_task` re-reads status atomically, so a second claimer fails and rolls back. This is "claim, then confirm".

> **Cross-file atomicity:** SQLite cannot join transactions across files. Mitigation: (a) claim-first-insert, (b) transition as serial commit point, (c) one live execution per task, (d) lease expiry as crash backstop.

### 5.3 Worker (per execution)

```
def worker(execution_id):
    claim = lease_manager.checkout(execution_id)     # CLAIMED → IN_PROGRESS
    if claim is None: return                          # already superseded
    task = load task + mission_id + business_id
    audit.record(intent="task_execution_start", ...)
    try:
        result = tools.call_tool(task.tool, task.input, business_id)   # NEVER raises
        if result.get("ok") is True:
            transition_task(mission_id, task_id, "COMPLETED", output=result)
            execution.status = COMPLETED; write result; finish
        else:
            failure_path(execution_id, error=result.get("error"))
    finally:
        lease_manager.release(execution_id)
        task_graph._refresh_readiness(mission_id)     # fan-out (Phase 3.2)
        audit.record(intent="task_execution_end", success=..., lat_ms=...)
```

### 5.4 Failure path / retry policy

```
def failure_path(execution_id, error):
    e = executions[execution_id]
    e.status = FAILED
    e.error = error[:MAX_ERROR]
    if e.attempt_no < e.max_attempts:
        delay = min(BACKOFF_BASE * (2 ** (e.attempt_no - 1)), BACKOFF_CAP)  # 1,2,4,...cap
        schedule_retry(execution_id, delay)   # task stays RUNNING
        return
    # permanent failure:
    transition_task(mission_id, task_id, "FAILED", error=e.error)   # Phase 3.2 enforces
    _refresh_readiness(mission_id)   # dependents → BLOCKED (existing 3.2 behavior)
```

Retry re-claim: timer wakes after `delay`, re-checks task still RUNNING with this execution as last attempt, inserts new execution row (`attempt_no+1`, fresh lease), dispatches new worker. **Task never leaves RUNNING between attempts.**

### 5.5 Idempotency

| Layer | Mechanism |
|---|---|
| Execution ID | Globally-unique per attempt (`exe_<12-hex>`); PK; audit/metrics correlate on it. |
| Retry safety | Retry only for tools declaring `idempotent: true`; non-idempotent failures → permanent FAILED, never auto-retried. |
| Duplicate worker protection | Final write guarded by `WHERE execution_id=? AND status='IN_PROGRESS'` — first write wins; second rejected (`superseded`). |
| Transition guard | `transition_task` rejects terminal-state transitions; double-complete impossible. |

---

## 6. PERSISTENCE MODEL

### 6.1 New file: `.heer/execution_engine.sqlite3` (same `.heer/` pattern as 3.1/3.2)

```sql
PRAGMA journal_mode=WAL;

CREATE TABLE executions (
    execution_id  TEXT PRIMARY KEY,   -- exe_<12-hex>  (per attempt)
    task_id       TEXT NOT NULL,
    mission_id    TEXT NOT NULL,
    attempt_no    INTEGER NOT NULL DEFAULT 1,
    status        TEXT NOT NULL,      -- CLAIMED|IN_PROGRESS|COMPLETED|FAILED|
                                      -- RETRY_SCHEDULED|LEASE_EXPIRED|RECLAIMED|ABANDONED
    lease_owner   TEXT NOT NULL,
    lease_expires_at REAL NOT NULL,
    input_snapshot TEXT,              -- copy of task.input at claim time (JSON)
    output        TEXT,
    error         TEXT,
    timeout_sec   REAL,
    max_attempts  INTEGER,
    cancel_requested INTEGER NOT NULL DEFAULT 0,
    created_at    REAL NOT NULL,
    updated_at    REAL NOT NULL,
    started_at    REAL,
    finished_at   REAL
);
CREATE INDEX ix_exec_task    ON executions(task_id);
CREATE INDEX ix_exec_mission ON executions(mission_id, status);
CREATE INDEX ix_exec_lease   ON executions(lease_expires_at, status);

CREATE TABLE execution_events (    -- append-only structured observability log
    event_id   TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL,
    task_id    TEXT NOT NULL,
    mission_id TEXT NOT NULL,
    event_type TEXT NOT NULL,      -- CLAIMED|STARTED|TOOL_OUTPUT|COMPLETED|FAILED|
                                   -- RETRY_SCHEDULED|CANCELLED|TIMEOUT|LEASE_EXPIRED|RECLAIMED
    payload    TEXT,
    ts         REAL NOT NULL
);
CREATE INDEX ix_events_exec   ON execution_events(execution_id);
CREATE INDEX ix_events_mission ON execution_events(mission_id, ts);

CREATE TABLE scheduler_config (
    key   TEXT PRIMARY KEY,         -- max_concurrent_tasks, per_mission_limit,
    value TEXT NOT NULL             -- lease_ttl_sec, backoff_base_sec, backoff_cap_sec,
);                                  -- default_timeout_sec, mission_timeout_sec, poll_interval
```

### 6.2 Cross-file integrity rules (no cross-DB FKs)

| Relationship | Rule |
|---|---|
| `executions.mission_id` → `mission_engine.missions` | Validated at `start_mission()`; compensated on mission cancel/delete. |
| `executions.task_id` → `task_graph.tasks` | Validated at claim (`get_task` None → ABANDONED). |
| Task status vs executions | Invariant: task `RUNNING` ⇔ exactly one live execution (`CLAIMED`/`IN_PROGRESS`). Enforced by live-execution uniqueness + lease sweep. |

### 6.3 What is NOT persisted

Task output stays authoritative in `task_graph.tasks.output` (Phase 3.2). Executions store only the attempt-level envelope (who, when, lease, attempt, retry decision).

---

## 7. CONCURRENCY MODEL

### 7.1 SQLite locking

| Concern | Approach |
|---|---|
| `execution_engine.sqlite3` writes | `PRAGMA journal_mode=WAL`; claim/lease-updates inside `BEGIN IMMEDIATE` (writers serialize). Transactions stay **short** (<2ms) — no tool calls inside a transaction. |
| Phase 3.2 `tasks` status writes | Already serialized by SQLite single-writer semantics; 3.3 calls its functions, never raw SQL. |
| Phase 3.1 `missions` writes | Same — via `mission_engine.transition()`. |
| Lock collisions | `sqlite3.connect(timeout=30)` + `busy_timeout` pragma + jittered retry (existing pattern). |
| Cross-file atomicity | Impossible; compensated via claim-first-insert + startup failsafe sweep. |

### 7.2 Atomic state transitions

- Task status changes: only via `task_graph.transition_task()` (single writer, validates inside one DB).
- Mission status changes: only via `mission_engine.transition()`.
- Execution status changes: guarded compare-and-swap `UPDATE executions SET status=? WHERE execution_id=? AND status=?`.

### 7.3 Race conditions and defenses

| Race | Defense |
|---|---|
| Two schedulers claim same READY task | Claim-insert + guarded `READY→RUNNING` transition; loser rolls back. |
| Two workers complete same execution | `WHERE execution_id=? AND status='IN_PROGRESS'` — first write wins. |
| Retry timer fires after cancel/fail | Re-checks `status='RETRY_SCHEDULED'` AND task RUNNING AND no newer attempt. |
| Cancel races worker completing | `cancel_requested=1` guards final write; worker transitions `RUNNING→CANCELLED` instead. |
| Lease expiry while worker slow | Heartbeat every 30s updates `lease_expires_at`; sweep requires expiry AND stale heartbeat. |

### 7.4 Leases

- **TTL default** `LEASE_TTL_SEC=300`; per-task override via `task.metadata.timeout_sec`.
- **Heartbeat** every 30s during `call_tool` (quick UPDATE, never inside user code).
- **Reclaim rule** — `CLAIMED`/`IN_PROGRESS` + expired lease → `LEASE_EXPIRED` → if `cancel_requested` → `CANCELLED`; else retry or permanent `FAILED`.

### 7.5 Worker model

- `ThreadPoolExecutor(max_workers=max_concurrent_tasks)` — stdlib, matches `ThreadingHTTPServer`.
- Workers are stateless; all state in SQLite. Worker crash = lease expiry = swept = recovered.
- `call_tool` is sync and never raises; worker additionally wraps in `try/finally` for lease release.

---

## 8. FAILURE / RECOVERY MODEL

### 8.1 Failure taxonomy

| Failure | Detection | Recovery |
|---|---|---|
| Tool failure (`ok=False`) | worker | retry policy or permanent FAILED |
| Dependency failure | Phase 3.2 `_refresh_readiness` | dependents → BLOCKED (existing) |
| Worker crash | lease expiry | sweep reclaims → retry or FAILED |
| Scheduler/process crash | startup sweep | orphans reclaimed; missions resume |
| SQLite locked | busy_timeout retries | jittered backoff loop |
| Mission timeout | TimeoutGuard | mission FAILED; all active → cancel → CANCELLED; dependents BLOCKED |
| Task timeout | TimeoutGuard (`started_at+timeout_sec`) | execution FAILED; task retried or FAILED |
| Task cancel (RUNNING) | cooperative flag | worker completes tool, transitions RUNNING→CANCELLED |
| Task cancel (PENDING/READY/BLOCKED) | direct transition | → CANCELLED (legal in 3.2) |
| Invalid/duplicate write | guarded `WHERE status=...` | rejected + `DUPLICATE_WRITE_REJECTED` event |
| `task_graph` DB corrupt | exceptions from 3.2 | scheduler aborts loop; startup sweep retries; mission FAILED (engine error) |

### 8.2 Retry policy (final)

- `max_attempts` default **3**, only for `idempotent:true` tools; override via `task.metadata.retry`.
- Backoff: `delay = min(base * 2**(attempt-1), cap)` — base 1s, cap 60s, ±20% jitter.
- Transient errors retried; `PERMANENT:`-prefixed errors fail immediately.
- After exhaustion: task FAILED; mission auto-FAILED only if `constraints.fail_mission_on_task_failure:true` (default false — independent branches continue).

### 8.3 Failure propagation

```
Task FAILED (permanent)
    ├──▶ _refresh_readiness() → dependents BLOCKED (recursive)
    ├──▶ executions → FAILED (permanent)
    └──▶ (optional fail_mission_on_task_failure)
         └──▶ mission FAILED → all active tasks CANCELLED (cooperative)
```

### 8.4 Recovery semantics

| Scenario | Behavior |
|---|---|
| Server restart | Startup sweep: expired-lease executions → retry/FAILED; READY tasks re-dispatched; RUNNING missions resume. |
| Mission RUNNING, no live executions | Scheduler claims remaining READY/PENDING; if none → auto-COMPLETED. |
| Mission RUNNING, all tasks terminal | `finalize_mission()` each poll → COMPLETED or FAILED by task outcomes. |
| Orphaned executions | `RECLAIMED` + `error="worker_crash"`. |
| Duplicate events after replay | `event_id` PK + `INSERT OR IGNORE`. |

---

## 9. SECURITY MODEL

| Concern | Design |
|---|---|
| Authorization | Every op validates `mission_id` + task ownership via `get_task(mission_id, task_id)`; routes reuse Phase 3.1/3.2 checks. Mission scoping is tenant-shaped. |
| Untrusted inputs | `input` is validated JSON — strictly arguments to registered tools, never executable content. Length caps carry through. |
| Tool isolation | **Only** side-effect boundary is `tools.call_tool`; engine never evals/execs/subprocesses. Approval gates inherited from Phase 3.8 (`approvals.check()` pre-claim when metadata requires). |
| Arbitrary code prevention | Tool names resolved against static `TOOLS` allowlist; unknown name → task FAILED, never interpreted. |
| Secrets hygiene | Inputs/outputs/errors must not contain secrets by contract; audit stores truncated summaries; secret args stay in `.env`. |
| Cancel authority | Same ownership semantics as mission create. |

---

## 10. OBSERVABILITY MODEL

### 10.1 Structured events (`execution_events`, append-only)

Event types: `CLAIMED`, `STARTED`, `TOOL_OUTPUT`, `COMPLETED`, `FAILED`, `RETRY_SCHEDULED`, `CANCELLED`, `TIMEOUT`, `LEASE_EXPIRED`, `RECLAIMED`, `DUPLICATE_WRITE_REJECTED`. Each carries `execution_id + task_id + mission_id`.

### 10.2 Audit (reuses single `audit.record()`)

Intents: `task_execution_start/end/retry/fail/cancel`, `scheduler_start/stop/recovery/paused`, `mission_execute_start/end`. Best-effort; never breaks engine.

### 10.3 Metrics

executions total/per-mission/per-task; success/failure rates; p50/p95 latency; retry distribution; timeout/lease-expiry/reclaim counts; active concurrency (global + per mission); blocked task count; READY queue depth. Exposed via `/api/execution-engine/metrics`.

### 10.4 Logging

`logging` (stderr, `[heer]` style); every line carries `execution_id= task_id= mission_id=`; payloads truncated to 500 chars; no secrets.

---

## 11. API / INTERFACE PROPOSAL (proposed only — NOT implemented)

### 11.1 Module-level interface (`agent/execution_engine.py` — new)

```
# ── lifecycle ─────────────────────────────────────────────────────────────
start_mission(mission_id, *, business_id=None, max_concurrent=None)
    → {"ok": True, "active_workers": n, "dispatched": [execution_ids]}
pause_mission_execution(mission_id) / resume_mission_execution(mission_id)
    → {"ok": True, "mission": {...}}        # scheduler skips/resumes mission
stop_mission_execution(mission_id)
    → {"ok": True, "cancelled": [...execution_ids]}    # cooperative cancel all active

# ── per-task control ──────────────────────────────────────────────────────
cancel_task(mission_id, task_id) → {"ok": True, "task": {...}}
retry_task(mission_id, task_id, *, reason="manual") → {"ok": True, "execution": {...}}

# ── queries ───────────────────────────────────────────────────────────────
execution(execution_id) → {...} | None
list_executions(mission_id=None, task_id=None, status=None, limit=100)
executions_payload(mission_id=None, limit=100)     # for UI
scheduler_metrics() → {...}
list_events(mission_id=None, execution_id=None, limit=200)

# ── scheduler control ─────────────────────────────────────────────────────
scheduler_start() / scheduler_stop() / scheduler_status()
recover()   # startup sweep (called automatically on import/scheduler_start)

# ── internal primitives (documented, not public API) ──────────────────────
_claim(task_id, mission_id)     → execution_id | None
_worker(execution_id)           → None (thread entry)
_sweep_expired_leases()         → n_reclaimed
_enforce_timeouts()             → n_timed_out
_honor_cancellations()          → n_cancelled
_finalize_mission_if_done(mission_id) → {"ok": True, "terminal": bool, "status": ...}
```

### 11.2 HTTP routes (additive to `agent/main.py` — wiring only)

| Method | Path | Action |
|---|---|---|
| POST | `/api/mission-engine/missions/{mid}/execute` | `start_mission(mid, business_id=current)` |
| POST | `/api/mission-engine/missions/{mid}/execute/pause` | pause |
| POST | `/api/mission-engine/missions/{mid}/execute/resume` | resume |
| POST | `/api/mission-engine/missions/{mid}/execute/cancel` | `stop_mission_execution(mid)` |
| POST | `/api/mission-engine/missions/{mid}/tasks/{tid}/cancel` | `cancel_task(mid, tid)` |
| POST | `/api/mission-engine/missions/{mid}/tasks/{tid}/retry` | `retry_task(mid, tid)` |
| GET | `/api/execution-engine/executions?mission_id=&status=&limit=` | `executions_payload(...)` |
| GET | `/api/execution-engine/executions/{exec_id}` | `execution(exec_id)` |
| GET | `/api/execution-engine/events?mission_id=` | `list_events(...)` |
| GET | `/api/execution-engine/metrics` | `scheduler_metrics()` |
| GET | `/api/execution-engine/status` | `scheduler_status()` |

Errors: 400 invalid input, 404 unknown mission/task/execution, 409 invalid transition (3.1/3.2 conventions).

### 11.3 Integration contract (no change to 3.2)

Imports/calls: `task_graph.create_task/get_task/list_tasks/validate_graph`, `task_graph.ready_tasks/blocked_tasks/transition_task/_refresh_readiness`, `mission_engine.get_mission/transition/list_missions`, `tools.call_tool`, `audit.record`, `approvals.check` (when approval metadata). **Zero imports from `orchestrator` or `mission.py`.**

---

## 12. TEST STRATEGY

`tests/execution_engine_test.py` (stdlib `unittest`, ephemeral `.heer/` paths, fake tool registry monkeypatched — deterministic success/fail-once/slow/crash simulators).

| Test area | Cases |
|---|---|
| Parallel fan-out | Diamond DAG A→B,C→D: B,C overlap (concurrency window > 0); D starts after both. |
| Dependency ordering | Linear A→B→C: starts strictly ordered, no overlap; join D waits B,C. |
| Race conditions | Two concurrent `start_mission` → each task dispatched exactly once; zero duplicate executions. |
| Duplicate execution prevention | Second worker update rejected (`superseded`); `DUPLICATE_WRITE_REJECTED` event. |
| Retries | Fail-once → attempt 2 succeeds; distinct execution_ids; task COMPLETED from attempt 2. |
| Retry exhaustion | Always-fail, max_attempts=3 → FAILED on attempt 3; dependents BLOCKED. |
| Cancellation | READY task → CANCELLED, never dispatched. RUNNING slow task → cooperative cancel; worker transitions CANCELLED; dependents BLOCKED. |
| Timeout | `timeout_sec=0.5`, tool sleeps 3s → `TIMEOUT`, execution FAILED, task FAILED/retried per policy. |
| Worker crash | Thread dies without lease release; TTL=1s → sweep reclaims; `LEASE_EXPIRED`+`RECLAIMED`; task retried or FAILED. |
| Restart recovery | Drop scheduler mid-flight; new `scheduler_start()` sweep → reclaimed, re-dispatched, mission resumes. |
| Concurrency limits | 10 READY, global=3 → peak ≤3; per-mission=2 → peak ≤2 while other mission continues. |
| Invariants | task terminal ⇔ no live execution; RUNNING ⇔ exactly 1 live execution; transitions only via public API. |
| Backward compat | Existing `mission_engine_test.py`, `task_graph_test.py`, acceptance C5–C8 pass unchanged. |
| Idempotency guard | Non-idempotent tool failure → immediate FAILED, no retry. |

### 12.2 Acceptance: `scripts/acceptance_phase33.py`

Live-server: create mission → `/execute` → poll → assert fan-out window, join ordering, completed mission; retry/cancel/timeout scenarios; legacy endpoints (C5–C8) + `/api/chat` regression.

---

## 13. RISKS

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | SQLite `database is locked` under many worker threads | Med | Med | WAL + `busy_timeout` + short transactions + claim-first; verify at 32 workers. |
| R2 | Long tools holding threads (heartbeat covers lease, not GIL) | Med | Med | Per-tool timeout upper bound; heartbeat; `max_concurrent` caps. |
| R3 | Non-idempotent tools auto-retried → duplicate side effects | Med | High | Retry only for `idempotent:true`; `PERMANENT:` error convention. |
| R4 | Cross-file task/execution drift after crash | Low | Med | Startup sweep + invariant check → event + audit + manual repair. |
| R5 | Mission COMPLETED races last worker write | Med | Low | Finalize only when zero live executions; re-check under `BEGIN IMMEDIATE`. |
| R6 | Retry storm (many simultaneous failures) | Low | Med | Jittered backoff + attempt cap + global retry semaphore. |
| R7 | Thread explosion under many missions | Med | Med | Hard global cap (default 8) + per-mission caps; never submit beyond limit. |
| R8 | Mission appears stuck (PAUSED not auto-resumed) | Low | Low | Explicit pause/resume; `scheduler_status` exposes paused missions. |
| R9 | Manual transition collides with live execution | Med | Low | 409 when a live lease owns the task; manual transitions remain legal otherwise. |
| R10 | Tenancy isolation deferred to Phase 4/5 | Low | Med | Schema already mission-scoped; per-mission limits tenant-shaped. |

---

## 14. FAILURE SCENARIOS (12 modeled)

| # | Scenario | Expected system behavior |
|---|---|---|
| F1 | Tool `ok=False` transient, idempotent, attempt 1/3 | Execution FAILED; `RETRY_SCHEDULED`; backoff 1s; attempt 2 dispatched; task stays RUNNING. |
| F2 | Tool `ok=False` permanent (invalid args) | No retry; execution FAILED; task RUNNING→FAILED; dependents BLOCKED; independent branches continue. |
| F3 | Tool raises uncaught exception | Worker catch-all: execution FAILED (`Tool error: ...`); retry policy applies; audit `task_execution_fail`. |
| F4 | Worker thread dies mid-tool | Lease expiry → `LEASE_EXPIRED`+`RECLAIMED`; task retried or FAILED; dependents resolved. |
| F5 | Scheduler process killed; restart | Startup `recover()` reclaims orphans; missions resume; duplicate-execution guard prevents double-run. |
| F6 | Task timeout exceeded | TimeoutGuard → execution FAILED (`TIMEOUT`); task retried or FAILED; lease released. |
| F7 | Mission timeout exceeded | Mission → FAILED; all live executions cancel → CANCELLED; PENDING/READY/BLOCKED → CANCELLED. |
| F8 | Mission cancelled by user | Cascading cancel (F7); mission → CANCELLED; no further dispatch. |
| F9 | Task cancelled while RUNNING | Cooperative flag; worker finishes tool, transitions RUNNING→CANCELLED; dependents BLOCKED. |
| F10 | Duplicate execution attempt (stale heartbeat) | Second writer match 0 rows → rejected + `DUPLICATE_WRITE_REJECTED` event; first result preserved. |
| F11 | Dependency chain fails at depth 2 (A→B→C) | B BLOCKED on A FAILED; C BLOCKED on B BLOCKED (3.2 recursive rule exists); mission FAILED only if `fail_mission_on_task_failure`. |
| F12 | Two missions, per-mission=2, global=4 | Both caps honored; never exceeded; FIFO fairness across missions by `created_at`. |

---

## 15. ARCHITECTURE DECISION

### 15.1 Candidates compared

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **A. In-process ThreadPoolExecutor + SQLite lease** | Fits `ThreadingHTTPServer`; stdlib-only; `call_tool` already sync/non-raising; lease model testable; portable seam to Hermes Runtime | Single-process; GIL for CPU-bound (tools are I/O-bound) | **RECOMMENDED** |
| B. asyncio cooperative | Single-threaded simplicity | All Phase 3 tools blocking; requires rewriting tools.py + legacy `handle()` | Rejected |
| C. External queue (Celery/RQ/Redis) | Horizontal scale | Adds deps; breaks stdlib constraint; no infra today | Rejected |
| D. Subprocess worker pool | Isolation | Heavy; IPC; tools not fork-safe | Rejected |
| E. Multi-process + SQLite | Fault isolation | Process mgmt overhead; lease model already gives recovery | Rejected for now; portable seam makes it a non-breaking later swap |

### 15.2 Recommendation

**Option A.** Rationale mapped to codebase: `main.py` already threaded; `tools.call_tool` is the ideal worker unit with zero Phase 3.8 changes; Phase 3.2 already provides atomic transitions + readiness propagation so the scheduler only orchestrates; the `executions` + `lease_expires_at` + `execution_events` tables are the inter-process seam — replacing `ThreadPoolExecutor.submit` with a queue producer later requires no state-model change.

---

## 16. BACKWARD COMPATIBILITY (EXPLICIT)

| Contract | Status |
|---|---|
| Phase 3.1 `mission_engine.py` | Untouched; no new imports or modified functions. |
| Phase 3.2 `task_graph.py` | Untouched; 3.3 only calls public functions; retries are new execution attempts — no new task transitions. |
| Legacy `mission.py` + `orchestrator.handle()` | Untouched; 3.3 never imports them; `/api/chat`, `/api/orchestrate`, legacy endpoints keep working. |
| `audit.py`, `approvals.py`, `tools.py` | Untouched; 3.3 consumes them. |
| Task statuses | Unchanged — exactly the Phase 3.3 required set; attempt-level statuses live in a separate table. |
| Manual API transitions | Still legal when no live lease; 409 only when a live execution owns the task. |
| Manifest | One new module + one new SQLite file + additive `main.py` route scaffolding. `main.py` is the only existing file modified. |

---

## 17. IMPLEMENTATION SCOPE NOTE (DOES NOT CONSTITUTE APPROVAL)

When (and only when) explicitly approved: new `agent/execution_engine.py` per this spec; `.heer/execution_engine.sqlite3` auto-created on first use; additive route scaffolding in `agent/main.py`; `tests/execution_engine_test.py` + `scripts/acceptance_phase33.py`; roadmap status note. **No** changes to `mission_engine.py`, `task_graph.py`, `mission.py`, `orchestrator.py`, `tools.py`, `audit.py`, `approvals.py`.

---

## 18. DESIGN SUMMARY CHECKLIST

- ✅ Current architecture assessment (3.1/3.2 pure state machines; `call_tool` isolated boundary; thread-based server; three-file SQLite pattern; legacy `handle()` preserved)
- ✅ Proposed Phase 3.3 architecture (in-process ThreadPoolExecutor scheduler; lease/claim; zero changes to 3.1/3.2)
- ✅ Component diagram (Scheduler/WorkerPool/LeaseManager/RetryPolicy/CancellationCoordinator/TimeoutGuard/RecoveryEngine/MetricsCollector)
- ✅ State transitions (task states unchanged authoritative; attempt-level states; mission unchanged)
- ✅ Execution algorithm (poll loop; claim-then-confirm; guarded worker writes; retry as new attempt)
- ✅ Persistence model (`executions`, `execution_events`, `scheduler_config`; cross-file invariants; first-write-wins)
- ✅ Concurrency model (WAL + immediate transactions + lease/heartbeat + guarded transitions + race table)
- ✅ Failure/recovery model (12 failure scenarios; backoff/max attempts; cascade to BLOCKED; startup recovery sweep)
- ✅ Security model (tool allowlist dispatch; JSON-only input; no eval/exec; approval gates; secrets hygiene)
- ✅ Observability model (structured events with execution/task/mission IDs; audit reuse; metrics suite)
- ✅ API/interface proposal (module signatures + HTTP routes — proposed, not implemented)
- ✅ Test strategy (13 groups covering all 10 required scenarios + backward-compat suite)
- ✅ Risks (10 risks with mitigations)
- ✅ Recommendation (Option A, with portable Hermes Runtime seam)

---

*End of Phase 3.3 architecture design specification. No source code was written or modified. Phase 3.3 implementation is on hold pending explicit approval.*
