"""Parallel Execution Engine (Phase 3.3) on top of frozen 3.1/3.2 modules."""
import json, os, random, sqlite3, threading, time, uuid
from concurrent.futures import ThreadPoolExecutor
from . import audit, data, mission_engine, task_graph, tools

CLAIMED, IN_PROGRESS, COMPLETED = "CLAIMED", "IN_PROGRESS", "COMPLETED"
FAILED, RETRY_SCHEDULED = "FAILED", "RETRY_SCHEDULED"
LEASE_EXPIRED, RECLAIMED, ABANDONED = "LEASE_EXPIRED", "RECLAIMED", "ABANDONED"
LIVE = (CLAIMED, IN_PROGRESS)
ALL = (CLAIMED, IN_PROGRESS, COMPLETED, FAILED, RETRY_SCHEDULED, LEASE_EXPIRED, RECLAIMED, ABANDONED)
MAX_C, PER_M, TTL, BB, BC, POLL, DTMO, MTMO, MAXERR = 8, 0, 300.0, 1.0, 60.0, 0.5, 0, 0, 2000

def _state_dir():
    root = data.data_root() or os.path.abspath(".")
    d = os.path.join(os.path.abspath(os.path.join(root, "..")), ".heer")
    os.makedirs(d, exist_ok=True)
    return d

