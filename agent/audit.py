#!/usr/bin/env python3
"""audit.py — HEER Execution Audit Log (Phase 1).

Records every agent execution (request → intent → agent → tools →
approval → outcome) in SQLite for traceability and metrics.
"""

import json
import os
import sqlite3
import time
import uuid

from . import data


def _state_dir():
    root = data.data_root() or os.path.abspath(".")
    d = os.path.join(os.path.abspath(os.path.join(root, "..")), ".heer")
    os.makedirs(d, exist_ok=True)
    return d


def _db_path():
    return os.path.join(_state_dir(), "executions.sqlite3")


def _conn():
    c = sqlite3.connect(_db_path())
    c.execute(
        """CREATE TABLE IF NOT EXISTS agent_executions (
            id TEXT PRIMARY KEY,
            request TEXT,
            intent TEXT,
            agent_id TEXT,
            tools TEXT,
            inputs TEXT,
            outputs TEXT,
            approval TEXT,
            success INTEGER,
            lat_ms INTEGER,
            created_at REAL
        )"""
    )
    return c


def _summary(outputs):
    """Compact, always-JSON-safe summary of execution outputs.

    Full payloads (business intel, opportunities, ...) can be megabytes and
    force truncation that corrupts stored JSON. We store only the execution
    skeleton: per-tool status + ok/error, never the big `data` blobs.
    """
    if not isinstance(outputs, dict):
        return json.dumps({"note": repr(outputs)[:300]}, default=str)
    if "results" in outputs:
        summary = []
        for r in outputs.get("results", []):
            if not isinstance(r, dict):
                continue
            item = {"tool": r.get("tool"), "status": r.get("status")}
            if "ok" in r:
                item["ok"] = bool(r.get("ok"))
            if "error" in r:
                item["error"] = str(r.get("error"))[:200]
            if "lat_ms" in r:
                item["lat_ms"] = r.get("lat_ms")
            summary.append(item)
        return json.dumps({"blocked": outputs.get("blocked"), "results": summary}, default=str)
    return json.dumps({"note": repr(outputs)[:300]}, default=str)


def record(request, intent, agent_id, tools, inputs, outputs, approval, success, lat_ms):
    """Append an execution record. Returns record id."""
    rid = str(uuid.uuid4())[:12]
    c = _conn()
    c.execute(
        "INSERT INTO agent_executions "
        "(id, request, intent, agent_id, tools, inputs, outputs, approval, success, lat_ms, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            rid, request[:1000], intent, agent_id,
            json.dumps(tools), json.dumps(inputs, default=str)[:2000],
            _summary(outputs),
            json.dumps(approval, default=str), 1 if success else 0,
            int(lat_ms), time.time(),
        ),
    )
    c.commit()
    c.close()
    return rid


def recent(limit=50):
    c = _conn()
    rows = c.execute(
        "SELECT id, request, intent, agent_id, tools, inputs, outputs, approval, success, lat_ms, created_at "
        "FROM agent_executions ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    c.close()
    def _loads(raw, fallback):
        try:
            return json.loads(raw or "")
        except (json.JSONDecodeError, TypeError):
            return fallback

    out = []
    for r in rows:
        out.append({
            "id": r[0], "request": r[1], "intent": r[2], "agent_id": r[3],
            "tools": _loads(r[4], []),
            "inputs": _loads(r[5], {}),
            "outputs": _loads(r[6], {}),
            "approval": _loads(r[7], {}),
            "success": bool(r[8]), "lat_ms": r[9], "created_at": r[10],
        })
    return out


def metrics():
    c = _conn()
    total = c.execute("SELECT COUNT(*) FROM agent_executions").fetchone()[0]
    ok = c.execute("SELECT COUNT(*) FROM agent_executions WHERE success=1").fetchone()[0]
    lat = c.execute("SELECT AVG(lat_ms) FROM agent_executions").fetchone()[0]
    tools_failed = c.execute(
        "SELECT COUNT(*) FROM agent_executions WHERE success=0"
    ).fetchone()[0]
    c.close()
    return {
        "total": total,
        "success": ok,
        "failure": total - ok,
        "success_rate": round(ok / total, 3) if total else 0,
        "avg_lat_ms": round(lat or 0, 1),
        "tool_failures": tools_failed,
    }


def executions_payload(limit=50):
    return {"executions": recent(limit), "metrics": metrics()}