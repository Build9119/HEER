# D4 IMPLEMENTATION-READINESS REVIEW

---

## 1. REPOSITORY SAFETY BASELINE

### Branch Status
* **Branch:** `safe-branch` (tracking `origin/safe-branch`)
* **HEAD Commit:** `06f35cf` - feat: add D1 worker persistence

### Working Tree Status
* Untracked:
  - `?? HEER_PHASE38_D4_AUTHORITY_DECISION.md` (newly added file)
* Modified SQLite state files only (expected runtime databases):
  - `MM data/.heer/execution_engine.sqlite3`
  - `MM data/.heer/executions.sqlite3`
  - `MM data/.heer/mission_engine.sqlite3`
  - `MM data/.heer/task_graph.sqlite3`

### Frozen Contracts Diff Check
No differences in frozen contracts (`agent/worker_contracts.py`, `agent/worker_registry.py`, `agent/d1_persistence.py`, `agent/execution_engine.py`):
* **DIFF:** CLEAN
* **CHECK:** CLEAN

---

## 2. CANONICAL AUTHORITY MAP

### D3 (Tenant and Worker Identity)

| Property          | Created by       | Validated by      | Persisted by       | Consumed by        | Must Not Be Modified By |
|--------------------|------------------|-------------------|--------------------|--------------------|--------------------------|
| worker_id          | WorkerRegistry   | WorkerRegistry    | D1Persistence      | WorkerMatcher, EE  | Business Authorization   |
| worker_instance_id | WorkerRegistry   | WorkerRegistry    | Not persisted      | WorkerMatcher, EE  | Business Authorization   |
| worker_epoch       | WorkerRegistry   | WorkerRegistry    | D1Persistence      | WorkerMatcher, EE  | Business Management      |
| tenant_scope       | WorkerRegistry   | WorkerMatcher     | Not persisted      | WorkerMatcher      | Business Registry        |

### D4 (Business Identity and Authorization)

| Property                | Created by       | Validated by              | Persisted by       | Consumed by        | Must Not Be Modified By |
|--------------------------|------------------|---------------------------|---------------------|--------------------|--------------------------|
| business_id              | Business Registry | Business Registry         | Business Registry  | Orchestrator, EE   | WorkerRegistry          |
| business definition      | Business Registry | WorkerMatcher            | Business Registry  | Orchestrator, EE   | WorkerRegistry, D1       |
| business → tenant mapping | Business Registry | Business Registry         | Business Registry  | Worker Authorization | WorkerRegistry, EE      |
| worker → authorized business set | Business Registry | Worker Authorization     | Business Registry  | WorkerMatcher       | ExecutionEngine, WorkerMatcher |

---

## 3. BUSINESS → TENANT AUTHORITY

### Current State
* Defined in: **businesses.json** (but currently lacks any `tenant_scope` field)
* No runtime or persistent mapping of `business_id → tenant_scope`

### Requirement
* Add `tenant_scope` field alongside existing business properties; non-persistent at runtime.

---

## 4. WORKER → BUSINESS AUTHORIZATION

### Current State
* No mechanism for explicit worker → business relationships:
  * **WorkerIdentity** carries only `worker_id`, `worker_instance_id`, `worker_epoch`, and `tenant_scope`.
* WorkerMatcher uses `tenant_scope` to filter workers but does not consider business authorization.

### Requirement
* Extend **businesses.json** to include `authorized_workers: list[str]`.

---

## 5. EXACT AUTHORIZATION FLOW

### Current Dispatch Path
1. Request → business_id extracted
2. Business Registry resolves→ Neither tenant_scope nor `authorized_workers` are present.
3. Authorization does **not** occur beyond `tenant_scope`.

### Required Authorization Enforcement
* Authorization Check at: **WorkerMatcher**
  - Add method: `_is_authorized(worker_id: str, business: BusinessDefinition)`

---

## 6. EXECUTIONENGINE BOUNDARY

### Verified:
* Execution authority remains intact:
  - `execution_id`
  - `attempt_no`
  - Leases and retry

---

## 7. D1 BOUNDARY

**Frozen Contracts Verified - CLEAN**

### NO NEED for:
* worker → business mappings
* Business Identity stored persistently in D1.

**Status: Frozen contract preserved.**

---

## 8–13. MINIMUM DESIGN

### Target Design Points
1. **Business registry** → resolved.
2. Scope preservation remains frozen.

### Recommendation: Move doc