def _conn():
    c = sqlite3.connect(os.path.join(_state_dir(), "execution_engine.sqlite3"), timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA busy_timeout=30000")
    c.execute("""CREATE TABLE IF NOT EXISTS executions (
        execution_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, mission_id TEXT NOT NULL,
        attempt_no INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL,
        lease_owner TEXT NOT NULL, lease_expires_at REAL NOT NULL,
        input_snapshot TEXT, output TEXT, error TEXT, timeout_sec REAL,
        max_attempts INTEGER NOT NULL DEFAULT 1, idempotent INTEGER NOT NULL DEFAULT 0,
        cancel_requested INTEGER NOT NULL DEFAULT 0,
        created_at REAL NOT NULL, updated_at REAL NOT NULL,
        started_at REAL, finished_at REAL)""")
    for idx in ("ix_exec_task ON executions(task_id)", "ix_exec_mission ON executions(mission_id,status)",
                "ix_exec_lease ON executions(lease_expires_at,status)"):
        c.execute(f"CREATE INDEX IF NOT EXISTS {idx}")
    c.execute("""CREATE TABLE IF NOT EXISTS execution_events (
        event_id TEXT PRIMARY KEY, execution_id TEXT NOT NULL, task_id TEXT NOT NULL,
        mission_id TEXT NOT NULL, event_type TEXT NOT NULL, payload TEXT, ts REAL NOT NULL)""")
    c.execute("CREATE INDEX IF NOT EXISTS ix_events_mission ON execution_events(mission_id,ts)")
    c.execute("CREATE TABLE IF NOT EXISTS scheduler_config (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    return c

_LOCK, _LIMITS, _STARTS = threading.RLock(), {}, {}
_RUNTIME, _RUNTIME_LOCK = None, threading.Lock()
_REGISTRY, _REGISTRY_LOCK = None, threading.Lock()

def _cfg(k, d=None):
    try:
        c = _conn()
        try:
            r = c.execute("SELECT value FROM scheduler_config WHERE key=?", (k,)).fetchone()
        finally:
            c.close()
        if r is None: return d
        raw = r["value"]
        if isinstance(d, bool): return str(raw).strip().lower() in ("1", "true", "yes")
        if isinstance(d, int):
            try: return int(raw)
            except (TypeError, ValueError): return d
        if isinstance(d, float):
            try: return float(raw)
            except (TypeError, ValueError): return d
        return raw
    except Exception:
        return d

def _fcfg(k, d=0.0):
    v = _cfg(k, None)   # raw string, not type-dispatched
    if v is None:
        return d
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(d)

def _icfg(k, d=0):
    v = _cfg(k, None)   # raw string, not type-dispatched
    if v is None:
        return d
    try:
        return int(v)
    except (TypeError, ValueError):
        return int(d)

def configure(**kw):
    with _LOCK:
        c = _conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            for k, v in kw.items():
                c.execute("INSERT INTO scheduler_config(key,value) VALUES(?,?) "
                          "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                          (k, "1" if v is True else "0" if v is False else str(v)))
            c.commit()
        finally:
            c.close()
    return {"ok": True, "config": {k: str(v) for k, v in kw.items()}}

def _rcfg():
    return {"max_concurrent": _cfg("max_concurrent", MAX_C), "per_mission": _cfg("per_mission", PER_M),
            "lease_ttl": _cfg("lease_ttl", TTL), "backoff_base": _cfg("backoff_base", BB),
            "backoff_cap": _cfg("backoff_cap", BC), "poll": _cfg("poll", POLL),
            "task_timeout": _cfg("task_timeout", DTMO), "mission_timeout": _cfg("mission_timeout", MTMO)}

def _audit(intent, mission_id, success, execution_id=None, task_id=None, detail=""):
    try:
        audit.record(request=f"{intent} mission={mission_id} task={task_id or ''} execution={execution_id or ''} {detail[:200]}",
                     intent=intent, agent_id="execution_engine", tools=[intent],
                     inputs={"mission_id": mission_id, "task_id": task_id, "execution_id": execution_id, "detail": detail[:500]},
                     outputs={"success": success}, approval={"blocked": False}, success=success, lat_ms=0)
    except Exception:
        pass

def _ev(execution_id, task_id, mission_id, etype, payload=None):
    try:
        c = _conn()
        try:
            c.execute("INSERT INTO execution_events VALUES (?,?,?,?,?,?,?)",
                      ("evt_" + uuid.uuid4().hex[:12], execution_id, task_id, mission_id, etype,
                       json.dumps(payload, default=str) if payload is not None else None, time.time()))
            c.commit()
        finally:
            c.close()
    except Exception:
        pass

def _now():
    return time.time()

def _loads(raw, fb=None):
    try: return json.loads(raw or "")
    except Exception: return fb

def _dumps(v):
    try: return json.dumps(v, default=str) if v is not None else None
    except Exception: return None

def _row(eid):
    c = _conn()
    try:
        r = c.execute("SELECT * FROM executions WHERE execution_id=?", (eid,)).fetchone()
    finally:
        c.close()
    if r is None: return None
    d = dict(r)
    d["idempotent"] = bool(d["idempotent"]); d["cancel_requested"] = bool(d["cancel_requested"])
    d["input_snapshot"] = _loads(d["input_snapshot"]); d["output"] = _loads(d["output"])
    return d

def _policy(task):
    meta = task.get("metadata") or {}
    if not isinstance(meta, dict): meta = {}
    idem = bool(meta.get("idempotent"))
    r = meta.get("retry", 1)
    if isinstance(r, dict):
        try: ma = max(1, int(r.get("max_attempts", 1)))
        except Exception: ma = 1
    elif isinstance(r, bool): ma = 3 if (r and idem) else 1
    else:
        try: ma = max(1, int(r))
        except Exception: ma = 1
    if ma > 1 and not idem: ma = 1
    to = None
    try:
        t = meta.get("timeout_sec")
        if t is not None: to = float(t)
    except Exception: to = None
    if to is None:
        d = _fcfg("task_timeout", DTMO)
        to = d or None
    return ma, idem, to

def _backoff(n):
    raw = min(_fcfg("backoff_base", BB) * (2 ** max(0, n - 1)), _fcfg("backoff_cap", BC))
    return max(0.0, raw * (1.0 + random.uniform(-0.2, 0.2)))

def _gw(eid, cur, tgt, fields=None):
    fields = fields or {}
    sets, vals = ["status=?"], [tgt]
    for k, v in fields.items():
        sets.append(f"{k}=?"); vals.append(v)
    vals += [_now(), eid, cur]
    with _LOCK:
        c = _conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT 1 FROM executions WHERE execution_id=?", (eid,)).fetchone() is None:
                c.rollback(); return False
            c.execute(f"UPDATE executions SET {', '.join(sets)}, updated_at=? "
                      "WHERE execution_id=? AND status=?", vals)
            changed = c.total_changes; c.commit()
        finally:
            c.close()
    return changed > 0

def _mark_abandoned(eid, reason):
    with _LOCK:
        c = _conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            r = c.execute("SELECT task_id, mission_id FROM executions WHERE execution_id=?", (eid,)).fetchone()
            c.execute("UPDATE executions SET status=?, error=?, updated_at=?, finished_at=? WHERE execution_id=?",
                      (ABANDONED, (reason or "")[:MAXERR], _now(), _now(), eid))
            c.commit()
        finally:
            c.close()
    if r is not None: _ev(eid, r["task_id"], r["mission_id"], "ABANDONED", {"reason": reason})

def _cancel_req(eid):
    c = _conn()
    try:
        r = c.execute("SELECT cancel_requested FROM executions WHERE execution_id=?", (eid,)).fetchone()
    finally:
        c.close()
    return bool(r and r["cancel_requested"])

def _set_cancel(eid):
    with _LOCK:
        c = _conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute("UPDATE executions SET cancel_requested=1, updated_at=? WHERE execution_id=?", (_now(), eid))
            c.commit()
        finally:
            c.close()

def _live_for_task(task_id):
    c = _conn()
    try:
        r = c.execute("SELECT execution_id FROM executions WHERE task_id=? AND status IN ('CLAIMED','IN_PROGRESS') "
                      "ORDER BY attempt_no DESC LIMIT 1", (task_id,)).fetchone()
    finally:
        c.close()
    return r["execution_id"] if r else None

def heartbeat(eid, ttl=None):
    raw = ttl if ttl is not None else _cfg("lease_ttl", TTL)
    ttl = float(raw) if raw is not None else float(TTL)
    with _LOCK:
        c = _conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute("UPDATE executions SET lease_expires_at=?, updated_at=? "
                      "WHERE execution_id=? AND status IN ('CLAIMED','IN_PROGRESS')", (_now() + ttl, _now(), eid))
            c.commit()
        finally:
            c.close()
    return True

def _current_runtime():
    with _RUNTIME_LOCK:
        return _RUNTIME

def install_runtime(runtime, **adapter_kw):
    """Install a Hermes-compatible runtime transport for task execution.

    With a runtime installed, _worker dispatches through agent.hermes_adapter
    (submit -> start -> poll terminal result -> map back). Passing None -- or
    calling uninstall_runtime() -- restores the legacy in-process
    tools.call_tool path byte-for-byte, so Phase 3.1/3.2/3.3 semantics are
    unchanged.
    """
    global _RUNTIME
    with _RUNTIME_LOCK:
        if runtime is None:
            _RUNTIME = None
            _audit("hermes_runtime_uninstall", "", True)
            return {"ok": True, "installed": False}
        if not callable(getattr(runtime, "submit", None)) or not callable(getattr(runtime, "result", None)):
            return {"ok": False, "error": "runtime must expose submit() and result()"}
        from .hermes_adapter import RuntimeAdapter
        _RUNTIME = RuntimeAdapter(runtime, **adapter_kw)
        _audit("hermes_runtime_install", "", True)
        return {"ok": True, "installed": True}

def uninstall_runtime():
    return install_runtime(None)

def runtime_status():
    """Observability: whether a runtime is installed and its identity."""
    with _RUNTIME_LOCK:
        rt = _RUNTIME
    r = getattr(rt, "runtime", None) if rt is not None else None
    return {"ok": True, "installed": rt is not None,
            "runtime_id": getattr(r, "_runtime_id", None) if r is not None else None}

def install_registry(registry):
    global _REGISTRY
    with _REGISTRY_LOCK:
        _REGISTRY = registry
        return {"ok": True, "installed": registry is not None}

def _claim(task_id, mission_id):
    task = task_graph.get_task(mission_id, task_id)
    if task is None or task["status"] != task_graph.TASK_READY: return None
    ma, idem, to = _policy(task)
    ttl = _fcfg("lease_ttl", TTL); now = _now()
    eid = "exe_" + uuid.uuid4().hex[:12]
    with _LOCK:
        c = _conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT COUNT(*) n FROM executions WHERE task_id=? AND status IN ('CLAIMED','IN_PROGRESS')",
                         (task_id,)).fetchone()["n"]:
                c.rollback(); return None
            c.execute("INSERT INTO executions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (eid, task_id, mission_id, 1, CLAIMED, f"w-{uuid.uuid4().hex[:6]}", now + ttl,
                       _dumps(task.get("input")), None, None, to, ma, 1 if idem else 0, 0, now, now, None, None))
            c.commit()
        finally:
            c.close()
    r = task_graph.transition_task(mission_id, task_id, task_graph.TASK_RUNNING)
    if not r["ok"]:
        _mark_abandoned(eid, "lost claim: " + str(r.get("error", ""))[:200]); return None
    _ev(eid, task_id, mission_id, "CLAIMED", {"attempt": 1})
    return eid

def _claim_retry(eid):
    e = _row(eid)
    if e is None or e["status"] != RETRY_SCHEDULED: return None
    task = task_graph.get_task(e["mission_id"], e["task_id"])
    if task is None or task["status"] != task_graph.TASK_RUNNING:
        _mark_abandoned(eid, "task no longer RUNNING for retry"); return None
    ttl = _fcfg("lease_ttl", TTL)
    with _LOCK:
        c = _conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT 1 FROM executions WHERE execution_id=? AND status=?",
                         (eid, RETRY_SCHEDULED)).fetchone() is None:
                c.rollback(); return None
            c.execute("UPDATE executions SET status=?, lease_expires_at=?, updated_at=? WHERE execution_id=?",
                      (CLAIMED, _now() + ttl, _now(), eid))
            c.commit()
        finally:
            c.close()
    _ev(eid, e["task_id"], e["mission_id"], "CLAIMED", {"attempt": e["attempt_no"], "retry": True})
    return eid

