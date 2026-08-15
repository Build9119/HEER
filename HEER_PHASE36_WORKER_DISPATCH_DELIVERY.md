# PHASE 3.6 WORKER DISPATCH & CAPABILITY MATCHING — DELIVERY REPORT

## 1. Current Architecture Assessment

Re-verified from `HEER_PHASE36_WORKER_DISPATCH_GATE.md` (full 598-line read), `agent/dispatch_contracts.py`, `agent/worker_matcher.py`, `agent/worker_registry.py`, `agent/worker_contracts.py`, `agent/runtime_contracts.py`, `agent/hermes_adapter.py`, `agent/hermes_runtime.py`, `agent/execution_engine.py`, plus the two new Phase 3.6 test suites.

- **Frozen stack**: HEER → Mission Engine (3.1) → Task Graph/DAG (3.2) → Parallel Execution Engine (3.3, sole execution/lease/retry/timeout authority) → Hermes Adapter (3.4, pure mapping seam) → HermesRuntime (execution plane, INPROCESS ThreadPoolExecutor) → governed tool boundary (`tools.call_tool` / allowlist / approvals L0–L3).
- **Frozen contracts**: `RuntimeRequest`/`RuntimeResult`/`RuntimeHandle`/`RuntimeCapabilities` with `job_id == execution_id`, `idempotency_key == execution_id`, `correlation_id == execution_id` as canonical dedup identity.
- **Worker Fabric (3.5)**: in-memory `WorkerRegistry` with 8 public methods (`register` / `heartbeat` / `mark_stale` / `depart` / `get` / `list` / `list_by_capability` / `status`), descriptive identity/capability/liveness, zero policy authority. **Nothing in `agent/*.py` calls `WorkerRegistry`** — it is unwired (gate §1.4 verified).
- **The gap Phase 3.6 addresses**: the Execution Engine selects *which ready task to claim* (DB iteration order) but there is **no dispatch layer** that selects *which eligible worker* honors a given already-authorized request. The gate froze the design and explicitly directed a subsequent implementation phase: "Phase 3.6 implementation (dispatch/matching seam, Registry-only matching, deterministic-first-eligible)" (§27).

## 2. Phase 3.6 Architectures Delivered

Two additive, transport-agnostic modules on the execution plane with **zero policy authority**:

### 2.1 Dispatch Contracts (`agent/dispatch_contracts.py`) — Phase 3.6.1
Immutable, JSON-safe contract shapes for the dispatch seam. **No selection logic lives here** — the module validates shapes, enforces the authority boundary structurally, and freezes the ordering to exactly `DETERMINISTIC_FIRST_ELIGIBLE`.

- `WorkerCandidate` — snapshot of a registry entry: frozen `WorkerIdentity` (worker triple + tenant + isolation + transport_identity) + liveness state + heartbeat-seq-last-known. **Identity snapshot, not a live registry handle.**
- `CapabilityMatch` — candidate + matched hard/soft attribute-name tuples + `execution_id` correlation + `matched_at`. Descriptive; carries no `authorized`/`granted`/`allow` fields.
- `DispatchDecision` — `execution_id` + candidate (SELECTED) or none (NO_ELIGIBLE / TENANT_REJECTED) + `decided_at`. **No `job_id`, no `idempotency_key`, no lease, no retry, no task-state fields** — it carries `execution_id` only as correlation; a second execution identity is never minted.
- `DispatchConstraints` — declarative hard filters: `tenant_scope` (caller-supplied; job tenant context is OPEN per gate §24), `require_live` (default True), `required_isolation`, `required_tool_classes`, `required_runtime_features` (validated against the frozen `RuntimeCapability` enum), `required_architecture`, `ordering`. **No capacity fields** (capacity is never a hard gate — I22).
- `DispatchPolicy` — policy id + frozen ordering. Reference only; no ranking weight/score/fairness fields exist (I3/I20).
- `DispatchOrdering` / `DispatchReason` enums — exactly `DETERMINISTIC_FIRST_ELIGIBLE` (len 1) / `SELECTED`/`NO_ELIGIBLE`/`TENANT_REJECTED` (len 3).
- `to_dict` / `from_dict` / `to_json` / `from_json` — deterministic (sorted keys, `", "`/`": "` separators asserted absent), secret-safe, forward-compatible defaults.

