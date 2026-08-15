#!/usr/bin/env python3
"""worker_registry.py — HEER Worker Fabric Registry (Phase 3.5.2).

In-memory, thread-safe registry of worker PRESENCE and DESCRIPTIVE STATE only.

SCOPE (frozen — HEER_PHASE35_WORKER_FABRIC_GATE.md sections 3, 6, 9, 11, 15):
  - registered workers (WorkerIdentity)
  - worker instance identity (worker_instance_id)
  - worker epoch (staleness/fencing signal)
  - worker capabilities (DESCRIPTIVE ONLY — capability is never authorization, I10)
  - tenant scope (immutable per registration; tenant-scoped queries only)
  - isolation declaration
  - liveness state (REGISTERED / LIVE / STALE / DEPARTED — fabric-local, NEVER a lease, I11)
  - heartbeat sequence (fabric-local monotonic counter)
  - registration timestamp / last heartbeat timestamp
  - read-only capability discovery

The registry MUST NOT own (gate §15, invariants I1–I8):
  - execution_id / task lifecycle / task state / attempt lifecycle
  - EE leases (lease_owner, lease_expires_at, lease TTL, lease sweep)
  - retry policy / retry counters / backoff / max attempts
  - timeout policy / cancellation policy
  - final execution results
  - authorization decisions / tool governance
  - mission state / scheduling policy

The registry is NOT a scheduler (invariant I11): it schedules nothing, dispatches
nothing, and never selects a worker for work. It reports presence. The Execution
Engine remains the sole execution/lease/retry authority (I1–I4).

Persistence: NONE by design. Gate §22 Q1 explicitly leaves registry persistence
open ("in-memory fabric registry vs a future additive table"); no answer is
invented here. Registry state is process-local: after a server restart, workers
re-register per the gate's worker-restart model (new instance/epoch; old epoch
ignored). This phase creates NO second persistence authority for executions (I12)
and NO competing audit store (I13; worker events are future-additive per gate §12).

Concurrency: single `threading.RLock` guards every public operation. All state
transitions are compare-and-swap sequences inside the lock. No distributed locking.

Security boundaries:
  - worker attestation / identity verification is NOT implemented (gate §22 Q2 open)
  - self-reported capabilities are descriptive; the registry grants nothing
  - executable objects and unsafe payloads are rejected by the frozen contracts
  - secrets are never persisted (no persistence exists) and never emitted
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

from .worker_contracts import (
    WorkerIdentity,
    WorkerLiveness,
    WorkerLivenessState,
    to_dict as worker_contract_to_dict,
)

__all__ = ["WorkerRegistry"]

# Gate §3 — exactly four fabric-local liveness states.
_STATE_ORDER = (WorkerLivenessState.REGISTERED,
                WorkerLivenessState.LIVE,
                WorkerLivenessState.STALE,
                WorkerLivenessState.DEPARTED)


@dataclass
class _Entry:
    """Registry-local mutable row. NOT a public contract; not exported."""
    identity: WorkerIdentity
    state: WorkerLivenessState = WorkerLivenessState.REGISTERED
    registered_at: float = 0.0
    reported_at: Optional[float] = None
    heartbeat_seq: int = 0


class WorkerRegistry:
    """In-memory, thread-safe worker presence registry (execution plane).

    Public operations:
      register(identity)                     — idempotent registration
      heartbeat(...)                         — fabric-local liveness signal
      mark_stale(...)                        — registry-local LIVE -> STALE
      depart(...)                            — registry-local terminal DEPARTED
      get(...) / list(...)                   — read-only presence queries
      list_by_capability(...)                — read-only capability discovery
      status()                               — registry summary

    All mutations are CAS-style, protected by one RLock. All query results are
    JSON-safe deterministic dicts (frozen worker-contract serialization).
    """

    def __init__(self, *, clock: Optional[Callable[[], float]] = None):
        self._lock = threading.RLock()
        self._workers: dict[str, _Entry] = {}
        # Deterministic clock injection for tests; default to wall-clock time.
        self._clock = clock if clock is not None else time.time

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, identity: WorkerIdentity) -> dict:
        """Register a worker (or handle a re-registration collision).

        Returns deterministic dict: {"ok": bool, ...}.

        Collision semantics (gate §3 / §6; no invention beyond the gate):
          - first registration      -> REGISTERED, heartbeat_seq 0
          - same instance + epoch   -> idempotent duplicate (capabilities are
                                       mutable at registration per gate §3; the
                                       registration's state/sequence are preserved)
          - new instance + newer epoch -> supersedes the older entry (new
                                       REGISTERED, sequence reset)
          - new instance + EQUAL epoch -> rejected: the gate binds a restarted
                                       worker to a NEW instance AND a NEW epoch
          - older epoch             -> rejected (stale; cannot overwrite newer state)
        """
        with self._lock:
            if not isinstance(identity, WorkerIdentity):
                return {"ok": False,
                        "error": "identity must be a WorkerIdentity"}
            wid = identity.worker_id
            existing = self._workers.get(wid)
            if existing is None:
                now = self._clock()
                self._workers[wid] = _Entry(
                    identity=identity,
                    state=WorkerLivenessState.REGISTERED,
                    registered_at=now,
                    reported_at=None,
                    heartbeat_seq=0,
                )
                return {
                    "ok": True,
                    "worker_id": wid,
                    "state": WorkerLivenessState.REGISTERED.value,
                    "duplicate": False,
                }

            cur = existing.identity
            same_instance = (cur.worker_instance_id == identity.worker_instance_id)
            same_epoch = (cur.worker_epoch == identity.worker_epoch)

            # Duplicate registration — idempotent; capabilities mutable per gate §3.
            if same_instance and same_epoch:
                existing.identity = identity  # identical ids, fresh capabilities
                return {
                    "ok": True,
                    "worker_id": wid,
                    "state": existing.state.value,
                    "duplicate": True,
                }

            # Newer epoch supersedes (always — never let older data win).
            if identity.worker_epoch > cur.worker_epoch:
                now = self._clock()
                self._workers[wid] = _Entry(
                    identity=identity,
                    state=WorkerLivenessState.REGISTERED,
                    registered_at=now,
                    reported_at=None,
                    heartbeat_seq=0,
                )
                return {
                    "ok": True,
                    "worker_id": wid,
                    "state": WorkerLivenessState.REGISTERED.value,
                    "duplicate": True,
                    "superseded": True,
                }

            # New instance without a newer epoch — gate-model violation.
            if identity.worker_epoch == cur.worker_epoch and not same_instance:
                return {
                    "ok": False,
                    "error": ("new worker instance requires worker_epoch > "
                              f"current epoch ({cur.worker_epoch})"),
                }

            # Older epoch — stale; cannot revive/overwrite a newer registration.
            return {
                "ok": False,
                "error": "stale epoch",
                "stale": True,
                "current_epoch": cur.worker_epoch,
            }

    # ------------------------------------------------------------------
    # Heartbeat (fabric-local liveness — NEVER an EE lease, I11)
    # ------------------------------------------------------------------

    def heartbeat(self, *, worker_id: str, worker_instance_id: str,
                  worker_epoch: int, heartbeat_seq: int,
                  reported_at: float) -> dict:
        """Process a fabric-local worker heartbeat.

        Validates via the frozen WorkerLiveness contract, then applies the
        registry-local transition. Monotonic heartbeat_seq is the ordering
        guard; timestamps are recorded, not used for ordering.
        """
        with self._lock:
            # Validate through the frozen contract (rejects NaN/inf, bad seq,
            # bad ids, string enums, etc.).
            try:
                WorkerLiveness(
                    worker_id=worker_id,
                    worker_instance_id=worker_instance_id,
                    worker_epoch=worker_epoch,
                    state=WorkerLivenessState.LIVE,
                    reported_at=reported_at,
                    heartbeat_seq=heartbeat_seq,
                )
            except ValueError as exc:
                return {"ok": False, "error": f"invalid heartbeat: {exc}"}

            entry = self._workers.get(worker_id)
            if entry is None:
                return {"ok": False, "error": "worker not registered"}

            cur = entry.identity
            if (cur.worker_instance_id != worker_instance_id
                    or cur.worker_epoch != worker_epoch):
                return {
                    "ok": False,
                    "error": "stale heartbeat (instance/epoch mismatch)",
                    "stale": True,
                }

            if entry.state is WorkerLivenessState.DEPARTED:
                return {"ok": False,
                        "error": "worker departed; heartbeat rejected"}

            if heartbeat_seq < entry.heartbeat_seq:
                return {
                    "ok": False,
                    "error": "heartbeat sequence regression",
                    "current_seq": entry.heartbeat_seq,
                }

            if heartbeat_seq == entry.heartbeat_seq:
                return {
                    "ok": True,
                    "worker_id": worker_id,
                    "state": entry.state.value,
                    "seq": heartbeat_seq,
                    "duplicate": True,
                }

            # Strictly greater sequence: register the beat, promote liveness.
            if entry.state is WorkerLivenessState.REGISTERED:
                entry.state = WorkerLivenessState.LIVE
            elif entry.state is WorkerLivenessState.STALE:
                entry.state = WorkerLivenessState.LIVE  # current instance proved alive
            entry.heartbeat_seq = heartbeat_seq
            entry.reported_at = reported_at
            return {
                "ok": True,
                "worker_id": worker_id,
                "state": entry.state.value,
                "seq": heartbeat_seq,
                "duplicate": False,
            }

    # ------------------------------------------------------------------
    # Stale detection / departure (registry-local only)
    # ------------------------------------------------------------------

    def mark_stale(self, *, worker_id: str, worker_instance_id: str,
                   worker_epoch: int) -> dict:
        """Registry-local LIVE -> STALE transition for the current instance.

        Records ONLY worker-fabric liveness. Never touches executions, leases,
        retries, task states, or transport state (gate §6 / I7 / I8).
        """
        with self._lock:
            entry = self._workers.get(worker_id)
            if entry is None:
                return {"ok": False, "error": "worker not registered"}
            cur = entry.identity
            if (cur.worker_instance_id != worker_instance_id
                    or cur.worker_epoch != worker_epoch):
                return {"ok": False,
                        "error": "stale (instance/epoch mismatch)"}
            if entry.state is WorkerLivenessState.DEPARTED:
                return {"ok": False, "error": "worker departed"}
            if entry.state is WorkerLivenessState.STALE:
                return {"ok": True,
                        "worker_id": worker_id,
                        "state": WorkerLivenessState.STALE.value,
                        "duplicate": True}
            entry.state = WorkerLivenessState.STALE
            return {"ok": True,
                    "worker_id": worker_id,
                    "state": WorkerLivenessState.STALE.value}

    def depart(self, *, worker_id: str, worker_instance_id: str,
               worker_epoch: int) -> dict:
        """Idempotent terminal DEPARTED transition for the current instance.

        A departed worker is never revived by a heartbeat; a NEW instance with a
        NEWER epoch may register fresh (gate §3 / §6).
        """
        with self._lock:
            entry = self._workers.get(worker_id)
            if entry is None:
                return {"ok": False, "error": "worker not registered"}
            cur = entry.identity
            if (cur.worker_instance_id != worker_instance_id
                    or cur.worker_epoch != worker_epoch):
                return {"ok": False,
                        "error": "stale (instance/epoch mismatch)"}
            if entry.state is WorkerLivenessState.DEPARTED:
                return {"ok": True,
                        "worker_id": worker_id,
                        "state": WorkerLivenessState.DEPARTED.value,
                        "duplicate": True}
            entry.state = WorkerLivenessState.DEPARTED
            return {"ok": True,
                    "worker_id": worker_id,
                    "state": WorkerLivenessState.DEPARTED.value}

    # ------------------------------------------------------------------
    # Read-only queries (descriptive only — never authorization)
    # ------------------------------------------------------------------

    def get(self, worker_id: str, *, tenant_scope: Optional[str] = None) -> Optional[dict]:
        """Return the registry entry for a worker, or None.

        `tenant_scope` optionally narrows visibility: a worker that does not
        serve that tenant is invisible to that tenant's view.
        """
        with self._lock:
            entry = self._workers.get(worker_id)
            if entry is None:
                return None
            if tenant_scope is not None and tenant_scope not in entry.identity.tenant_scope:
                return None
            return self._entry_dict(entry)

    def list(self, *, tenant_scope: Optional[str] = None) -> list:
        """All registered workers (deterministic worker_id order).

        `tenant_scope` narrows to workers serving that tenant, preserving the
        gate's tenant isolation boundary (I9).
        """
        with self._lock:
            out = []
            for wid in sorted(self._workers):
                entry = self._workers[wid]
                if tenant_scope is not None and tenant_scope not in entry.identity.tenant_scope:
                    continue
                out.append(self._entry_dict(entry))
            return out

    def list_by_capability(self, capability: str,
                           *, tenant_scope: Optional[str] = None) -> list:
        """Read-only capability discovery.

        Matches `capability` against a worker's descriptive `tool_classes` OR its
        frozen `RuntimeCapabilities.features`. Returns workers whose capabilities
        INCLUDE the name — this NEVER authorizes anything (I10). Selection is a
        placement concern; authorization stays in the Execution Engine.
        """
        with self._lock:
            out = []
            for wid in sorted(self._workers):
                entry = self._workers[wid]
                if tenant_scope is not None and tenant_scope not in entry.identity.tenant_scope:
                    continue
                caps = entry.identity.capabilities
                if caps is None:
                    continue
                tool_hit = capability in caps.tool_classes
                feat_hit = False
                if caps.runtime_capabilities is not None:
                    feat_hit = capability in {
                        m.value for m in caps.runtime_capabilities.features
                    }
                if tool_hit or feat_hit:
                    out.append(self._entry_dict(entry))
            return out

    def status(self) -> dict:
        """Registry summary: total + per-liveness-state counts (gate §3 states)."""
        with self._lock:
            counts = {s.value: 0 for s in _STATE_ORDER}
            for entry in self._workers.values():
                counts[entry.state.value] = counts.get(entry.state.value, 0) + 1
            return {
                "total": len(self._workers),
                "by_state": counts,
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _entry_dict(entry: _Entry) -> dict:
        """Deterministic JSON-safe query dict (no lease/retry/task fields)."""
        return {
            "identity": worker_contract_to_dict(entry.identity),
            "state": entry.state.value,
            "registered_at": entry.registered_at,
            "reported_at": entry.reported_at,
            "heartbeat_seq": entry.heartbeat_seq,
        }