def _schedule_retry(e, error, force=False):
    """Create a RETRY_SCHEDULED execution row for the next attempt.

    force=True is used by the lease sweep and the timeout sweep after they
    have already marked the row terminal (LEASE_EXPIRED / FAILED), so the
    IN_PROGRESS transition is intentionally a no-op there. Without force, the
    transition from IN_PROGRESS is CAS-guarded so a concurrent authority (e.g.
    the worker itself, or a sweep that finalized the row first) cannot trigger
    a duplicate retry row when the execution was already finalized.
    """
    task = task_graph.get_task(e["mission_id"], e["task_id"])
    if task is None or task["status"] != task_graph.TASK_RUNNING: return False
    delay = _backoff(e["attempt_no"]); now = _now()
    new_id = "exe_" + uuid.uuid4().hex[:12]
    with _LOCK:
        c = _conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            cur = c.execute("UPDATE executions SET status=?, error=?, finished_at=?, updated_at=? "
                            "WHERE execution_id=? AND status='IN_PROGRESS'",
                            (FAILED, (error or "tool failed")[:MAXERR], now, now, e["execution_id"]))
            if cur.rowcount == 0 and not force:
                c.rollback()
                _ev(e["execution_id"], e["task_id"], e["mission_id"], "RETRY_ABORTED",
                    {"reason": "execution already finalized by another authority",
                     "error": (error or "")[:200]})
                return False
            c.execute("INSERT INTO executions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (new_id, e["task_id"], e["mission_id"], e["attempt_no"] + 1, RETRY_SCHEDULED,
                       e["lease_owner"], now + delay, _dumps(e["input_snapshot"]), None, None,
                       e["timeout_sec"], e["max_attempts"], 1 if e["idempotent"] else 0,
                       1 if e["cancel_requested"] else 0, now, now, None, None))
            c.commit()
        finally:
            c.close()
    _ev(e["execution_id"], e["task_id"], e["mission_id"], "FAILED", {"error": (error or "")[:500], "retry": True})
    _ev(new_id, e["task_id"], e["mission_id"], "RETRY_SCHEDULED",
        {"attempt": e["attempt_no"] + 1, "delay_sec": round(delay, 3)})
    _audit("task_execution_retry", e["mission_id"], True, execution_id=e["execution_id"], task_id=e["task_id"])
    return True

def _fail_permanent(e, error):
    if not _gw(e["execution_id"], IN_PROGRESS, FAILED, {"error": error, "finished_at": _now()}):
        _ev(e["execution_id"], e["task_id"], e["mission_id"], "DUPLICATE_WRITE_REJECTED", {}); return
    _ev(e["execution_id"], e["task_id"], e["mission_id"], "FAILED", {"permanent": True, "error": error[:500]})
    _audit("task_execution_fail", e["mission_id"], False, execution_id=e["execution_id"], task_id=e["task_id"])
    r = task_graph.transition_task(e["mission_id"], e["task_id"], task_graph.TASK_FAILED, error=error)
    if r["ok"]: task_graph._refresh_readiness(e["mission_id"])

def _handle_failure(eid, error):
    e = _row(eid)
    if e is None: return
    error = (error or "tool failed")[:MAXERR]
    if error.startswith("PERMANENT:") or not e["idempotent"] or e["attempt_no"] >= e["max_attempts"]:
        _fail_permanent(e, error)
    else:
        _schedule_retry(e, error)

