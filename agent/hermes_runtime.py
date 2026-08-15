#!/usr/bin/env python3
"""Hermes Runtime (Phase 3.4.2) — in-process runtime transport behind the frozen
Phase 3.4 contract seam (agent/runtime_contracts.py).

ARCHITECTURAL RULE
------------------
Hermes is a RUNTIME / EXECUTION SUBSTRATE, NOT a scheduler, task graph,
retry authority, lease authority, governance engine, or audit system.

  HEER -> Mission Engine -> Task Graph/DAG -> Execution Engine -> HermesRuntime

Execution Engine remains authoritative for:
  - execution_id
  - attempt lifecycle
  - task state transitions (READY/RUNNING/COMPLETED/FAILED/BLOCKED/CANCELLED)
  - leases (lease_owner / lease_expires_at / claim / reclaim)
  - retries / exponential backoff / max attempts
  - cancellation policy
  - timeout policy (EE decides what TIMED_OUT means for attempts/tasks)
  - final execution persistence

Hermes owns ONLY runtime transport/lifecycle concerns:
  - dispatch/queue of one already-authorized RuntimeRequest
  - cooperative in-process tool invocation through tools.call_tool
  - transport outcome reporting (SUCCEEDED / FAILED / CANCELLED / TIMED_OUT)
  - transport-local heartbeat/status (liveness only, never leases)
  - bounded, idempotent recovery of runtime handles it can identify

This transport is intentionally in-process: no subprocess, no shell, no eval,
no exec, no network, no external queues, no containers, no new DB authority.
Future transports (subprocess -> container -> remote -> K8s) implement the same
public surface without changing Execution Engine semantics.
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from . import audit, tools
from .runtime_contracts import (
    RuntimeCapabilities, RuntimeCapability, RuntimeError, RuntimeErrorType,
    RuntimeHandle, RuntimeIsolation, RuntimeRequest, RuntimeResult,
    RuntimeResultStatus, RuntimeTransportKind, _json_safe_copy,
)

__all__ = ["HermesRuntime"]

_REDACTED_JSON = {"note": "[redacted]"}


def _safe_summary(value):
    """Always-JSON-safe, secret-redacted dict snapshot for events/audit."""
    try:
        safe = _json_safe_copy(value, redact=True)
    except Exception:
        return dict(_REDACTED_JSON)
    if isinstance(safe, dict):
        return safe
    return {"_summary": json.dumps(safe, ensure_ascii=True, default=str)[:500]}


class HermesRuntime:
    """In-process Hermes runtime transport behind the Phase 3.4 seam.

    Public surface (transport-level only):
      capabilities / submit / start / cancel / heartbeat / status / result /
      terminate / recover / events
    """

    def __init__(self, *, transport=RuntimeTransportKind.INPROCESS,
                 isolation=RuntimeIsolation.NONE, max_concurrency=8,
                 supports_hard_timeout=True, supports_secrets=False,
                 supports_tenant_isolation=False, governance_check=None,
                 event_sink=None, auto_start=False):
        """Create an in-process runtime gateway.

        governance_check: optional callable(RuntimeRequest) -> bool, supplied by
        the governing layer. It NEVER grants authorization — when provided it
        can only fail-closed. Default None == "request is already authorized".
        """
        if not isinstance(transport, RuntimeTransportKind):
            raise ValueError("transport must be a RuntimeTransportKind")
        if not isinstance(isolation, RuntimeIsolation):
            raise ValueError("isolation must be a RuntimeIsolation")
        max_concurrency = int(max_concurrency)
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        if governance_check is not None and not callable(governance_check):
            raise ValueError("governance_check must be callable or None")

        self._runtime_id = "hrm_" + uuid.uuid4().hex[:12]
        self._transport_kind = transport
        self._isolation = isolation
        self._max_concurrency = max_concurrency
        self._supports_hard_timeout = bool(supports_hard_timeout)
        self._supports_secrets = bool(supports_secrets)
        self._supports_tenant_isolation = bool(supports_tenant_isolation)
        self._governance_check = governance_check
        self._event_sink = event_sink
        self._auto_start = bool(auto_start)

        _features = {RuntimeCapability.CANCELLATION, RuntimeCapability.HEARTBEAT}
        if self._supports_hard_timeout:
            _features.add(RuntimeCapability.TIMEOUT)
        self._capabilities = RuntimeCapabilities(
            transport=self._transport_kind, isolation=self._isolation,
            max_concurrency=self._max_concurrency,
            supports_heartbeat=True,
            supports_hard_timeout=self._supports_hard_timeout,
            supports_secrets=self._supports_secrets,
            supports_tenant_isolation=self._supports_tenant_isolation,
            features=frozenset(_features))

        self._lock = threading.RLock()
        self._jobs = {}            # execution_id -> entry
        self._keys = {}            # idempotency_key -> execution_id
        self._handles = {}         # handle_id -> execution_id
        self._events = []          # transport-local correlated event ring
        self._closed = False
        self._executor = ThreadPoolExecutor(
            max_workers=self._max_concurrency, thread_name_prefix="heer-hermes")

        self._monitor = threading.Thread(
            target=self._monitor_loop, daemon=True, name="heer-hermes-monitor")
        self._monitor.start()

    # ------------------------------------------------------------------
    # Capability reporting (capability only — NEVER authorization)
    # ------------------------------------------------------------------

    def capabilities(self):
        """Return the transport's frozen RuntimeCapabilities."""
        return self._capabilities

    # ------------------------------------------------------------------
    # Submission / identity / idempotency
    # ------------------------------------------------------------------

    def submit(self, request):
        """Queue an already-authorized RuntimeRequest.

        Returns the RuntimeHandle. Deduplicated by idempotency_key
        (defaults to execution identity): a duplicate submission returns the
        existing handle and NEVER creates a second runtime job.

        Raises ValueError on:
          - non-RuntimeRequest
          - conflicting execution identity for an existing idempotency key
          - submission to a terminated runtime
        """
        if not isinstance(request, RuntimeRequest):
            raise ValueError("submit() requires a RuntimeRequest")
        if request.job.job_id != request.job.execution_id:
            raise ValueError("job_id must equal execution_id (canonical dedup identity)")

        key = request.idempotency_key
        with self._lock:
            if self._closed:
                raise ValueError("hermes runtime is closed")
            existing = self._keys.get(key)
            if existing is not None:
                if existing != request.job.execution_id:
                    raise ValueError(
                        f"conflicting execution identity for idempotency key {key!r}")
                entry = self._jobs[existing]
                entry["submitted_count"] += 1
                self._emit("TRANSPORT_DUPLICATE_SUBMIT", entry, {"key": key})
                return entry["handle"]

            exec_id = request.job.execution_id
            if exec_id in self._jobs:
                raise ValueError(f"execution already tracked: {exec_id}")

            handle = RuntimeHandle(
                handle_id="hrm_" + uuid.uuid4().hex[:12],
                execution_id=exec_id,
                runtime_id=self._runtime_id,
                submitted_at=time.time(),
                worker_id=None)

            entry = {
                "request": request,
                "handle": handle,
                "phase": "QUEUED",
                "final_status": None,
                "result": None,
                "cancel_event": threading.Event(),
                "timed_out": False,
                "deadline": None,
                "thread": None,
                "submitted_count": 1,
                "tool_calls": 0,
            }
            self._jobs[exec_id] = entry
            self._keys[key] = exec_id
            self._handles[handle.handle_id] = exec_id
            self._emit("TRANSPORT_SUBMITTED", entry, {"idempotency_key": key})

            if self._auto_start:
                self.start(handle.handle_id)

            return handle

    # ------------------------------------------------------------------
    # Lifecycle (transport-level only)
    # ------------------------------------------------------------------

    def start(self, handle_id):
        """Start a queued dispatch. Idempotent for RUNNING/TERMINAL entries."""
        with self._lock:
            entry = self._by_handle(handle_id)
            if entry is None:
                return {"ok": False, "error": f"unknown handle {handle_id!r}"}
            if entry["phase"] == "TERMINAL":
                return {"ok": True, "execution_id": entry["handle"].execution_id,
                        "phase": "TERMINAL", "status": entry["final_status"].value}
            if entry["phase"] == "RUNNING":
                return {"ok": True, "execution_id": entry["handle"].execution_id,
                        "phase": "RUNNING"}
            if self._closed:
                self._finalize(entry, RuntimeResultStatus.CANCELLED,
                               error=self._err(entry, RuntimeErrorType.UNKNOWN,
                                               "runtime terminated before start"))
                return {"ok": True, "execution_id": entry["handle"].execution_id,
                        "phase": "TERMINAL", "status": entry["final_status"].value}
            entry["phase"] = "RUNNING"
            entry["deadline"] = None
            if (self._supports_hard_timeout
                    and entry["request"].job.timeout_sec is not None
                    and entry["request"].job.timeout_sec > 0):
                entry["deadline"] = time.time() + entry["request"].job.timeout_sec
            self._emit("TRANSPORT_STARTED", entry, {})
            self._executor.submit(self._run, entry["handle"].execution_id)
            return {"ok": True, "execution_id": entry["handle"].execution_id,
                    "phase": "RUNNING"}

    def cancel(self, handle_id):
        """Cooperative, idempotent cancellation. Never force-kills the tool."""
        with self._lock:
            entry = self._by_handle(handle_id)
            if entry is None:
                return {"ok": False, "error": f"unknown handle {handle_id!r}"}
            if entry["phase"] == "TERMINAL":
                return {"ok": True, "execution_id": entry["handle"].execution_id,
                        "already_terminal": True, "status": entry["final_status"].value}
            entry["cancel_event"].set()
            self._emit("TRANSPORT_CANCEL_REQUESTED", entry, {})
            if entry["phase"] == "QUEUED":
                self._finalize(entry, RuntimeResultStatus.CANCELLED,
                               error=self._err(entry, RuntimeErrorType.UNKNOWN,
                                               "cancelled before dispatch"))
            # RUNNING entries are finalized cooperatively by the worker after
            # the tool returns (or by the timeout monitor).
            return {"ok": True, "execution_id": entry["handle"].execution_id,
                    "cooperative": True}

    def terminate(self):
        """Stop accepting work and cooperatively cancel live dispatches.

        The in-process transport cannot force-kill an already-running tool
        thread; cancellation is cooperative. Idempotent.
        """
        with self._lock:
            if self._closed:
                return {"ok": True, "already_terminated": True}
            self._closed = True
            queue = list(self._jobs.values())
        for entry in queue:
            if entry["phase"] != "TERMINAL":
                entry["cancel_event"].set()
                if entry["phase"] == "QUEUED":
                    with self._lock:
                        self._finalize(entry, RuntimeResultStatus.CANCELLED,
                                       error=self._err(
                                           entry, RuntimeErrorType.UNKNOWN,
                                           "runtime terminated"))
        # Cooperative drain — never block callers on a possibly-hung tool.
        def _drain():
            try:
                self._executor.shutdown(wait=True)
            except Exception:
                pass
        threading.Thread(target=_drain, daemon=True, name="heer-hermes-drain").start()
        return {"ok": True, "terminated": True, "live": sum(
            1 for e in self._jobs.values() if e["phase"] == "RUNNING")}

    # ------------------------------------------------------------------
    # Observability (transport-local; audit.record remains the persistent trail)
    # ------------------------------------------------------------------

    def heartbeat(self, handle_id):
        """Transport liveness ping. NEVER touches EE lease state."""
        with self._lock:
            entry = self._by_handle(handle_id)
            if entry is None:
                return {"ok": False, "error": f"unknown handle {handle_id!r}"}
            alive = (entry["phase"] == "RUNNING"
                     and entry["thread"] is not None
                     and entry["thread"].is_alive())
            return {"ok": True, "execution_id": entry["handle"].execution_id,
                    "alive": alive, "phase": entry["phase"],
                    "status": entry["final_status"].value if entry["final_status"] else None,
                    "runtime_id": self._runtime_id,
                    "worker_id": entry["thread"].name if entry["thread"] else None}

    def status(self, handle_id):
        """Transport phase: QUEUED / RUNNING / TERMINAL (with outcome)."""
        with self._lock:
            entry = self._by_handle(handle_id)
            if entry is None:
                return {"ok": False, "error": f"unknown handle {handle_id!r}"}
            return {"ok": True, "execution_id": entry["handle"].execution_id,
                    "handle": entry["handle"],
                    "phase": entry["phase"],
                    "status": entry["final_status"].value if entry["final_status"] else None,
                    "submitted_at": entry["handle"].submitted_at,
                    "duplicate_submissions": entry["submitted_count"]}

    def result(self, handle_id):
        """RuntimeResult once terminal, else None."""
        with self._lock:
            entry = self._by_handle(handle_id)
            if entry is None:
                return None
            return entry["result"]

    def events(self, limit=200):
        """Transport-local correlated events (additive ring). Persistent audit
        remains in agent/audit.py; this never replaces it."""
        with self._lock:
            return list(self._events[-int(limit):])

    # ------------------------------------------------------------------
    # Recovery (bounded, idempotent — runtime handles only)
    # ------------------------------------------------------------------

    def recover(self):
        """Recover runtime handles Hermes can safely identify.

        RUNNING entries whose worker thread is gone are reported FAILED(CRASH,
        retryable=descriptive). Never mutates EE attempts/leases/task state.
        Idempotent.
        """
        with self._lock:
            checked = list(self._jobs.values())
            recovered = []
            for entry in checked:
                if entry["phase"] != "RUNNING":
                    continue
                th = entry["thread"]
                if th is not None and th.is_alive():
                    continue
                self._finalize(
                    entry, RuntimeResultStatus.FAILED,
                    error=self._err(entry, RuntimeErrorType.CRASH,
                                    "hermes worker thread lost (crash recovery)",
                                    retryable=True))
                recovered.append(entry["handle"].execution_id)
        return {"ok": True, "checked": len(checked), "recovered": recovered}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _by_handle(self, handle_id):
        exec_id = self._handles.get(handle_id)
        if exec_id is None:
            return None
        return self._jobs.get(exec_id)

    @staticmethod
    def _err(entry, error_type, message, *, retryable=False, details=None):
        req = entry["request"]
        safe = _safe_summary(details) if details is not None else None
        return RuntimeError(
            error_type=error_type, message=str(message)[:500],
            retryable=retryable,
            execution_id=req.job.execution_id, job_id=req.job.job_id,
            runtime_id=entry["handle"].runtime_id,
            correlation_id=req.job.correlation_id,
            details=safe)

    def _emit(self, event_type, entry, detail):
        req = entry["request"]
        ev = {
            "ts": time.time(),
            "runtime_id": self._runtime_id,
            "event_type": event_type,
            "execution_id": req.job.execution_id,
            "mission_id": req.job.mission_id,
            "task_id": req.job.task_id,
            "attempt_no": req.job.attempt_no,
            "correlation_id": req.job.correlation_id,
            "detail": _safe_summary(detail or {}),
        }
        with self._lock:
            self._events.append(ev)
            if self._event_sink is not None:
                try:
                    self._event_sink(ev)
                except Exception:
                    pass

    def _audit(self, intent, entry, success, detail="", tool=None):
        req = entry["request"]
        corr = {"mission_id": req.job.mission_id, "task_id": req.job.task_id,
                "execution_id": req.job.execution_id,
                "attempt_no": req.job.attempt_no,
                "correlation_id": req.job.correlation_id}
        try:
            audit.record(
                request=f"{intent} mission={req.job.mission_id} "
                        f"task={req.job.task_id} execution={req.job.execution_id} "
                        f"attempt={req.job.attempt_no} {str(detail)[:200]}",
                intent=intent, agent_id="hermes_runtime",
                tools=[tool or intent],
                inputs={k: v for k, v in corr.items()},
                outputs={"success": bool(success), "runtime_id": self._runtime_id},
                approval={"blocked": False}, success=bool(success), lat_ms=0)
        except Exception:
            pass

    def _finalize(self, entry, status, *, error=None, output=None, metadata=None,
                  tool_output_lat_ms=None, tool_name=None):
        """Single-writer outcome: compare-and-swap under lock."""
        with self._lock:
            if entry["phase"] == "TERMINAL":
                return False
            req = entry["request"]
            now = time.time()
            started = entry["thread"] and getattr(entry["thread"], "started_at", None)
            result = RuntimeResult(
                execution_id=req.job.execution_id,
                job_id=req.job.job_id,
                status=status,
                output=_safe_summary(output) if output is not None else None,
                error=error,
                started_at=entry.get("started_at"),
                finished_at=now,
                runtime_id=self._runtime_id,
                worker_id=entry["thread"].name if entry["thread"] else None,
                correlation_id=req.job.correlation_id,
                metadata=_safe_summary(metadata or {}))
            entry["result"] = result
            entry["final_status"] = status
            entry["phase"] = "TERMINAL"
            self._emit(f"TRANSPORT_{status.value}", entry,
                       {"lat_ms": tool_output_lat_ms} if tool_output_lat_ms is not None
                       else {})
            self._audit(f"runtime_{status.value.lower()}",
                        entry, status == RuntimeResultStatus.SUCCEEDED,
                        detail=str(error.message if error else "")[:200],
                        tool=tool_name)
            return True

    def _run(self, exec_id):
        entry = self._jobs.get(exec_id)
        if entry is None or entry["phase"] != "RUNNING":
            return
        with self._lock:
            entry["thread"] = threading.current_thread()
            entry["thread"].started_at = time.time()
            entry["started_at"] = entry["thread"].started_at
            req = entry["request"]
            job = req.job
            tool_name = str(job.metadata.get("tool", "") or "").strip()

            if entry["cancel_event"].is_set():
                self._finalize(entry, RuntimeResultStatus.CANCELLED,
                               error=self._err(entry, RuntimeErrorType.UNKNOWN,
                                               "cancelled before tool invocation"),
                               tool_name=tool_name)
                return

            if self._governance_check is not None:
                approved = False
                try:
                    approved = bool(self._governance_check(req))
                except Exception as exc:
                    self._finalize(
                        entry, RuntimeResultStatus.FAILED,
                        error=self._err(entry, RuntimeErrorType.GOVERNANCE_DENIED,
                                        f"governance check errored: {exc}"),
                        tool_name=tool_name)
                    return
                if not approved:
                    self._finalize(
                        entry, RuntimeResultStatus.FAILED,
                        error=self._err(entry, RuntimeErrorType.GOVERNANCE_DENIED,
                                        "blocked by governance boundary"),
                        tool_name=tool_name)
                    return

            req_caps = req.capabilities_required
            if req_caps is not None:
                unsupported = (set(getattr(req_caps, "features", frozenset()))
                               - set(self._capabilities.features))
                if unsupported:
                    self._finalize(
                        entry, RuntimeResultStatus.FAILED,
                        error=self._err(
                            entry, RuntimeErrorType.TRANSPORT,
                            f"unsupported required capabilities: "
                            f"{sorted(f.value for f in unsupported)}"),
                        tool_name=tool_name)
                    return

            if not tool_name:
                self._finalize(entry, RuntimeResultStatus.FAILED,
                               error=self._err(entry, RuntimeErrorType.UNKNOWN,
                                               "no metadata['tool'] provided"),
                               tool_name=None)
                return

        # ---- Invoke through the governed tool boundary only ----
        self._emit("TRANSPORT_TOOL_CALL", entry, {"tool": tool_name})
        entry["tool_calls"] += 1
        t0 = time.time()
        biz = None
        raw_input = dict(job.input)
        if isinstance(raw_input.get("_business_id"), str):
            biz = raw_input["_business_id"]
        result = tools.call_tool(tool_name, raw_input, business_id=biz)
        lat_ms = int((time.time() - t0) * 1000)

        with self._lock:
            if entry["timed_out"] or entry["phase"] == "TERMINAL":
                return  # monitor or another writer already finalized this dispatch
            if entry["cancel_event"].is_set() and not (isinstance(result, dict)
                                                       and result.get("ok") is True):
                self._finalize(entry, RuntimeResultStatus.CANCELLED,
                               error=self._err(entry, RuntimeErrorType.UNKNOWN,
                                               "cancelled during tool execution"),
                               tool_output_lat_ms=lat_ms, tool_name=tool_name)
                return

            if not isinstance(result, dict) or "ok" not in result:
                self._finalize(
                    entry, RuntimeResultStatus.FAILED,
                    error=self._err(entry, RuntimeErrorType.INVALID_RESULT,
                                    "tool returned malformed result (missing ok)"),
                    tool_output_lat_ms=lat_ms, tool_name=tool_name)
                return

            if result.get("ok") is True:
                if entry["cancel_event"].is_set():
                    # Cooperative supersede: cancellation requested during run
                    self._finalize(entry, RuntimeResultStatus.CANCELLED,
                                   error=self._err(
                                       entry, RuntimeErrorType.UNKNOWN,
                                       "cancelled after tool returned"),
                                   metadata={"tool_returned_ok": True},
                                   tool_output_lat_ms=lat_ms, tool_name=tool_name)
                    return
                self._finalize(entry, RuntimeResultStatus.SUCCEEDED,
                               output=result,
                               metadata={"lat_ms": lat_ms},
                               tool_output_lat_ms=lat_ms, tool_name=tool_name)
                return

            # Tool reported failure (call_tool never raises; wraps exceptions)
            self._finalize(
                entry, RuntimeResultStatus.FAILED,
                error=self._err(entry, RuntimeErrorType.UNKNOWN,
                                str(result.get("error") or "tool failed"),
                                retryable=True,
                                details={"tool": tool_name, "lat_ms": lat_ms}),
                tool_output_lat_ms=lat_ms, tool_name=tool_name)

    def _monitor_loop(self):
        """Timeout observation only — never retry/lease/task authority."""
        while True:
            with self._lock:
                if self._closed:
                    break
                now = time.time()
                for entry in list(self._jobs.values()):
                    if entry["phase"] != "RUNNING" or entry["timed_out"]:
                        continue
                    if entry["deadline"] is None or now < entry["deadline"]:
                        continue
                    entry["timed_out"] = True
                    self._finalize(
                        entry, RuntimeResultStatus.TIMED_OUT,
                        error=self._err(entry, RuntimeErrorType.TIMEOUT,
                                        f"tool exceeded timeout "
                                        f"({entry['request'].job.timeout_sec}s)"),
                        metadata={"timeout_sec": entry["request"].job.timeout_sec,
                                  "tool_completed_after_timeout": False})
            time.sleep(0.05)