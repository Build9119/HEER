#!/usr/bin/env python3
"""approvals.py — HEER Human Approval Engine (Phase 1).

L0=Read (auto) | L1=Prepare | L2=Execute | L3=Critical.
L1+ actions become pending approvals in SQLite until a human
approves or denies them. See HEER_ROADMAP.md Phase 1.
"""

import json
import os
import sqlite3
import time
import uuid

from . import data

APPROVAL_NAMES = {0: "READ", 1: "PREPARE", 2: "EXECUTE", 3: "CRITICAL"}


def _db_path():
    root = data.data_root() or os.path.abspath(".")
    return os.path.join(os.path.abspath(os.path.join(root, "..")), ".heer", "approvals.sqlite3")


def _conn():
    os.makedirs(os.path.dirname(_db_path()), exist_ok=True)
    c = sqlite3.connect(_db_path())
    c.execute(
        """CREATE TABLE IF NOT EXISTS approvals (
            id TEXT PRIMARY KEY,
            request_id TEXT,
            level INTEGER,
            action TEXT,
            agent_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at REAL,
            responded_at REAL
        )"""
    )
    return c


def requires_approval(level):
    """True when a human must approve actions at this level."""
    return level >= 1


def check(level, action, agent_id="", request_id=""):
    """Check whether an action may proceed.

    Returns {"approved": bool, "approval_id": str|None, "reason": str}.
    L0 auto-passes; L1+ creates a pending approval.
    """
    if not requires_approval(level):
        return {"approved": True, "approval_id": None, "reason": "read-level action"}
    rid = str(uuid.uuid4())[:8]
    c = _conn()
    c.execute(
        "INSERT INTO approvals (id, request_id, level, action, agent_id, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (rid, request_id or "", level, action[:500], agent_id, time.time()),
    )
    c.commit()
    c.close()
    return {
        "approved": False,
        "approval_id": rid,
        "reason": f"{APPROVAL_NAMES.get(level, str(level))} approval required",
    }


def pending_approvals():
    c = _conn()
    rows = c.execute(
        "SELECT id, request_id, level, action, agent_id, created_at "
        "FROM approvals WHERE status='pending' ORDER BY created_at DESC"
    ).fetchall()
    c.close()
    return [
        {
            "id": r[0], "request_id": r[1], "level": r[2],
            "level_name": APPROVAL_NAMES.get(r[2], str(r[2])),
            "action": r[3], "agent_id": r[4], "created_at": r[5],
        }
        for r in rows
    ]


def respond(approval_id, decision):
    """decision: 'approved' | 'denied'. Returns result dict or None if not found."""
    decision = "approved" if decision == "approved" else "denied"
    c = _conn()
    cur = c.execute("SELECT id FROM approvals WHERE id=? AND status='pending'", (approval_id,))
    if cur.fetchone() is None:
        c.close()
        return None
    c.execute(
        "UPDATE approvals SET status=?, responded_at=? WHERE id=?",
        (decision, time.time(), approval_id),
    )
    c.commit()
    c.close()
    return {"id": approval_id, "status": decision}


def approvals_payload():
    return {
        "pending": pending_approvals(),
        "counts": {
            "pending": len(pending_approvals()),
            "levels": APPROVAL_NAMES,
        },
    }