_EXEC, _EXEC_LOCK = None, threading.Lock()

def _executor():
    global _EXEC
    n = max(1, _icfg("max_concurrent", MAX_C))
    with _EXEC_LOCK:
        if _EXEC is None:
            _EXEC = ThreadPoolExecutor(max_workers=n, thread_name_prefix="heer-exec")
    return _EXEC

def _dispatch(eid):
    try:
        _executor().submit(_worker, eid)
    except RuntimeError:
        _mark_abandoned(eid, "executor shut down")

def _finish_cancelled(e, reason):
    if not _gw(e["execution_id"], IN_PROGRESS, FAILED, {"error": "cancelled", "finished_at": _now()}):
        _ev(e["execution_id"], e["task_id"], e["mission_id"], "DUPLICATE_WRITE_REJECTED", {}); return
    _ev(e["execution_id"], e["task_id"], e["mission_id"], "CANCELLED", {"reason": reason})
    _audit("task_execution_cancel", e["mission_id"], False, execution_id=e["execution_id"], task_id=e["task_id"])
    r = task_graph.transition_task(e["mission_id"], e["task_id"], task_graph.TASK_CANCELLED, error="cancelled")
    if r["ok"]: task_graph._refresh_readiness(e["mission_id"])

def _invoke_tool(eid, mid, tid, e, tool_name, task_input, biz, worker_candidate=None):
    """Execute one tool invocation.

    With no runtime installed this is EXACTLY the legacy in-process path
    (tools.call_tool). With a Hermes-compatible runtime installed the request
    is submitted through the transport seam; the adapter polls the terminal
    RuntimeResult, renews the EE lease while running, propagates cooperative
    cancellation, and maps the result back to the tools.call_tool shape. A
    transport stall returns None and the caller exits WITHOUT touching EE
    state -- the lease sweep remains the single recovery authority.
    """
    rt = _current_runtime()
    if rt is None:
        return tools.call_tool(tool_name, task_input, business_id=biz)
    result = rt.invoke(
        execution_id=eid, mission_id=mid, task_id=tid, attempt_no=e["attempt_no"],
        tool_name=tool_name, task_input=task_input, timeout_sec=e["timeout_sec"],
        cancel_check=lambda: _cancel_req(eid),
        engine_heartbeat=lambda: heartbeat(eid),
        worker_candidate=worker_candidate,
    )
    if result.get("runtime_stalled"):
        _ev(eid, tid, mid, "RUNTIME_STALLED", {"error": (result.get("error") or "")[:500]})
        return None
    return dict(result)

def _worker(eid):
    e = _row(eid)
    if e is None: return
    tid, mid = e["task_id"], e["mission_id"]
    try:
        if not _gw(eid, CLAIMED, IN_PROGRESS, {"started_at": _now()}):
            _ev(eid, tid, mid, "DUPLICATE_WRITE_REJECTED", {"error": "not CLAIMED"}); return
        task = task_graph.get_task(mid, tid)
        if task is None or task["status"] != task_graph.TASK_RUNNING:
            _mark_abandoned(eid, "task not RUNNING at worker start"); return
        meta = task.get("metadata") or {}
        if not isinstance(meta, dict): meta = {}
        tool_name = str(meta.get("tool", "") or "").strip()
        if not tool_name:
            _handle_failure(eid, "PERMANENT: task has no metadata['tool'] to invoke")
            return
        _ev(eid, tid, mid, "STARTED", {"attempt": e["attempt_no"], "tool": tool_name})
        _audit("task_execution_start", mid, True, execution_id=eid, task_id=tid)
        biz = (task.get("input") or {}).get("_business_id")

        worker_candidate = None
        global _REGISTRY
        if _REGISTRY is not None:
            task_input = task.get("input") or {}
            tenant_id = None
            if isinstance(task_input, dict):
                tenant_id = task_input.get("_tenant_id") or task_input.get("_business_id")
            
            required_tool_classes = ()
            if tool_name:
                required_tool_classes = (tool_name,)
                
            required_isolation = None
            iso_val = meta.get("isolation")
            if iso_val:
                from .runtime_contracts import RuntimeIsolation
                try:
                    required_isolation = RuntimeIsolation(iso_val)
                except ValueError:
                    pass
                
            required_runtime_features = ()
            feats = meta.get("features")
            if feats:
                if isinstance(feats, str):
                    required_runtime_features = (feats,)
                elif isinstance(feats, (list, tuple, set)):
                    required_runtime_features = tuple(feats)
                
            required_architecture = meta.get("architecture")
            
            from .dispatch_contracts import DispatchConstraints
            constraints = DispatchConstraints(
                tenant_scope=tenant_id,
                require_live=True,
                required_isolation=required_isolation,
                required_tool_classes=required_tool_classes,
                required_runtime_features=required_runtime_features,
                required_architecture=required_architecture
            )
            
            from .worker_matcher import WorkerMatcher
            from .dispatch_contracts import DispatchReason
            matcher = WorkerMatcher(_REGISTRY)
            decision, cmatch = matcher.evaluate(constraints, execution_id=eid, decided_at=_now())
            if decision.reason == DispatchReason.SELECTED:
                worker_candidate = decision.candidate
                _ev(eid, tid, mid, "DISPATCH_SELECTED", {
                    "worker_id": worker_candidate.identity.worker_id,
                    "worker_instance_id": worker_candidate.identity.worker_instance_id,
                    "worker_epoch": worker_candidate.identity.worker_epoch
                })
            elif decision.reason == DispatchReason.NO_ELIGIBLE:
                _ev(eid, tid, mid, "DISPATCH_NO_ELIGIBLE", {"reason": "NO_ELIGIBLE"})
                _handle_failure(eid, "NO_ELIGIBLE_WORKER")
                return
            elif decision.reason == DispatchReason.TENANT_REJECTED:
                _ev(eid, tid, mid, "DISPATCH_TENANT_REJECTED", {"reason": "TENANT_REJECTED"})
                _handle_failure(eid, "NO_ELIGIBLE_WORKER")
                return

        t0 = _now()
        if _cancel_req(eid):
            _finish_cancelled(e, "cancelled before tool invocation"); return
        result = _invoke_tool(eid, mid, tid, e, tool_name, task.get("input") or {}, biz, worker_candidate)
        if result is None:
            return   # RUNTIME_STALLED: EE lease sweep remains recovery authority
        lat = int((_now() - t0) * 1000)
        if _cancel_req(eid):
            _finish_cancelled(e, "cancelled after tool returned"); return
        if result.get("cancelled"):
            _finish_cancelled(e, "cancelled by runtime transport"); return
        _ev(eid, tid, mid, "TOOL_OUTPUT", {"lat_ms": lat, "ok": result.get("ok") is True})
        if result.get("ok") is True:
            if not _gw(eid, IN_PROGRESS, COMPLETED, {"output": _dumps(result), "error": None, "finished_at": _now()}):
                _ev(eid, tid, mid, "DUPLICATE_WRITE_REJECTED", {"error": "stale COMPLETED"}); return
            r = task_graph.transition_task(mid, tid, task_graph.TASK_COMPLETED, output=result)
            if not r["ok"]:
                _ev(eid, tid, mid, "TRANSITION_REJECTED", {"target": "COMPLETED"})
            _ev(eid, tid, mid, "COMPLETED", {"lat_ms": lat, "attempt": e["attempt_no"]})
            _audit("task_execution_end", mid, True, execution_id=eid, task_id=tid, detail=f"lat_ms={lat}")
            task_graph._refresh_readiness(mid)
        else:
            _ev(eid, tid, mid, "TOOL_FAILED", {"error": (result.get("error") or "")[:500], "lat_ms": lat})
            _handle_failure(eid, result.get("error") or "tool failed")
    except Exception as exc:
        try:
            _ev(eid, tid, mid, "WORKER_ERROR", {"error": str(exc)[:500]})
            _handle_failure(eid, f"worker error: {exc}"[:MAXERR])
        except Exception:
            pass

