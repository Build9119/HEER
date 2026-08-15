#!/usr/bin/env python3
"""Hermes Runtime Adapter (Phase 3.4.2 seam) — thin transport-agnostic bridge
between the Phase 3.3 Parallel Execution Engine and a Hermes-compatible runtime
transport.

ARCHITECTURAL RULE
------------------
The adapter is a TRANSPORT-AGNOSTIC SEAM. It owns NO authority:

  - it never writes Execution Engine state
    (no CAS transitions, no leases, no retries, no task-graph changes)
  - it never decides retry / backoff / cancellation / timeout policy
  - it ONLY: builds a frozen RuntimeRequest from an EE task+execution row,
    submits and starts one transport dispatch, observes the terminal
    RuntimeResult, and maps it back to the tool-shaped dict that the EE worker
    already understands.

Authority boundaries (unchanged from EE_RULES):
  Execution Engine: execution_id, attempt lifecycle, task states
    (READY/RUNNING/COMPLETED/FAILED/BLOCKED/CANCELLED), leases (claim/reclaim),
    retries + exponential backoff + max attempts, cancellation policy, timeout
    policy, final execution persistence.
  Runtime transport: dispatch/queue of one already-authorized request,
    cooperative tool invocation, transport outcome reporting
    (SUCCEEDED/FAILED/CANCELLED/TIMED_OUT), transport-local heartbeat/status,
    bounded idempotent recovery of runtime handles.

The adapter works against ANY transport exposing the Hermes public surface
(submit/start/cancel/heartbeat/status/result/recover/terminate), enabling
future subprocess / container / remote / K8s transports with zero EE changes.
If no runtime is installed, the Execution Engine falls back to the legacy
in-process tools.call_tool path byte-for-byte (install_runtime(None) restores
that path exactly).
"""
from __future__ import annotations

import time
from typing import Any, Callable, Mapping, Optional

from .runtime_contracts import (
    RuntimeCapabilities,
    RuntimeJob,
    RuntimeRequest,
    RuntimeResult,
    RuntimeResultStatus,
)

__all__ = ["RuntimeAdapter", "build_request", "map_result"]


def _timeout_value(timeout_sec):
    """Normalize EE timeout_sec to what RuntimeJob accepts (>0 float | None)."""
    try:
        t = float(timeout_sec)
    except (TypeError, ValueError):
        return None
    return t if t is not None and t > 0 else None


def build_request(*, runtime, execution_id, mission_id, task_id, attempt_no,
                  tool_name, task_input, timeout_sec=None,
                  requested_by="execution_engine", worker_candidate=None):
    """Build a frozen RuntimeRequest for one EE execution dispatch.

    job_id == execution_id (canonical dedup identity per Phase 3.4 contracts),
    idempotency_key defaults to execution_id, and metadata['tool'] carries the
    tool name the transport routes the invocation by (Hermes _run reads exactly
    job.metadata['tool']).  The transport may use capabilities for capability
    gating — NEVER for authorization (the EE is the authorizer).
    """
    capabilities = None
    caps = getattr(runtime, "capabilities", None)
    if callable(caps):
        value = caps()
        if isinstance(value, RuntimeCapabilities):
            capabilities = value

    meta = {
        "tool": tool_name,
        "execution_id": execution_id,
        "mission_id": mission_id,
        "task_id": task_id,
        "attempt_no": int(attempt_no),
    }
    if worker_candidate is not None:
        meta["worker_id"] = worker_candidate.identity.worker_id
        meta["worker_instance_id"] = worker_candidate.identity.worker_instance_id
        meta["worker_epoch"] = worker_candidate.identity.worker_epoch

    job = RuntimeJob(
        job_id=execution_id,
        execution_id=execution_id,
        mission_id=mission_id,
        task_id=task_id,
        attempt_no=int(attempt_no),
        input=dict(task_input or {}),
        metadata=meta,
        timeout_sec=_timeout_value(timeout_sec),
        correlation_id=execution_id,
        capabilities=capabilities,
        cancel_token=None,
    )
    return RuntimeRequest(
        job=job,
        requested_at=time.time(),
        requested_by=requested_by,
        capabilities_required=capabilities,
        idempotency_key=execution_id,
    )


def map_result(result):
    """Map a terminal RuntimeResult to the tools.call_tool-shaped dict the EE
    worker already understands.

    Never raises and never writes EE state. CANCELLED / TIMED_OUT are surfaced
    as distinct flags so the EE worker applies its OWN policy (cooperative
    cancel / timeout-retry decision), not a transport decision.
    """
    if result is None:
        return {"ok": False, "error": "no runtime result (transport lost)"}
    if not isinstance(result, RuntimeResult):
        return {"ok": False, "error": "runtime returned a non-RuntimeResult"}
    if result.status == RuntimeResultStatus.SUCCEEDED:
        out = result.output if isinstance(result.output, Mapping) else {}
        return {"ok": True, "result": dict(out), "runtime_status": "SUCCEEDED"}
    if result.status == RuntimeResultStatus.CANCELLED:
        return {"ok": False, "cancelled": True, "error": "cancelled",
                "runtime_status": "CANCELLED"}
    if result.status == RuntimeResultStatus.TIMED_OUT:
        return {"ok": False, "timed_out": True, "error": "task timeout",
                "runtime_status": "TIMED_OUT"}
    msg = result.error.message if result.error is not None else "runtime failed"
    return {"ok": False, "error": (str(msg) or "runtime failed")[:2000],
                "runtime_status": "FAILED"}


