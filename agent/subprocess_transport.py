#!/usr/bin/env python3
"""Subprocess Transport (Phase 3.7) — process-isolated Hermes runtime transport.

ARCHITECTURAL RULES (HEER Phase 3.7):
-----------------------------------
1. Execution Engine remains sole authority over task state, retry, lease, governance, audit.
2. SubprocessTransport owns process isolation, process lifecycle, stdin/stdout JSONL IPC,
   worker identity/epoch verification at handshake, and transport outcome reporting.
3. Stdlib only. No third-party dependencies.
4. Absolute executable paths and strict environment allowlists (no shell execution).
5. Identity verification against WorkerRegistry before tool invocation. Fail closed.
"""
from __future__ import annotations

import json
import os
import select
import shutil
import subprocess
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set

from . import audit
from .runtime_contracts import (
    RuntimeCapabilities,
    RuntimeCapability,
    RuntimeError,
    RuntimeErrorType,
    RuntimeHandle,
    RuntimeIsolation,
    RuntimeJob,
    RuntimeRequest,
    RuntimeResult,
    RuntimeResultStatus,
    RuntimeTransportKind,
    _json_safe_copy,
)

__all__ = ["SubprocessTransport"]

_REDACTED_JSON = {"note": "[redacted]"}

def _safe_summary(value: Any) -> Dict[str, Any]:
    try:
        safe = _json_safe_copy(value, redact=True)
    except Exception:
        return dict(_REDACTED_JSON)
    if isinstance(safe, dict):
        return safe
    return {"_summary": json.dumps(safe, ensure_ascii=True, default=str)[:500]}