_SCHED, _SCHED_RUN, _SCHED_LOCK = None, False, threading.Lock()

def scheduler_start():
    global _SCHED, _SCHED_RUN
    with _SCHED_LOCK:
        if _SCHED_RUN and _SCHED is not None and _SCHED.is_alive():
            return {"ok": True, "already_running": True}
        _SCHED_RUN = True
        def _loop():
            iv = max(0.05, _fcfg("poll", POLL))
            while _SCHED_RUN:
                try: _tick()
                except Exception: pass
                time.sleep(iv)
        _SCHED = threading.Thread(target=_loop, daemon=True, name="heer-scheduler")
        _SCHED.start()
        _audit("scheduler_start", "", True)
        return {"ok": True, "already_running": False}

def scheduler_stop():
    global _SCHED_RUN, _SCHED, _EXEC
    with _SCHED_LOCK:
        _SCHED_RUN = False; th = _SCHED; _SCHED = None
    if th is not None: th.join(timeout=5)
    with _EXEC_LOCK:
        if _EXEC is not None:
            try: _EXEC.shutdown(wait=True)
            except Exception: pass
            _EXEC = None
    _audit("scheduler_stop", "", True)
    return {"ok": True, "stopped": True}

def scheduler_status():
    with _SCHED_LOCK: running = bool(_SCHED_RUN)
    c = _conn()
    try:
        active = c.execute("SELECT COUNT(*) n FROM executions WHERE status IN ('CLAIMED','IN_PROGRESS')").fetchone()["n"]
        retries = c.execute("SELECT COUNT(*) n FROM executions WHERE status='RETRY_SCHEDULED'").fetchone()["n"]
    finally:
        c.close()
    return {"ok": True, "scheduler_running": running, "config": _rcfg(), "active_executions": active,
            "pending_retries": retries, "per_mission_limits": dict(_LIMITS)}

def _active_global():
    c = _conn()
    try:
        return c.execute("SELECT COUNT(*) n FROM executions WHERE status IN ('CLAIMED','IN_PROGRESS')").fetchone()["n"]
    finally:
        c.close()

def _active_mission(mid):
    c = _conn()
    try:
        return c.execute("SELECT COUNT(*) n FROM executions WHERE mission_id=? AND status IN ('CLAIMED','IN_PROGRESS')",
                         (mid,)).fetchone()["n"]
    finally:
        c.close()

def _dispatch_ready():
    gmax = _icfg("max_concurrent", MAX_C)
    for m in mission_engine.list_missions(limit=200)["missions"]:
        if m["status"] not in (mission_engine.STATUS_RUNNING, mission_engine.STATUS_READY): continue
        if _active_global() >= gmax: return
        per = _LIMITS.get(m["mission_id"], _icfg("per_mission", PER_M))
        q = task_graph.ready_tasks(m["mission_id"])
        if not q["ok"]: continue
        for t in q["ready"]:
            if _active_global() >= gmax: return
            if per and _active_mission(m["mission_id"]) >= per: break
            eid = _claim(t["task_id"], m["mission_id"])
            if eid: _dispatch(eid)

def _dispatch_retries():
    gmax = _icfg("max_concurrent", MAX_C)
    c = _conn()
    try:
        rows = c.execute("SELECT execution_id FROM executions WHERE status='RETRY_SCHEDULED' AND lease_expires_at <= ?",
                         (_now(),)).fetchall()
    finally:
        c.close()
    for r in rows:
        if _active_global() >= gmax: return
        eid = _claim_retry(r["execution_id"])
        if eid: _dispatch(eid)