### 2.2 Worker Matcher (`agent/worker_matcher.py`) — Phase 3.6.2
The gate's **Option A — Registry-only matching**: a thin, transport-agnostic selection function exposing exactly `{match, evaluate}` and nothing else.

- **Registry purity**: the matcher touches ONLY `list()` and `status()` on any registry-like object; a `_ReadOnlySpy` proves no Hermes/EE/audit/tools/registry-mutation interaction; a forbidden-imports test proves `worker_matcher` imports neither `hermes`, `execution_engine`, `audit`, `tools`, `worker_registry`, `mission_engine`, nor `task_graph`.
- **Deterministic first eligible**: hard attributes filter (tenant → liveness → isolation → tool classes → runtime features → architecture → epoch), then candidates sorted by `worker_id`, first eligible selected. Deterministic and registration-order independent.
- **Re-validation at call time**: selection consumes the registry `list()` snapshot at call time, so a worker that went STALE/DEPARTED (or whose epoch superseded) between writes is never selected.
- **Capacity is soft/absent**: no capacity field exists in constraints/policy; capacity never eliminates (I22).
- **Unwired**: nothing in the EE/adapter call path invokes the matcher. Runtime behavior is unchanged; wiring is a separate gated step (gate risk #17, §25 prerequisite #4).

## 3. Component Diagram

```
Execution Engine (control plane: execution_id, attempts, leases, retries, cancellation, final persistence, audit — UNCHANGED, UNWIRED to matcher)
      ↓ frozen RuntimeRequest / RuntimeResult / RuntimeHandle / RuntimeCapabilities
Hermes Adapter (boundary seam: mapping only — frozen, UNCHANGED)
      ↓
[ Dispatch / Matching Seam (NEW 3.6):  WorkerMatcher — pure function over registry ]   ← gate §25 "PROPOSED" option A
      ├── match()      → DispatchDecision (SELECTED | NO_ELIGIBLE | TENANT_REJECTED)
      └── evaluate()   → (DispatchDecision, CapabilityMatch)
      ↓ reads-only
Worker Registry (Phase 3.5 — descriptive identity/capability/liveness, UNCHANGED)
      ├── list(tenant_scope=...)     deterministic sorted snapshot
      └── status()                   aggregate counters
      ↓ eligible worker candidate
Hermes Transport (HermesRuntime, INPROCESS today — UNCHANGED)
      ↓
Worker (execution plane: runs one authorized job; never policy)
      ↓
Governed Tool Boundary (tools.call_tool / allowlist / approvals)
```

No scheduler, no dispatcher-into-EE wiring, no task-state writes, no lease/retry creation, no transport changes.

## 4. Selection Semantics (the matcher's state interaction)

The matcher consumes the registry liveness state machine (Phase 3.5, frozen) per gate §8:

| Registry state | Matcher eligibility (gate §8, implemented) |
|---|---|
| `LIVE` | **Selected** by default (`require_live=True` is the contract default) |
| `REGISTERED` | **Excluded** by default; admitted only under explicit `require_live=False` (declared in contract test 34, enforced in matcher test 12) |
| `STALE` | **Never selected** — excluded under both `require_live` modes (matcher test 10, 12) |
| `DEPARTED` | **Never selected** — no zombie revival (matcher test 11, 12) |
| newer `worker_epoch` | Supersedes old triple; old `(worker_id, instance, epoch)` never selected (matcher test 13); stale instance heartbeats rejected at the registry and never surface (matcher test 14) |

**Rule:** hard attributes filter; soft attributes rank. Only one ordering is frozen (`DETERMINISTIC_FIRST_ELIGIBLE`); weighted/least-loaded/round-robin remain OPEN (gate §10, §24).

## 5. Selection Algorithm (as implemented)

`match(constraints, execution_id, decided_at=None) -> DispatchDecision`:

1. `status()` — empty registry short-circuits to `NO_ELIGIBLE` (only `status()` is touched).
2. `list(tenant_scope=constraints.tenant_scope)` — deterministic sorted snapshot; server-side tenant filter; cross-tenant selection structurally impossible.
3. Hard filter per candidate:
   - `worker_epoch` valid, matching the current registered triple (old triples absent from list).
   - liveness: `LIVE` if `require_live=True`; `REGISTERED` also admitted if `require_live=False`; `STALE`/`DEPARTED` always excluded.
   - `isolation_mode` satisfies `required_isolation` when declared.
   - `tool_classes` ⊇ every `required_tool_classes` entry when declared.
   - runtime `features` ⊇ every `required_runtime_features` entry when declared (validated against frozen enum at constraint construction).
   - `architecture` equality when `required_architecture` declared (no fuzzy aliases).
4. Deterministic order by `worker_id`; first eligible → `SELECTED`.
5. No candidates at all → `NO_ELIGIBLE`; candidates exist but none match the tenant filter → `TENANT_REJECTED`.
6. `evaluate()` additionally returns a `CapabilityMatch` with the matched hard attributes (sorted, deduped) for observability.

All outcomes are **descriptive decisions about candidates** — never about whether the job runs, retries, leases, or persists. The EE remains sole authority for those (gate I1, I4, I5, I6).

## 6. Persistence Model

**In-memory only, zero storage.** The dispatch seam:
- writes **no** SQLite rows, `execution_events`, or `audit.record` entries;
- creates **no** new tables, schema, or files;
- holds no durable state — decisions are pure functions over the registry snapshot + request metadata.

Durable truth remains unchanged: `execution_engine.sqlite3` (`executions` + `execution_events`) + `audit.record`, owned solely by the EE. On restart the registry is empty and the seam returns `NO_ELIGIBLE` until workers re-register — a fabric-local, acceptable loss (EE lease/sweep composes on top, unchanged).

## 7. Concurrency Model

- **Matcher**: stateless; reads `status()`/`list()` under the registry's own `RLock` (Phase 3.5); no shared mutable state; no locks needed beyond the registry's. Concurrent decisions are race-free by construction and deterministic for equal inputs.
- **Contracts**: fully frozen `@dataclass(frozen=True)`; immutable after construction; attribute tuples sorted/deduped at validation; serialization deterministic (byte-identical for identical input including `decided_at`).
- **Identity immutability**: `tenant_scope`, `worker_id`, `worker_instance_id`, `worker_epoch`, `isolation_mode` immutable on `WorkerIdentity`; tests assert `AttributeError` on mutation attempts.
- No threads, no barrier tests needed — the seam introduces zero shared state; the 292-test suite includes the existing 16-thread barrier tests from Phase 3.5.

## 8. Failure / Recovery Model

Unchanged from the frozen model — the seam decides nothing about recovery:

| Gate scenario | Behavior (verified unchanged) |
|---|---|
| No eligible worker | `NO_ELIGIBLE` descriptive decision; EE lease/sweep drives the task's fate |
| All workers stale | No LIVE candidate → `NO_ELIGIBLE`; fabric liveness is NOT a lease |
| Worker departs after selection | Re-validation at call time: `list()` snapshot excludes DEPARTED |
| Worker epoch changes | New epoch supersedes; old triple absent from `list()` |
| Late/duplicate results | EE `_finalize`/`_gw` terminal CAS rejects — the only new writer would be wiring, which does not exist |
| Transport stall | Unchanged: adapter returns `runtime_stalled`; EE lease sweep recovers |
| Duplicate dispatch | No execution identity is ever minted by the seam (`DispatchDecision` carries no `job_id`/`idempotency_key`); Hermes dedup remains authoritative |

**Explicit:** the matcher never calls `heartbeat`, `mark_stale`, `depart`, or `register` on the registry — it is a read-only consumer (proven by spy + forbidden-import tests).

## 9. Security Model

- **Capability is descriptive, never authorization** (I3): `CapabilityMatch`/`DispatchDecision`/`WorkerCandidate` carry no `authorize`/`grant`/`permission`/`trust` fields (contract tests 21, 28; matcher test 27). The EE's approve/allowlist/attempt-claim remains the authorizer.
- **No secondary writer / no authority surface**: `WorkerMatcher` exposes exactly `{match, evaluate}`; `DispatchDecision` has no claim/lease/retry/task-state/schedule methods; module-level absence of `DispatchLease`/`TaskState`/`DispatchJob` asserted (contract tests 17–22, 25; matcher authority test).
- **Tenant isolation** (I9): tenant filter enforced server-side via `list(tenant_scope=...)`; identity `tenant_scope` immutable; identity cannot override scope (contract tests 30–31; matcher tests 6–7).
- **No attestation claimed** (I3/I10): no `signature`/`verified`/`trusted` fields (contract test 29); forged/self-reported capabilities are representable descriptive metadata only.
- **Secret-safety**: serialization contains no `api_key`/`token`/`password`/`credential`; `"secret"` appears only inside the frozen `supports_secrets` boolean flag (contract test 42).
- **Spoofing posture**: worker-claimed identity is never authority; decisions are descriptive; any future wiring must preserve EE correlation to the `execution_id` it authorized (gate §3).

## 10. Observability Model

- Contract composition carries the full correlation lineage: `execution_id → worker_id → worker_instance_id → worker_epoch → tenant_scope → transport_identity → state → heartbeat_seq` (contract test 39).
- `CapabilityMatch` records matched hard attributes for later metrics.
- **No event emission this phase**: `DISPATCH_CANDIDATES` / `DISPATCH_SELECTED` / `DISPATCH_NO_ELIGIBLE` / `DISPATCH_TENANT_REJECTED` / `WORKER_*` remain **proposed, not implemented** (gate §16) — the seam is a pure state/view layer; events belong to a later delivery with audit correlation.

## 11. API / Interface Surface (delivered)

### `agent/dispatch_contracts.py`
- `WorkerCandidate(identity, state, registered_at, reported_at=None, heartbeat_seq=0) -> WorkerCandidate` — immutable snapshot; `nan`/negative-seq/`None`-at rejected.
- `CapabilityMatch(candidate, execution_id, matched_hard_attributes=(), matched_soft_attributes=(), matched_at=None)` — sorted attr tuples; empty `execution_id` rejected.
- `DispatchDecision(execution_id, candidate=None, reason=SELECTED, decided_at=None)` — SELECTED requires candidate; NO_ELIGIBLE/TENANT_REJECTED must NOT carry one.
- `DispatchConstraints(tenant_scope=None, require_live=True, required_isolation=None, required_tool_classes=(), required_runtime_features=(), required_architecture=None, ordering=DETERMINISTIC_FIRST_ELIGIBLE)` — validates against frozen enums; no capacity fields.
- `DispatchPolicy(policy_id, description="", ordering=DETERMINISTIC_FIRST_ELIGIBLE)`.
- `DispatchOrdering` / `DispatchReason` enums; `DISPATCH_ORDERING_VALUES` (`("DETERMINISTIC_FIRST_ELIGIBLE",)`); `DISPATCH_REASON_VALUES` (`("SELECTED","NO_ELIGIBLE","TENANT_REJECTED")`).
- `to_dict(obj) / from_dict(dict, type) / to_json(obj) / from_json(str, type)` — deterministic, JSON-safe, forward-compatible.

### `agent/worker_matcher.py`
- `WorkerMatcher(registry).match(constraints, *, execution_id, decided_at=None) -> DispatchDecision`
- `WorkerMatcher(registry).evaluate(constraints, *, execution_id, decided_at=None) -> tuple[DispatchDecision, CapabilityMatch]`
- Constructor rejects anything lacking `list()`/`status()`.
- **No other public surface** (asserted).

All methods return/consume plain JSON-safe dataclasses; no internal registry state is ever exposed.

## 12. Test Strategy (84 new tests; 292 total)

| Suite | Tests | Covers |
|---|---|---|
| `tests/dispatch_contracts_test.py` (Phase 3.6.1) | **43** | Contract shapes (WorkerCandidate/CapabilityMatch/DispatchDecision/Constraints/Policy), immutability, validation discipline (nan/empty/negative/BOGUS/type), deterministic serialization (sorted keys, no spaces), JSON round-trip all types, malformed input rejection, **authority absence** (no claim/lease/retry/task-state/authorize/scheduling fields, no `DispatchLease`/`TaskState`/`DispatchJob`), capacity-never-hard-gate, ordering frozen to exactly one value, no-second-execution-identity, duplicate-dispatch correlation, capability≠authorization, spoofing posture, tenant immutability, epoch triple binding, liveness representability + LIVE-by-default, hard/soft attribute declaration, correlation lineage, runtime-feature enum validation, reason taxonomy, secret-safety, deserializer defaults |
| `tests/worker_matcher_test.py` (Phase 3.6.2) | **41** | Empty-registry NO_ELIGIBLE, single-eligible SELECTED, deterministic first by worker_id, byte-identical repeat, registration-order independence, tenant mismatch NO/TENANT_REJECTED, no cross-tenant leakage, LIVE accepted, REGISTERED rejected (require_live default), STALE/DEPARTED rejected, require_live=False semantics, epoch supersede, stale-instance rejection, tool-class match/miss/multi, runtime-feature match/miss/invalid, isolation match/mismatch, arch match/mismatch, capacity-never-hard-gate, capability-never-authorization, candidate/no-candidate invariants, sorted matched attrs, no dup attrs, immutable result, registry unchanged after match, **read-only spy** (only `status`/`list`, zero foreign access, empty-path short-circuit), **no forbidden imports**, **public surface exactly `{match, evaluate}`**, no lease/retry/task-state fields in serialized decisions, JSON round-trip both decision paths, frozen-contract composition |

Numbering note: the matcher suite's method prefixes run 1–44 but several groups (40/41/42, 35–39/44) share prefixes across `test_40_41_42_*` methods, so actual method count is 41. The contract suite runs 1–43. **Combined: 84 new tests.**

| Group (gate §21) | Covered by |
|---|---|
| 1 Determinism | contract 12/27; matcher 3/4/5/31 |
| 2 No eligible | contract 3/9; matcher 1/16/19/29 |
| 3/4/22 Stale/Departed/registered | contract 33/34; matcher 9/10/11/12 |
| 5 Epoch | contract 32; matcher 13/14 |
| 6 Tenant isolation | contract 30/31; matcher 6/7/30 |
| 7 Capability hard+soft | contract 36/37; matcher 15–24/31 |
| 8/9 Spoofing + ≠ authz | contract 28/29; matcher 27 |
| 10/11/25/26 Duplicate + idempotency | contract 25/26/12 |
| 12 Lease race | contract 35/38; matcher 35 |
| 13 Worker crash | unchanged (EE suite) |
| 14/15 Late/transport | unchanged (EE/Hermes suites) |
| 16 Capacity soft-only | contract 23; matcher 25_26 |
| 17 Observability | contract 39 |
| 18/19 Legacy + Hermes compat | full 292 regression |
| 20 Full regression | `unittest discover` → 292 OK |
| 21 Authority absence | contract 17–22; matcher authority |
| 22 LIVE-only default | contract 33/34; matcher 8/9/12 |

## 13. Risks

| # | Risk | Mitigation |
|---|---|---|
| 1 | Seam becomes a scheduler | Public surface frozen to `{match, evaluate}`; no schedule/claim/lease methods; gate I4/I5/I6 asserted |
| 2 | Capability treated as authorization | I3 contract/matcher tests assert no authorize/grant/permission/trust fields; descriptive-only posture |
| 3 | Capability trust (forged caps) | No attestation claimed; governed boundary fail-closed remains the control; spoofing test 29 |
| 4 | Tenant leakage | Hard tenant filter via `list(tenant_scope=...)`; immutable identity scope; tests 6/7/30/31 |
| 5 | Worker spoofing | Identity never authority; decisions descriptive; EE correlation preserved by future wiring |
| 6 | Nondeterministic selection | Frozen single ordering; sorted/byte-identical tests |
| 7 | Starvation | Deterministic order + EE concurrency limits; fairness future work (gate OPEN) |
| 8 | Duplicate dispatch | No execution identity minted (`DispatchDecision` carries no job_id/idempotency_key); Hermes dedup unchanged |
| 9 | Split brain / second dispatch authority | Seam is read-only; unwired; no writer surface |
| 10 | Stale registry | Re-validation at call time (list snapshot); LIVE default; epoch supersede |
| 11 | Capacity deception | Capacity absent from constraints/policy (soft-only by construction) |
| 12 | Observability gaps | Correlation lineage on deterministic dicts; events deferred as gate mandates |
| 13 | Remote-worker security | No new transport; gate OPEN for 3.7+ |
| 14 | Policy duplication | No policy engine; EE + governance remain sole policy owners |
| 15 | Job tenant context missing | `tenant_scope` is caller-supplied; matching tenant-agnostic when omitted — documented OPEN, not invented |
| 16 | Attestation absence | Explicitly documented; no fake attestation fields |
| 17 | Dispatch seam unwired | **Explicitly documented here**: no runtime behavior change; wiring is gated (gate §25 prerequisite #4) |
| 18 | Contract drift | Frozen contracts untouched (mtime §16); the new contracts compose frozen enums only |
| 19 | In-memory registry loss | Re-register fresh instance+epoch; EE lease/sweep composes |
| 20 | Late result after terminal | Terminal CAS remains EE-only; no new writer |
| 21 | Cross-process contention | **Zero schema writes**; no SQLite touch in the seam |
| 22 | Selection re-validation gap | Snapshot consumed at call time; DEPARTED/stale/new-epoch never selected |

## 14. Recommendation

**Accept Phase 3.6** as delivered: an **unwired, read-only, in-memory, deterministic-first-eligible dispatch/matching seam** (`dispatch_contracts.py` + `worker_matcher.py`) implementing gate §25 "PROPOSED" option A (Registry-only matching). The frozen Execution Engine, Hermes Adapter, HermesRuntime, Worker Registry, and all 3.1–3.5 contracts are untouched. The seam reports candidate selection but decides nothing; it remains disconnected from the execution path pending the gate's own wiring decision (§25 prerequisite #4). First new transport (SubprocessTransport) remains Phase 3.7, gated on evidence.

**Reconciliation with gate §25 "MUST NOT IMPLEMENT":** that clause governs the gate-document phase (the gate itself was delivered as DESIGN ONLY). The gate's **PROPOSED** section and §27 "Recommended next phase" explicitly direct "Phase 3.6 implementation (dispatch/matching seam, Registry-only matching, deterministic-first-eligible)" with exactly the shape delivered: Option A, frozen single ordering, LIVE-only default, tenant-scoped hard filter, capacity-never-hard-gate, no new runtime contract, zero authority surface, no wiring. This delivery implements the gate's PROPOSED seam within the gate's frozen boundaries. What the gate's MUST-NOT list actually prohibits — wiring into EE/adapter, scheduling semantics beyond first-eligible, new transports, events, contract mutation — **was not done**.

## 15. Invariants I1–I22 Verification (via tests)

- **I1** EE sole execution authority — matcher surface `{match, evaluate}` only; no claim/attempt APIs (matcher authority; contract 17)
- **I2/I3** Registry descriptive; capability ≠ authorization — contract 21/28/29; matcher 27
- **I4** No lease ownership — contract 18/35/38; matcher 35
- **I5** No retry ownership — contract 19; matcher 36
- **I6** No task-state ownership — contract 20; matcher 37
- **I7/I8** `job_id == execution_id`, `idempotency_key == execution_id` — frozen contracts untouched; new contracts carry no job/idempotency fields (contract 25); full suite green
- **I9** Tenant isolation — contract 30/31; matcher 6/7
- **I10** Epoch prevents zombie identity — contract 32; matcher 13/14
- **I11** Liveness ≠ lease — matcher 35; contract 33/34
- **I12** Late results cannot overwrite — terminal CAS remains EE-only; no writer surface (contract 17–22)
- **I13** No second audit authority — seam emits no events, writes no audit rows (spy test)
- **I14** No autonomous worker policy — no approve/allow/grant/execute surface (contract 21; matcher authority)
- **I15** Hermes remains transport abstraction — frozen seam untouched (mtime §16)
- **I16** Legacy execution compatible — 292-suite + acceptance ALL PASS
- **I17** Frozen 3.1–3.5 contracts compatible — no frozen file modified (mtime §16)
- **I18** Selection cannot bypass governance — seam is descriptive; governance boundary untouched; unwired
- **I19** No second execution identity — contract 25/26
- **I20** Deterministic + tenant-scoped selection — contract 12/27/30; matcher 3/4/5/6/7/31
- **I21** Re-validates liveness/epoch at call time — matcher 10/11/13/14; snapshot semantics
- **I22** Capacity never a hard gate — contract 23; matcher 25_26

## 16. Frozen-File Verification

- `/Users/delit/JARVIS/jarvis` is **not a git repository** (confirmed previously: `git status` → `fatal: not a git repository`), so git-diff verification is unavailable.
- **mtime verification** (`ls -lT` over `agent/*.py` + the two test suites):

| File | mtime | Session |
|---|---|---|
| `agent/dispatch_contracts.py` | Aug 12 11:52 | **Phase 3.6 (this)** |
| `agent/worker_matcher.py` | Aug 12 12:18 | **Phase 3.6 (this)** |
| `tests/dispatch_contracts_test.py` | Aug 12 11:56 | **Phase 3.6 (this)** |
| `tests/worker_matcher_test.py` | Aug 12 12:20 | **Phase 3.6 (this)** |
| `agent/worker_registry.py` | Aug 12 08:31 | Phase 3.5 |
| `tests/worker_registry_test.py` | Aug 12 08:42 | Phase 3.5 |
| `agent/worker_contracts.py` | Aug 12 07:53 | Phase 3.5 |
| `agent/runtime_contracts.py` | Aug 11 19:31 | frozen (pre-3.5) |
| `agent/hermes_runtime.py` | Aug 11 19:55 | frozen (3.4) |
| `agent/hermes_adapter.py` | Aug 11 21:46 | frozen (3.4) |
| `agent/execution_engine.py` | Aug 11 21:34 | frozen (3.3) |
| `agent/mission_engine.py` | Aug 11 15:14 | frozen (3.1) |
| `agent/task_graph.py` | Aug 11 15:57 | frozen (3.2) |

Only the **4 new Phase 3.6 files** were written in this phase's window (Aug 12 11:52–12:20). Every frozen file predates this session.
- **No new dependencies**: both new modules import stdlib only (`json`, `dataclasses`, `enum`, `typing`, `collections.abc`, `inspect` in tests, `unittest` in tests) plus relative imports of **frozen** `.runtime_contracts` / `.worker_contracts`. `worker_matcher` imports neither the registry, Hermes, EE, audit, tools, mission_engine nor task_graph (asserted by test).
- **Prior-phase doc note**: Phase 3.5 delivery §11 proposed a `WorkerRegistry.unregister()`; the delivered registry has 8 public methods without it (gate §1.4 confirms). Recorded as context; not re-opened in Phase 3.6.

## 17. Verification Evidence

| Check | Result |
|---|---|
| `python3 tests/dispatch_contracts_test.py` | **43/43 OK** (0.003s) |
| `python3 -m unittest tests.worker_matcher_test -v` | **41/41 OK** (0.006s) |
| `python3 -m unittest discover -s tests -p "*_test.py"` | **292 tests OK** (18.582s) — 208 frozen/3.5 baseline + 84 new Phase 3.6 |
| `python3 scripts/acceptance_phase32.py` | **OVERALL: ALL PASS** (C1–C8, incl. C7b/C7c/C7d + C8 legacy payload) |
| Import smoke (`agent.dispatch_contracts`, `agent.worker_matcher`, `agent.worker_registry`) | OK |
| Stdlib-only imports on new agent modules | verified via grep (json/dataclasses/enum/typing/collections.abc + frozen relative imports) |
| Forbidden imports (`hermes`/`execution_engine`/`audit`/`tools`/`worker_registry`/`mission_engine`/`task_graph`) in `worker_matcher` | absent (test + grep) |
| Frozen-file mtimes | all frozen files Aug 11; only 4 new Phase 3.6 files in this window |
| Pylance | 0 errors on new files |

## 18. STOP

Phase 3.6 dispatch/matching seam delivered and verified: **contract layer + read-only deterministic matcher over the Phase 3.5 registry, unwired, zero policy authority**. No wiring into the Execution Engine/Hermes Adapter call path, no scheduler/dispatcher/assignment logic, no capability enforcement, no new transports, no `DISPATCH_*`/`WORKER_*` event emission, no contract mutation, no schema writes. No implementation of Phase 3.6+ beyond the seam (dispatch wiring, worker events, new transports, resource governance, capability enforcement) was performed. No further changes will be made without explicit approval.

---

PHASE 3.6 STATUS: DELIVERED (CONTRACTS + MATCHER, UNWIRED) — WIRING DEFERRED