class SubprocessTransport:
    """Subprocess runtime transport implementation providing process isolation
    and JSONL stdin/stdout IPC.
    """

    def __init__(
        self,
        *,
        worker_registry: Optional[Any] = None,
        default_executable: Optional[str] = None,
        env_allowlist: Optional[List[str]] = None,
        cwd: Optional[str] = None,
        spawn_timeout: float = 5.0,
        handshake_timeout: float = 5.0,
        ipc_idle_timeout: float = 30.0,
        shutdown_grace: float = 2.0,
        terminate_timeout: float = 3.0,
        max_message_bytes: int = 1_048_576,
        event_sink: Optional[Callable[[Dict[str, Any]], None]] = None,
        governance_check: Optional[Callable[[RuntimeRequest], bool]] = None,
    ):
        self._registry = worker_registry
        self._default_executable = default_executable
        self._env_allowlist = list(env_allowlist) if env_allowlist is not None else ["PATH"]
        self._cwd = cwd or "/Users/delit/JARVIS/jarvis"
        self._spawn_timeout = float(spawn_timeout)
        self._handshake_timeout = float(handshake_timeout)
        self._ipc_idle_timeout = float(ipc_idle_timeout)
        self._shutdown_grace = float(shutdown_grace)
        self._terminate_timeout = float(terminate_timeout)
        self._max_message_bytes = int(max_message_bytes)
        self._event_sink = event_sink
        self._governance_check = governance_check

        self._transport_id = "sp_" + uuid.uuid4().hex[:12]
        self._capabilities = RuntimeCapabilities(
            transport=RuntimeTransportKind.SUBPROCESS,
            isolation=RuntimeIsolation.PROCESS,
            max_concurrency=16,
            supports_heartbeat=True,
            supports_hard_timeout=True,
            supports_secrets=False,
            supports_tenant_isolation=True,
            features=frozenset({
                RuntimeCapability.CANCELLATION,
                RuntimeCapability.HEARTBEAT,
                RuntimeCapability.TIMEOUT,
                RuntimeCapability.SANDBOXING,
            }),
        )

        self._lock = threading.RLock()
        self._jobs: Dict[str, Dict[str, Any]] = {}       # execution_id -> entry
        self._keys: Dict[str, str] = {}                 # idempotency_key -> execution_id
        self._handles: Dict[str, str] = {}              # handle_id -> execution_id
        self._events: List[Dict[str, Any]] = []
        self._closed = False

        self._monitor = threading.Thread(
            target=self._monitor_loop, daemon=True, name="heer-subprocess-monitor"
        )
        self._monitor.start()

    # ------------------------------------------------------------------
    # Capability reporting
    # ------------------------------------------------------------------

    def capabilities(self) -> RuntimeCapabilities:
        return self._capabilities

    # ------------------------------------------------------------------
    # Submission / Identity / Idempotency
    # ------------------------------------------------------------------

    def submit(self, request: RuntimeRequest) -> RuntimeHandle:
        if not isinstance(request, RuntimeRequest):
            raise ValueError("submit() requires a RuntimeRequest")
        if request.job.job_id != request.job.execution_id:
            raise ValueError("job_id must equal execution_id (canonical dedup identity)")

        key = request.idempotency_key
        with self._lock:
            if self._closed:
                raise ValueError("subprocess transport is closed")

            existing = self._keys.get(key)
            if existing is not None:
                if existing != request.job.execution_id:
                    raise ValueError(f"conflicting execution identity for idempotency key {key!r}")
                entry = self._jobs[existing]
                entry["submitted_count"] += 1
                self._emit("SUBPROCESS_DUPLICATE_SUBMIT", entry, {"key": key})
                return entry["handle"]

            exec_id = request.job.execution_id
            if exec_id in self._jobs:
                raise ValueError(f"execution already tracked: {exec_id}")

            handle = RuntimeHandle(
                handle_id="sp_hdl_" + uuid.uuid4().hex[:12],
                execution_id=exec_id,
                runtime_id=self._transport_id,
                submitted_at=time.time(),
                worker_id=request.job.metadata.get("worker_id"),
            )

        nonce = request.job.metadata.get("transport_nonce")
        entry = {
            "request": request,
            "handle": handle,
            "phase": "QUEUED",
            "final_status": None,
            "result": None,
            "proc": None,
            "pid": None,
            "thread": None,
            "cancel_event": threading.Event(),
            "submitted_count": 1,
            "nonce": nonce,
            "executable": request.job.metadata.get("executable") or self._default_executable,
            "started_at": None,
            "last_heartbeat": None,
        }
        self._jobs[exec_id] = entry
        self._keys[key] = exec_id
        self._handles[handle.handle_id] = exec_id
        self._emit("SUBPROCESS_SPAWN_REQUESTED", entry, {"idempotency_key": key})
        return handle

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, handle_id: str) -> Dict[str, Any]:
        with self._lock:
            entry = self._by_handle(handle_id)
            if entry is None:
                return {"ok": False, "error": f"unknown handle {handle_id!r}"}
            if entry["phase"] == "TERMINAL":
                return {
                    "ok": True,
                    "execution_id": entry["handle"].execution_id,
                    "phase": "TERMINAL",
                    "status": entry["final_status"].value,
                }
            if entry["phase"] == "RUNNING":
                return {
                    "ok": True,
                    "execution_id": entry["handle"].execution_id,
                    "phase": "RUNNING",
                }
            if self._closed:
                self._finalize(
                    entry,
                    RuntimeResultStatus.FAILED,
                    error=self._err(
                        entry, RuntimeErrorType.TRANSPORT, "transport closed before start"
                    ),
                )
                return {
                    "ok": True,
                    "execution_id": entry["handle"].execution_id,
                    "phase": "TERMINAL",
                    "status": entry["final_status"].value,
                }

            entry["phase"] = "RUNNING"
            worker_thread = threading.Thread(
                target=self._run_process,
                args=(entry["handle"].execution_id,),
                daemon=True,
                name=f"heer-sp-{entry['handle'].execution_id[:8]}",
            )
            entry["thread"] = worker_thread
            worker_thread.start()
            return {
                "ok": True,
                "execution_id": entry["handle"].execution_id,
                "phase": "RUNNING",
            }

    def cancel(self, handle_id: str) -> Dict[str, Any]:
        with self._lock:
            entry = self._by_handle(handle_id)
            if entry is None:
                return {"ok": False, "error": f"unknown handle {handle_id!r}"}
            if entry["phase"] == "TERMINAL":
                return {
                    "ok": True,
                    "execution_id": entry["handle"].execution_id,
                    "already_terminal": True,
                    "status": entry["final_status"].value,
                }
            entry["cancel_event"].set()
            self._emit("SUBPROCESS_CANCELLED", entry, {})

            if entry["phase"] == "QUEUED":
                self._finalize(
                    entry,
                    RuntimeResultStatus.CANCELLED,
                    error=self._err(entry, RuntimeErrorType.UNKNOWN, "cancelled before dispatch"),
                )
                return {"ok": True, "execution_id": entry["handle"].execution_id, "cooperative": True}

            proc = entry.get("proc")
            if proc is not None and proc.poll() is None:
                try:
                    self._send_ipc(proc, {"type": "CANCEL", "execution_id": entry["request"].job.execution_id})
                except Exception:
                    pass

            return {"ok": True, "execution_id": entry["handle"].execution_id, "cooperative": True}

    def terminate(self) -> Dict[str, Any]:
        with self._lock:
            if self._closed:
                return {"ok": True, "already_terminated": True}
            self._closed = True
            entries = list(self._jobs.values())

        for entry in entries:
            if entry["phase"] != "TERMINAL":
                entry["cancel_event"].set()
                proc = entry.get("proc")
                if proc is not None and proc.poll() is None:
                    try:
                        self._send_ipc(proc, {"type": "SHUTDOWN"})
                    except Exception:
                        pass
                    try:
                        proc.terminate()
                        proc.wait(timeout=self._terminate_timeout)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                self._finalize(
                    entry,
                    RuntimeResultStatus.CANCELLED,
                    error=self._err(entry, RuntimeErrorType.TRANSPORT, "transport terminated"),
                )
        return {"ok": True, "terminated": True}

    def heartbeat(self, handle_id: str) -> Dict[str, Any]:
        with self._lock:
            entry = self._by_handle(handle_id)
            if entry is None:
                return {"ok": False, "error": f"unknown handle {handle_id!r}"}
            proc = entry.get("proc")
            alive = (
                entry["phase"] == "RUNNING"
                and proc is not None
                and proc.poll() is None
            )
            return {
                "ok": True,
                "execution_id": entry["handle"].execution_id,
                "alive": alive,
                "phase": entry["phase"],
                "status": entry["final_status"].value if entry["final_status"] else None,
                "runtime_id": self._transport_id,
                "pid": entry.get("pid"),
            }

    def status(self, handle_id: str) -> Dict[str, Any]:
        with self._lock:
            entry = self._by_handle(handle_id)
            if entry is None:
                return {"ok": False, "error": f"unknown handle {handle_id!r}"}
            return {
                "ok": True,
                "execution_id": entry["handle"].execution_id,
                "handle": entry["handle"],
                "phase": entry["phase"],
                "status": entry["final_status"].value if entry["final_status"] else None,
                "submitted_at": entry["handle"].submitted_at,
                "duplicate_submissions": entry["submitted_count"],
            }

    def result(self, handle_id: str) -> Optional[RuntimeResult]:
        with self._lock:
            entry = self._by_handle(handle_id)
            if entry is None:
                return None
            return entry["result"]

    def events(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._events[-int(limit) :])

    def recover(self) -> Dict[str, Any]:
        with self._lock:
            checked = list(self._jobs.values())
            recovered = []
            for entry in checked:
                if entry["phase"] != "RUNNING":
                    continue
                proc = entry.get("proc")
                if proc is not None and proc.poll() is not None:
                    self._emit("SUBPROCESS_ORPHAN_REAPED", entry, {"pid": entry.get("pid")})
                    self._finalize(
                        entry,
                        RuntimeResultStatus.FAILED,
                        error=self._err(
                            entry,
                            RuntimeErrorType.CRASH,
                            f"subprocess exited unexpectedly with code {proc.returncode}",
                            retryable=True,
                        ),
                    )
                    recovered.append(entry["handle"].execution_id)
        return {"ok": True, "checked": len(checked), "recovered": recovered}

    # ------------------------------------------------------------------
    # Worker Identity / Epoch & Handshake Security
    # ------------------------------------------------------------------

    def _validate_executable(self, exec_path: Optional[str]) -> str:
        if not exec_path or not isinstance(exec_path, str):
            raise ValueError("Executable path must be a non-empty string")
        if not os.path.isabs(exec_path):
            resolved = shutil.which(exec_path)
            if not resolved or not os.path.isabs(resolved):
                raise ValueError(f"Executable path must be absolute or resolve to an absolute path: {exec_path!r}")
            exec_path = resolved
        if not os.path.exists(exec_path):
            raise ValueError(f"Executable does not exist: {exec_path!r}")
        if not os.access(exec_path, os.X_OK):
            raise ValueError(f"Executable is not executable: {exec_path!r}")
        return exec_path

    def _build_env(self) -> Dict[str, str]:
        env = {}
        for key in self._env_allowlist:
            if key in os.environ:
                env[key] = os.environ[key]
        return env

    def _validate_handshake_identity(
        self, entry: Dict[str, Any], hello_msg: Dict[str, Any]
    ) -> Optional[str]:
        job_meta = entry["request"].job.metadata
        expected_worker_id = job_meta.get("worker_id")
        expected_instance_id = job_meta.get("worker_instance_id")
        expected_epoch = job_meta.get("worker_epoch")
        expected_tenant_id = job_meta.get("tenant_id")
        expected_nonce = entry.get("nonce")

        hello_worker_id = hello_msg.get("worker_id")
        hello_instance_id = hello_msg.get("worker_instance_id")
        hello_epoch = hello_msg.get("worker_epoch")
        hello_tenant_id = hello_msg.get("tenant_id")
        hello_nonce = hello_msg.get("nonce")

        if expected_worker_id is not None and hello_worker_id != expected_worker_id:
            return f"worker_id mismatch: expected {expected_worker_id!r}, got {hello_worker_id!r}"

        if expected_instance_id is not None and hello_instance_id != expected_instance_id:
            return f"worker_instance_id mismatch: expected {expected_instance_id!r}, got {hello_instance_id!r}"

        if expected_epoch is not None and hello_epoch != expected_epoch:
            return f"worker_epoch mismatch: expected {expected_epoch!r}, got {hello_epoch!r}"

        if expected_tenant_id is not None and hello_tenant_id != expected_tenant_id:
            return f"tenant_id mismatch: expected {expected_tenant_id!r}, got {hello_tenant_id!r}"

        if expected_nonce is not None and hello_nonce != expected_nonce:
            return f"nonce mismatch: expected {expected_nonce!r}, got {hello_nonce!r}"

        if self._registry is not None and hello_worker_id:
            tenant_scope = expected_tenant_id or hello_tenant_id
            try:
                worker_info = self._registry.get(hello_worker_id, tenant_scope=tenant_scope)
            except TypeError:
                worker_info = self._registry.get(hello_worker_id)

            if worker_info is None:
                return f"worker {hello_worker_id!r} not found in registry"

            if isinstance(worker_info, dict):
                w_ident = worker_info.get("identity") or {}
                w_status = worker_info.get("state") or worker_info.get("status")
                w_instance = w_ident.get("worker_instance_id") or w_ident.get("instance_id")
                w_epoch = w_ident.get("worker_epoch") or w_ident.get("epoch")
                w_tenant = w_ident.get("tenant_id")
            else:
                w_status = getattr(worker_info, "status", None) or getattr(worker_info, "state", None)
                w_instance = getattr(worker_info, "worker_instance_id", None) or getattr(worker_info, "instance_id", None)
                w_epoch = getattr(worker_info, "worker_epoch", None) or getattr(worker_info, "epoch", None)
                w_tenant = getattr(worker_info, "tenant_id", None)

            if hasattr(w_status, "value"):
                w_status = w_status.value
            w_status_str = str(w_status).lower() if w_status else ""
            if w_status_str not in ("active", "healthy", "live"):
                return f"worker {hello_worker_id!r} registry status is {w_status!r} (must be active/healthy/live)"

            if w_instance is not None and hello_instance_id is not None and w_instance != hello_instance_id:
                return f"worker instance mismatch in registry: expected {w_instance!r}, got {hello_instance_id!r}"

            if w_epoch is not None and hello_epoch is not None and w_epoch != hello_epoch:
                return f"worker epoch mismatch in registry: expected {w_epoch!r}, got {hello_epoch!r}"

            if w_tenant is not None and hello_tenant_id is not None and w_tenant != hello_tenant_id:
                return f"worker tenant mismatch in registry: expected {w_tenant!r}, got {hello_tenant_id!r}"

        return None

    # ------------------------------------------------------------------
    # IPC Execution Loop
    # ------------------------------------------------------------------

    def _send_ipc(self, proc: subprocess.Popen, msg: Dict[str, Any]) -> None:
        data = json.dumps(msg, ensure_ascii=True).encode("utf-8") + b"\n"
        if len(data) > self._max_message_bytes:
            raise ValueError(f"Oversized message: {len(data)} bytes > limit {self._max_message_bytes}")
        proc.stdin.write(data)
        proc.stdin.flush()

    def _read_ipc_line(self, proc: subprocess.Popen, timeout: float) -> Optional[Dict[str, Any]]:
        t0 = time.time()
        while time.time() - t0 < timeout:
            if proc.poll() is not None:
                return None
            r, _, _ = select.select([proc.stdout], [], [], min(0.1, max(0.01, timeout - (time.time() - t0))))
            if r:
                line = proc.stdout.readline()
                if not line:
                    return None
                if len(line) > self._max_message_bytes:
                    raise ValueError(f"Oversized message received: {len(line)} bytes > limit {self._max_message_bytes}")
                try:
                    return json.loads(line.decode("utf-8"))
                except Exception as exc:
                    raise ValueError(f"Malformed JSON from worker: {exc}") from exc
        return None

    def _run_process(self, exec_id: str) -> None:
        entry = self._jobs.get(exec_id)
        if entry is None or entry["phase"] != "RUNNING":
            return

        req = entry["request"]
        job = req.job
        tool_name = str(job.metadata.get("tool", "") or "").strip()

        # 1. Executable validation
        try:
            exec_path = self._validate_executable(entry["executable"])
        except Exception as exc:
            self._finalize(
                entry,
                RuntimeResultStatus.FAILED,
                error=self._err(entry, RuntimeErrorType.TRANSPORT, f"Executable validation failed: {exc}"),
            )
            return

        # 2. Spawn subprocess
        env = self._build_env()
        args = [exec_path]
        extra_args = job.metadata.get("argv")
        if isinstance(extra_args, list):
            args.extend([str(a) for a in extra_args])

        try:
            proc = subprocess.Popen(
                args,
                shell=False,
                cwd=self._cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                text=False,
            )
        except Exception as exc:
            self._finalize(
                entry,
                RuntimeResultStatus.FAILED,
                error=self._err(entry, RuntimeErrorType.CRASH, f"Spawn failure: {exc}"),
            )
            return

        entry["proc"] = proc
        entry["pid"] = proc.pid
        entry["started_at"] = time.time()
        self._emit("SUBPROCESS_STARTED", entry, {"pid": proc.pid, "executable": exec_path})

        # 3. Governance check
        if self._governance_check is not None:
            try:
                approved = bool(self._governance_check(req))
            except Exception as exc:
                self._terminate_proc(proc)
                self._finalize(
                    entry,
                    RuntimeResultStatus.FAILED,
                    error=self._err(
                        entry, RuntimeErrorType.GOVERNANCE_DENIED, f"Governance check errored: {exc}"
                    ),
                )
                return
            if not approved:
                self._terminate_proc(proc)
                self._finalize(
                    entry,
                    RuntimeResultStatus.FAILED,
                    error=self._err(
                        entry, RuntimeErrorType.GOVERNANCE_DENIED, "Blocked by governance boundary"
                    ),
                )
                return

        # 4. Handshake (HELLO -> Validation -> READY)
        try:
            hello_msg = self._read_ipc_line(proc, timeout=self._handshake_timeout)
        except Exception as exc:
            self._terminate_proc(proc)
            self._emit("SUBPROCESS_PROTOCOL_ERROR", entry, {"error": str(exc)})
            self._finalize(
                entry,
                RuntimeResultStatus.FAILED,
                error=self._err(entry, RuntimeErrorType.TRANSPORT, f"Handshake failed: {exc}"),
            )
            return

        if hello_msg is None:
            code = proc.poll()
            self._terminate_proc(proc)
            if code is not None and code != 0:
                self._emit("SUBPROCESS_CRASHED", entry, {"returncode": code})
                self._finalize(
                    entry,
                    RuntimeResultStatus.FAILED,
                    error=self._err(entry, RuntimeErrorType.CRASH, f"Subprocess worker crashed with exit code {code}"),
                )
            else:
                self._emit("SUBPROCESS_HANDSHAKE_FAILED", entry, {"reason": "timeout or EOF"})
                self._finalize(
                    entry,
                    RuntimeResultStatus.FAILED,
                    error=self._err(entry, RuntimeErrorType.TIMEOUT, "Handshake timeout or worker EOF"),
                )
            return

        if hello_msg.get("type") != "HELLO":
            self._terminate_proc(proc)
            self._emit("SUBPROCESS_PROTOCOL_ERROR", entry, {"got": hello_msg.get("type")})
            self._finalize(
                entry,
                RuntimeResultStatus.FAILED,
                error=self._err(
                    entry, RuntimeErrorType.TRANSPORT, f"Protocol error: expected HELLO, got {hello_msg.get('type')!r}"
                ),
            )
            return

        # Validate Identity / Epoch / Tenant / Nonce before invoking tool
        rejection_reason = self._validate_handshake_identity(entry, hello_msg)
        if rejection_reason is not None:
            self._terminate_proc(proc)
            event_type = "SUBPROCESS_IDENTITY_REJECTED"
            if "epoch" in rejection_reason:
                event_type = "SUBPROCESS_EPOCH_REJECTED"
            self._emit(event_type, entry, {"reason": rejection_reason})
            self._finalize(
                entry,
                RuntimeResultStatus.FAILED,
                error=self._err(entry, RuntimeErrorType.AUTH_DENIED, f"Handshake identity rejected: {rejection_reason}"),
            )
            return

        # Handshake accepted -> Send READY & REQUEST
        try:
            self._send_ipc(proc, {"type": "READY", "execution_id": exec_id})
            self._send_ipc(
                proc,
                {
                    "type": "REQUEST",
                    "execution_id": exec_id,
                    "tool": tool_name,
                    "input": dict(job.input),
                    "metadata": dict(job.metadata),
                },
            )
        except Exception as exc:
            self._terminate_proc(proc)
            self._finalize(
                entry,
                RuntimeResultStatus.FAILED,
                error=self._err(entry, RuntimeErrorType.TRANSPORT, f"IPC send request failed: {exc}"),
            )
            return

        # 5. Read loop for RESPONSE / HEARTBEAT / ERROR
        t0 = time.time()
        timeout_sec = job.timeout_sec or self._ipc_idle_timeout

        while True:
            if entry["cancel_event"].is_set():
                try:
                    self._send_ipc(proc, {"type": "CANCEL", "execution_id": exec_id})
                except Exception:
                    pass
                self._terminate_proc(proc)
                self._finalize(
                    entry,
                    RuntimeResultStatus.CANCELLED,
                    error=self._err(entry, RuntimeErrorType.UNKNOWN, "cancelled during worker execution"),
                )
                return

            if time.time() - t0 > timeout_sec:
                self._terminate_proc(proc)
                self._emit("SUBPROCESS_TIMEOUT", entry, {"timeout_sec": timeout_sec})
                self._finalize(
                    entry,
                    RuntimeResultStatus.TIMED_OUT,
                    error=self._err(
                        entry, RuntimeErrorType.TIMEOUT, f"Subprocess tool execution timed out ({timeout_sec}s)"
                    ),
                )
                return

            try:
                msg = self._read_ipc_line(proc, timeout=0.2)
            except ValueError as exc:
                err_msg = str(exc)
                err_type = RuntimeErrorType.INVALID_RESULT if "Oversized message" in err_msg else RuntimeErrorType.TRANSPORT
                self._terminate_proc(proc)
                self._emit("SUBPROCESS_PROTOCOL_ERROR", entry, {"error": err_msg})
                self._finalize(
                    entry,
                    RuntimeResultStatus.FAILED,
                    error=self._err(entry, err_type, f"Protocol error from worker: {err_msg}"),
                )
                return
            except Exception as exc:
                self._terminate_proc(proc)
                self._emit("SUBPROCESS_PROTOCOL_ERROR", entry, {"error": str(exc)})
                self._finalize(
                    entry,
                    RuntimeResultStatus.FAILED,
                    error=self._err(entry, RuntimeErrorType.INVALID_RESULT, f"Protocol error from worker: {exc}"),
                )
                return

            if msg is None:
                if proc.poll() is not None:
                    code = proc.returncode
                    self._emit("SUBPROCESS_EXITED", entry, {"exit_code": code})
                    if code != 0:
                        self._finalize(
                            entry,
                            RuntimeResultStatus.FAILED,
                            error=self._err(
                                entry, RuntimeErrorType.CRASH, f"Worker process exited with code {code}"
                            ),
                        )
                    else:
                        self._finalize(
                            entry,
                            RuntimeResultStatus.FAILED,
                            error=self._err(
                                entry, RuntimeErrorType.TRANSPORT, "Worker process closed stream before response"
                            ),
                        )
                    return
                continue

            msg_type = msg.get("type")
            if msg_type == "HEARTBEAT":
                entry["last_heartbeat"] = time.time()
                t0 = time.time()  # refresh idle timer
                continue

            if msg_type == "RESPONSE":
                lat_ms = int((time.time() - entry["started_at"]) * 1000)
                ok = msg.get("ok", True)
                if ok:
                    res_val = msg.get("result")
                    output = res_val if isinstance(res_val, dict) else {"result": res_val}
                    self._send_ipc(proc, {"type": "SHUTDOWN"})
                    self._wait_proc(proc)
                    self._finalize(
                        entry,
                        RuntimeResultStatus.SUCCEEDED,
                        output=output,
                        metadata={"lat_ms": lat_ms},
                        tool_name=tool_name,
                    )
                else:
                    err_msg = str(msg.get("error") or "Worker reported failure")
                    self._send_ipc(proc, {"type": "SHUTDOWN"})
                    self._wait_proc(proc)
                    self._finalize(
                        entry,
                        RuntimeResultStatus.FAILED,
                        error=self._err(entry, RuntimeErrorType.UNKNOWN, err_msg, retryable=True),
                        tool_name=tool_name,
                    )
                return

            if msg_type == "ERROR":
                err_msg = str(msg.get("error") or "Worker protocol error")
                self._terminate_proc(proc)
                self._finalize(
                    entry,
                    RuntimeResultStatus.FAILED,
                    error=self._err(entry, RuntimeErrorType.UNKNOWN, err_msg, retryable=True),
                    tool_name=tool_name,
                )
                return

            self._terminate_proc(proc)
            self._emit("SUBPROCESS_PROTOCOL_ERROR", entry, {"unsupported_type": msg_type})
            self._finalize(
                entry,
                RuntimeResultStatus.FAILED,
                error=self._err(entry, RuntimeErrorType.TRANSPORT, f"Unsupported IPC message type: {msg_type!r}"),
            )
            return

    def _terminate_proc(self, proc: subprocess.Popen) -> None:
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=self._terminate_timeout)
            except Exception:
                try:
                    proc.kill()
                    proc.wait(timeout=1.0)
                except Exception:
                    pass

    def _wait_proc(self, proc: subprocess.Popen) -> None:
        if proc.poll() is None:
            try:
                proc.wait(timeout=self._shutdown_grace)
            except Exception:
                self._terminate_proc(proc)

    # ------------------------------------------------------------------
    # Internal Helpers & Eventing
    # ------------------------------------------------------------------

    def _by_handle(self, handle_id: str) -> Optional[Dict[str, Any]]:
        exec_id = self._handles.get(handle_id)
        if exec_id is None:
            return None
        return self._jobs.get(exec_id)

    @staticmethod
    def _err(
        entry: Dict[str, Any],
        error_type: RuntimeErrorType,
        message: str,
        *,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ) -> RuntimeError:
        req = entry["request"]
        safe = _safe_summary(details) if details is not None else None
        return RuntimeError(
            error_type=error_type,
            message=str(message)[:500],
            retryable=retryable,
            execution_id=req.job.execution_id,
            job_id=req.job.job_id,
            runtime_id=entry["handle"].runtime_id,
            correlation_id=req.job.correlation_id,
            details=safe,
        )

    def _emit(self, event_type: str, entry: Dict[str, Any], detail: Dict[str, Any]) -> None:
        req = entry["request"]
        ev = {
            "ts": time.time(),
            "runtime_id": self._transport_id,
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

    def _audit(
        self, intent: str, entry: Dict[str, Any], success: bool, detail: str = "", tool: Optional[str] = None
    ) -> None:
        req = entry["request"]
        corr = {
            "mission_id": req.job.mission_id,
            "task_id": req.job.task_id,
            "execution_id": req.job.execution_id,
            "attempt_no": req.job.attempt_no,
            "correlation_id": req.job.correlation_id,
        }
        try:
            audit.record(
                request=f"{intent} mission={req.job.mission_id} "
                f"task={req.job.task_id} execution={req.job.execution_id} "
                f"attempt={req.job.attempt_no} {str(detail)[:200]}",
                intent=intent,
                agent_id="subprocess_transport",
                tools=[tool or intent],
                inputs={k: v for k, v in corr.items()},
                outputs={"success": bool(success), "runtime_id": self._transport_id},
                approval={"blocked": False},
                success=bool(success),
                lat_ms=0,
            )
        except Exception:
            pass

    def _finalize(
        self,
        entry: Dict[str, Any],
        status: RuntimeResultStatus,
        *,
        error: Optional[RuntimeError] = None,
        output: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tool_name: Optional[str] = None,
    ) -> bool:
        with self._lock:
            if entry["phase"] == "TERMINAL":
                return False
            req = entry["request"]
            now = time.time()
            result = RuntimeResult(
                execution_id=req.job.execution_id,
                job_id=req.job.job_id,
                status=status,
                output=_safe_summary(output) if output is not None else None,
                error=error,
                started_at=entry.get("started_at"),
                finished_at=now,
                runtime_id=self._transport_id,
                worker_id=req.job.metadata.get("worker_id"),
                correlation_id=req.job.correlation_id,
                metadata=_safe_summary(metadata or {}),
            )
            entry["result"] = result
            entry["final_status"] = status
            entry["phase"] = "TERMINAL"
            self._emit(f"SUBPROCESS_{status.value}", entry, {})
            self._audit(
                f"subprocess_{status.value.lower()}",
                entry,
                status == RuntimeResultStatus.SUCCEEDED,
                detail=str(error.message if error else "")[:200],
                tool=tool_name,
            )
            return True

    def _monitor_loop(self) -> None:
        while True:
            with self._lock:
                if self._closed:
                    break
                now = time.time()
                for entry in list(self._jobs.values()):
                    if entry["phase"] != "RUNNING":
                        continue
                    to = entry["request"].job.timeout_sec or self._ipc_idle_timeout
                    st = entry.get("started_at")
                    if st is not None and now - st > to + self._shutdown_grace + self._terminate_timeout + 2.0:
                        proc = entry.get("proc")
                        if proc is not None and proc.poll() is None:
                            self._terminate_proc(proc)
                            self._finalize(
                                entry,
                                RuntimeResultStatus.TIMED_OUT,
                                error=self._err(
                                    entry, RuntimeErrorType.TIMEOUT, f"Process execution timed out ({to}s)"
                                ),
                            )
            time.sleep(0.05)