def _sweep():
    c = _conn()
    try:
        rows = c.execute("SELECT execution_id FROM executions WHERE status IN ('CLAIMED','IN_PROGRESS') "
                         "AND lease_expires_at < ?", (_now(),)).fetchall()
    finally:
        c.close()
    for r in rows:
        e = _row(r["execution_id"])
        if e is None: continue
        with _LOCK:
            cc = _conn()
            try:
                cc.execute("BEGIN IMMEDIATE")
                cc.execute("UPDATE executions SET status=?, error=?, updated_at=?, finished_at=? "
                           "WHERE execution_id=? AND status IN ('CLAIMED','IN_PROGRESS')",
                           (LEASE_EXPIRED, "lease expired", _now(), _now(), r["execution_id"]))
                cc.commit()
            finally:
                cc.close()
        _ev(r["execution_id"], e["task_id"], e["mission_id"], "LEASE_EXPIRED", {})
        task = task_graph.get_task(e["mission_id"], e["task_id"])
        if task is None:
            _mark_abandoned(r["execution_id"], "task missing during recovery"); continue
        if task["status"] != task_graph.TASK_RUNNING:
            _mark_abandoned(r["execution_id"], f"task is {task['status']} during recovery"); continue
        _ev(r["execution_id"], e["task_id"], e["mission_id"], "RECLAIMED", {"action": "worker_crash_recovery"})
        if e["cancel_requested"]:
            r2 = task_graph.transition_task(e["mission_id"], e["task_id"], task_graph.TASK_CANCELLED, error="cancelled")
            if r2["ok"]: task_graph._refresh_readiness(e["mission_id"])
        elif e["idempotent"] and e["attempt_no"] < e["max_attempts"]:
            _schedule_retry(e, "execution lost (worker crash)", force=True)
        else:
            r2 = task_graph.transition_task(e["mission_id"], e["task_id"], task_graph.TASK_FAILED,
                                            error="execution lost (worker crash)")
            if r2["ok"]: task_graph._refresh_readiness(e["mission_id"])

def _timeouts():
    c = _conn()
    now = _now()
    try:
        rows = c.execute("SELECT execution_id FROM executions WHERE status='IN_PROGRESS' AND started_at IS NOT NULL "
                         "AND timeout_sec IS NOT NULL AND timeout_sec > 0 AND started_at + timeout_sec < ?", (now,)).fetchall()
    finally:
        c.close()
    for r in rows:
        e = _row(r["execution_id"])
        if e is None: continue
        with _LOCK:
            cc = _conn()
            try:
                cc.execute("BEGIN IMMEDIATE")
                cc.execute("UPDATE executions SET status=?, error=?, updated_at=?, finished_at=? "
                           "WHERE execution_id=? AND status='IN_PROGRESS'", (FAILED, "timeout", now, now, r["execution_id"]))
                cc.commit()
            finally:
                cc.close()
        _ev(r["execution_id"], e["task_id"], e["mission_id"], "TIMEOUT", {"timeout_sec": e["timeout_sec"]})
        _audit("task_execution_timeout", e["mission_id"], False, execution_id=r["execution_id"], task_id=e["task_id"])
        if e["idempotent"] and e["attempt_no"] < e["max_attempts"] and not e["cancel_requested"]:
            _schedule_retry(e, "task timeout", force=True)
        else:
            rr = task_graph.transition_task(e["mission_id"], e["task_id"], task_graph.TASK_FAILED, error="task timeout")
            if rr["ok"]: task_graph._refresh_readiness(e["mission_id"])
    mt = _fcfg("mission_timeout", MTMO)
    if mt:
        for mid, st in list(_STARTS.items()):
            mm = mission_engine.get_mission(mid)
            if mm is None or mm["status"] != mission_engine.STATUS_RUNNING: continue
            if now - st > mt:
                _ev("", "", mid, "MISSION_TIMEOUT", {})
                mission_engine.transition(mid, mission_engine.STATUS_FAILED, error="mission timeout")
                _cancel_live(mid, "mission timeout")
                _STARTS.pop(mid, None)

def _cancels():
    c = _conn()
    try:
        rows = c.execute("SELECT execution_id FROM executions WHERE status='CLAIMED' AND cancel_requested=1").fetchall()
    finally:
        c.close()
    for r in rows:
        e = _row(r["execution_id"])
        if e is None: continue
        with _LOCK:
            cc = _conn()
            try:
                cc.execute("BEGIN IMMEDIATE")
                cc.execute("UPDATE executions SET status=?, error=?, updated_at=?, finished_at=? "
                           "WHERE execution_id=? AND status='CLAIMED'", (ABANDONED, "cancelled before run", _now(), _now(),
                                                                          r["execution_id"]))
                cc.commit()
            finally:
                cc.close()
        _ev(r["execution_id"], e["task_id"], e["mission_id"], "CANCELLED", {"reason": "cancelled before run"})
        task = task_graph.get_task(e["mission_id"], e["task_id"])
        if task is not None and task["status"] == task_graph.TASK_RUNNING:
            rr = task_graph.transition_task(e["mission_id"], e["task_id"], task_graph.TASK_CANCELLED, error="cancelled")
            if rr["ok"]: task_graph._refresh_readiness(e["mission_id"])