class RuntimeAdapter:
    """Transport-agnostic adapter bound to one runtime instance.

    invoke() is synchronous, exactly like the legacy tools.call_tool call it
    replaces at the worker call site:

      1. build_request()  -> frozen RuntimeRequest
      2. submit()         -> RuntimeHandle (idempotency_key=execution_id dedupes)
      3. start()          -> QUEUED -> RUNNING (or TERMINAL already)
      4. poll result() to terminal, with:
         - cancel_check() -> runtime.cancel(handle) (cooperative; transport
           finalizes CANCELLED on its own schedule)
         - engine_heartbeat() -> renews the EE lease (throttled) so the EE
           lease sweep never reclaims a live worker
         - runtime.recover() -> idempotent crash escalation when a RUNNING
           dispatch stalls past stall_recover_interval
      5. map_result()     -> tool-shaped dict for the EE worker's CAS logic

    If the transport never finalizes within timeout_sec + hard_stop_grace, the
    adapter returns {"ok": False, "runtime_stalled": True} and the EE worker
    treats that as "do NOT touch EE state" — the EE lease sweep remains the
    single recovery authority, which prevents duplicate executions from an
    eager worker-side failure while the tool may still be running inside the
    transport.
    """

    def __init__(self, runtime, *, requested_by="execution_engine",
                 stall_recover_interval=1.0, lease_heartbeat_interval=1.0,
                 poll_interval=0.05, hard_stop_grace=120.0):
        self._runtime = runtime
        self._requested_by = requested_by
        self._stall_recover_interval = float(stall_recover_interval)
        self._lease_heartbeat_interval = float(lease_heartbeat_interval)
        self._poll_interval = float(poll_interval)
        self._hard_stop_grace = float(hard_stop_grace)

    @property
    def runtime(self):
        return self._runtime

    def invoke(self, *, execution_id, mission_id, task_id, attempt_no,
               tool_name, task_input, timeout_sec=None,
               cancel_check=None, engine_heartbeat=None,
               worker_candidate=None):
        """Run one EE execution through the runtime transport synchronously.

        Returns a tools.call_tool-shaped dict:
          {"ok": True, "result": {...}}                       on SUCCEEDED
          {"ok": False, "cancelled": True, "error": ...}      on CANCELLED
          {"ok": False, "timed_out": True, "error": ...}      on TIMED_OUT
          {"ok": False, "error": ...}                         on FAILED
          {"ok": False, "runtime_stalled": True, ...}         on transport stall
        """
        req = build_request(
            runtime=self._runtime,
            execution_id=execution_id,
            mission_id=mission_id,
            task_id=task_id,
            attempt_no=attempt_no,
            tool_name=tool_name,
            task_input=task_input,
            timeout_sec=timeout_sec,
            requested_by=self._requested_by,
            worker_candidate=worker_candidate,
        )
        try:
            handle = self._runtime.submit(req)
        except Exception as exc:
            return {"ok": False, "error": f"runtime submit rejected: {exc}"[:2000]}
        try:
            started = self._runtime.start(handle.handle_id)
        except Exception as exc:
            return {"ok": False, "error": f"runtime start raised: {exc}"[:2000]}
        if not isinstance(started, dict) or started.get("ok") is not True:
            err = str((started or {}).get("error") or "unknown")[:2000]
            return {"ok": False, "error": f"runtime rejected start: {err}"}
        try:
            terminal = self._poll_result(handle.handle_id,
                                         cancel_check=cancel_check,
                                         engine_heartbeat=engine_heartbeat,
                                         timeout_sec=timeout_sec)
        except Exception as exc:
            return {"ok": False, "error": f"runtime poll failed: {exc}"[:2000]}
        if terminal is None:
            return {"ok": False, "runtime_stalled": True,
                    "error": "runtime stalled (transport not finalizing)"}
        return map_result(terminal)

    def _poll_result(self, handle_id, *, cancel_check, engine_heartbeat,
                     timeout_sec):
        t0 = time.time()
        cancel_notified = False
        last_recover = t0
        last_hb = 0.0
        to = _timeout_value(timeout_sec)
        if to is not None:
            deadline = t0 + to + self._hard_stop_grace
        else:
            deadline = t0 + self._hard_stop_grace
        while True:
            rt = self._runtime.result(handle_id)
            if rt is not None:
                return rt
            now = time.time()
            if cancel_check is not None and cancel_check():
                if not cancel_notified:
                    cancel_notified = True
                    try:
                        self._runtime.cancel(handle_id)
                    except Exception:
                        pass   # cooperative; signal once, transport finalizes
            if engine_heartbeat is not None and \
                    now - last_hb >= self._lease_heartbeat_interval:
                last_hb = now
                try:
                    engine_heartbeat()
                except Exception:
                    pass
            if now - last_recover >= self._stall_recover_interval:
                last_recover = now
                try:
                    self._runtime.recover()
                except Exception:
                    pass
            if now >= deadline:
                return None
            time.sleep(max(0.01, self._poll_interval))