def _finalize_mission(mid):
    m = mission_engine.get_mission(mid)
    if m is None or m["status"] != mission_engine.STATUS_RUNNING: return
    q = task_graph.list_tasks(mid)
    if not q["ok"]: return
    tasks = q["tasks"]
    if not tasks: return
    states = {t["status"] for t in tasks}
    if states & {task_graph.TASK_RUNNING, task_graph.TASK_READY, task_graph.TASK_PENDING}: return
    leftover = states - {task_graph.TASK_COMPLETED, task_graph.TASK_CANCELLED, task_graph.TASK_BLOCKED, task_graph.TASK_FAILED}
    if states <= {task_graph.TASK_COMPLETED}:
        mission_engine.transition(mid, mission_engine.STATUS_COMPLETED, result={"tasks": len(tasks)})
        _audit("mission_execute_end", mid, True, detail="completed")
    elif task_graph.TASK_FAILED in states:
        mission_engine.transition(mid, mission_engine.STATUS_FAILED, error="one or more tasks failed permanently")
        _audit("mission_execute_end", mid, False, detail="failed")
    else:
        mission_engine.transition(mid, mission_engine.STATUS_CANCELLED)
        _audit("mission_execute_end", mid, False, detail="cancelled")
    _STARTS.pop(mid, None)

def _tick():
    _sweep(); _timeouts(); _cancels(); _dispatch_retries(); _dispatch_ready()
    for m in mission_engine.list_missions(limit=200)["missions"]:
        if m["status"] == mission_engine.STATUS_RUNNING:
            _finalize_mission(m["mission_id"])

def recover():
    _sweep(); _timeouts(); _cancels(); _dispatch_retries(); _dispatch_ready()
    for m in mission_engine.list_missions(limit=200)["missions"]:
        if m["status"] in (mission_engine.STATUS_RUNNING, mission_engine.STATUS_READY):
            _finalize_mission(m["mission_id"])
    _audit("scheduler_recovery", "", True)
    return {"ok": True, "active_missions": len(_STARTS)}

def start_mission(mission_id, *, business_id=None, max_concurrent=None):
    m = mission_engine.get_mission(mission_id)
    if m is None: return {"ok": False, "error": f"mission '{mission_id}' not found."}
    if m["status"] in (mission_engine.STATUS_COMPLETED, mission_engine.STATUS_FAILED,
                       mission_engine.STATUS_CANCELLED):
        return {"ok": False, "error": f"mission is {m['status']} (terminal); cannot execute."}
    if m["status"] == mission_engine.STATUS_PAUSED:
        return {"ok": False, "error": "mission is PAUSED; resume before executing."}
    step = {mission_engine.STATUS_CREATED: mission_engine.STATUS_PLANNED,
            mission_engine.STATUS_PLANNED: mission_engine.STATUS_READY,
            mission_engine.STATUS_READY: mission_engine.STATUS_RUNNING}
    while m["status"] in step:
        r = mission_engine.transition(mission_id, step[m["status"]])
        if not r["ok"]: return {"ok": False, "error": r["error"]}
        m = r["mission"]
    if max_concurrent is not None:
        try: _LIMITS[mission_id] = max(1, int(max_concurrent))
        except (TypeError, ValueError): return {"ok": False, "error": "max_concurrent must be an int >= 1"}
    _STARTS[mission_id] = _now()
    _audit("mission_execute_start", mission_id, True)
    scheduler_start(); recover()
    for _ in range(3): _tick()
    exs = list_executions(mission_id=mission_id)["executions"]
    return {"ok": True, "mission": mission_engine.get_mission(mission_id),
            "active_workers": _active_mission(mission_id),
            "dispatched": [x["execution_id"] for x in exs if x["status"] in LIVE + (RETRY_SCHEDULED,)]}

def pause_mission(mission_id):
    r = mission_engine.transition(mission_id, mission_engine.STATUS_PAUSED)
    if not r["ok"]: return {"ok": False, "error": r["error"]}
    _STARTS.pop(mission_id, None)
    _audit("mission_execute_pause", mission_id, True)
    return {"ok": True, "mission": r["mission"]}

def resume_mission(mission_id):
    r = mission_engine.transition(mission_id, mission_engine.STATUS_RUNNING)
    if not r["ok"]: return {"ok": False, "error": r["error"]}
    _STARTS[mission_id] = _now()
    _audit("mission_execute_resume", mission_id, True)
    scheduler_start(); recover()
    return {"ok": True, "mission": r["mission"]}

def _cancel_live(mid, reason):
    with _LOCK:
        c = _conn()
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute("UPDATE executions SET cancel_requested=1, updated_at=? "
                      "WHERE mission_id=? AND status IN ('CLAIMED','IN_PROGRESS') AND cancel_requested=0", (_now(), mid))
            c.commit()
        finally:
            c.close()
    c = _conn()
    try:
        rows = c.execute("SELECT execution_id, task_id FROM executions WHERE mission_id=? AND status IN ('CLAIMED','IN_PROGRESS')",
                         (mid,)).fetchall()
    finally:
        c.close()
    for r in rows:
        _ev(r["execution_id"], r["task_id"], mid, "CANCELLED", {"reason": reason})

def stop_mission(mission_id):
    m = mission_engine.get_mission(mission_id)
    if m is None: return {"ok": False, "error": f"mission '{mission_id}' not found."}
    _STARTS.pop(mission_id, None)
    _cancel_live(mission_id, "mission cancelled")
    q = task_graph.list_tasks(mission_id)
    cancelled = []
    if q["ok"]:
        for t in q["tasks"]:
            if t["status"] in (task_graph.TASK_PENDING, task_graph.TASK_READY, task_graph.TASK_BLOCKED):
                r = task_graph.transition_task(mission_id, t["task_id"], task_graph.TASK_CANCELLED,
                                               error="mission cancelled")
                if r["ok"]: cancelled.append(t["task_id"])
        task_graph._refresh_readiness(mission_id)
    if m["status"] not in (mission_engine.STATUS_COMPLETED, mission_engine.STATUS_FAILED,
                           mission_engine.STATUS_CANCELLED):
        mission_engine.transition(mission_id, mission_engine.STATUS_CANCELLED)
    _audit("mission_execute_cancel", mission_id, True)
    return {"ok": True, "mission": mission_engine.get_mission(mission_id), "cancelled": cancelled}

def cancel_task(mission_id, task_id):
    task = task_graph.get_task(mission_id, task_id)
    if task is None: return {"ok": False, "error": f"task '{task_id}' not found in mission '{mission_id}'."}
    if task["status"] in (task_graph.TASK_PENDING, task_graph.TASK_READY, task_graph.TASK_BLOCKED):
        r = task_graph.transition_task(mission_id, task_id, task_graph.TASK_CANCELLED, error="cancelled")
        if not r["ok"]: return {"ok": False, "error": r["error"]}
        _audit("task_execution_cancel", mission_id, False, task_id=task_id, detail="pre_run")
        task_graph._refresh_readiness(mission_id)
        return {"ok": True, "task": r["task"], "mode": "pre_run"}
    if task["status"] == task_graph.TASK_RUNNING:
        live = _live_for_task(task_id)
        if live: _set_cancel(live)
        _ev(live or "", task_id, mission_id, "CANCELLED", {"reason": "cooperative cancel requested"})
        _audit("task_execution_cancel", mission_id, False, execution_id=live, task_id=task_id, detail="cooperative")
        return {"ok": True, "task": task_graph.get_task(mission_id, task_id), "mode": "cooperative",
                "execution_id": live}
    return {"ok": False, "error": f"task is {task['status']} (terminal); cannot cancel."}

def retry_task(mission_id, task_id, *, reason="manual"):
    task = task_graph.get_task(mission_id, task_id)
    if task is None: return {"ok": False, "error": f"task '{task_id}' not found in mission '{mission_id}'."}
    if task["status"] != task_graph.TASK_RUNNING:
        return {"ok": False, "error": "manual retry is only supported for RUNNING tasks with a pending retry; "
                "terminal tasks cannot be re-opened without modifying Phase 3.2 semantics."}
    c = _conn()
    try:
        row = c.execute("SELECT execution_id FROM executions WHERE task_id=? AND status='RETRY_SCHEDULED' "
                        "ORDER BY attempt_no DESC LIMIT 1", (task_id,)).fetchone()
    finally:
        c.close()
    if row is None: return {"ok": False, "error": "no pending retry found for a RUNNING task."}
    eid = _claim_retry(row["execution_id"])
    if not eid: return {"ok": False, "error": "retry claim lost (race)."}
    _dispatch(eid)
    _ev(eid, task_id, mission_id, "RETRY_WOKEN", {"reason": reason})
    return {"ok": True, "execution": _row(eid)}

def list_executions(*, mission_id=None, task_id=None, execution_id=None, status=None, limit=100):
    sql = "SELECT * FROM executions WHERE 1=1"; args = []
    if mission_id is not None: sql += " AND mission_id=?"; args.append(mission_id)
    if task_id is not None: sql += " AND task_id=?"; args.append(task_id)
    if execution_id is not None: sql += " AND execution_id=?"; args.append(execution_id)
    if status is not None:
        if isinstance(status, (list, tuple)):
            sql += f" AND status IN ({','.join('?' * len(status))})"; args += list(status)
        else:
            sql += " AND status=?"; args.append(status)
    sql += " ORDER BY created_at DESC LIMIT ?"; args.append(int(limit))
    c = _conn()
    try:
        rows = c.execute(sql, args).fetchall()
    finally:
        c.close()
    return {"ok": True, "count": len(rows),
            "executions": [dict(r, idempotent=bool(r["idempotent"]),
                                cancel_requested=bool(r["cancel_requested"]),
                                input_snapshot=_loads(r["input_snapshot"]), output=_loads(r["output"]))
                           for r in rows]}

def list_events(*, mission_id=None, execution_id=None, event_type=None, limit=200):
    sql = "SELECT * FROM execution_events WHERE 1=1"; args = []
    if mission_id is not None: sql += " AND mission_id=?"; args.append(mission_id)
    if execution_id is not None: sql += " AND execution_id=?"; args.append(execution_id)
    if event_type is not None: sql += " AND event_type=?"; args.append(event_type)
    sql += " ORDER BY ts DESC LIMIT ?"; args.append(int(limit))
    c = _conn()
    try:
        rows = c.execute(sql, args).fetchall()
    finally:
        c.close()
    return {"ok": True, "count": len(rows), "events":
            [{"event_id": r["event_id"], "execution_id": r["execution_id"], "task_id": r["task_id"],
              "mission_id": r["mission_id"], "event_type": r["event_type"], "ts": r["ts"],
              "payload": _loads(r["payload"], {})} for r in rows]}

def metrics():
    c = _conn()
    try:
        by_status = {r["status"]: r["n"] for r in c.execute(
            "SELECT status, COUNT(*) n FROM executions GROUP BY status")}
        total = sum(by_status.values())
        failed = c.execute("SELECT COUNT(*) n FROM executions WHERE status='FAILED'").fetchone()["n"]
        retried = c.execute("SELECT COUNT(*) n FROM executions WHERE status='RETRY_SCHEDULED'").fetchone()["n"]
        avg_ok = c.execute("SELECT AVG((output ->> '$.lat_ms')) a FROM executions WHERE status='COMPLETED' "
                           "AND output IS NOT NULL").fetchone()["a"]
        top_tools = c.execute("SELECT e.task_id, COUNT(*) n FROM executions e WHERE e.status='FAILED' "
                              "GROUP BY e.task_id ORDER BY n DESC LIMIT 5").fetchall()
    finally:
        c.close()
    return {"ok": True, "total_executions": total, "by_status": by_status, "failed": failed,
            "pending_retries": retried, "avg_success_lat_ms": round(avg_ok, 1) if avg_ok else None,
            "top_failed_tasks": [{"task_id": r["task_id"], "failures": r["n"]} for r in top_tools]}
