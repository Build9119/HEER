#!/usr/bin/env python3
"""ai_inventory.py — HEER AI Inventory Registry.

Tracks AI systems, agents, models, providers, versions, capabilities,
ownership, risk classification, lifecycle state, approval state, associated
business, associated execution identity, agent IDs, and governance metadata.

Run:  python3 -m agent.ai_inventory --self-test
"""

import json
import os
import sqlite3
import time
import uuid

from . import data

DB_NAME = "ai_inventory.sqlite3"
STATE_DIR = os.path.join(
    os.path.abspath(os.path.join(data.data_root() or ".", "..")),
    ".heer",
)

_LIFECYCLE = ("active", "deprecated", "retired")
_APPROVAL = ("approved", "pending", "denied")
_RISK = ("low", "medium", "high", "critical")
_TYPE = ("system", "agent", "model", "provider")


def _state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)
    return STATE_DIR


def _db_path():
    return os.path.join(_state_dir(), DB_NAME)


def _conn():
    c = sqlite3.connect(_db_path())
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=30000")
    c.execute(
        """CREATE TABLE IF NOT EXISTS ai_inventory (
            inventory_id TEXT PRIMARY KEY,
            agent_id TEXT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            version TEXT DEFAULT '',
            provider TEXT DEFAULT '',
            capabilities TEXT DEFAULT '[]',
            ownership TEXT DEFAULT '',
            risk_classification TEXT DEFAULT 'low',
            lifecycle_state TEXT DEFAULT 'active',
            approval_state TEXT DEFAULT 'pending',
            business_id TEXT DEFAULT '',
            execution_identity TEXT DEFAULT '',
            governance_metadata TEXT DEFAULT '{}',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )"""
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS ix_inv_agent ON ai_inventory(agent_id)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS ix_inv_business ON ai_inventory(business_id)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS ix_inv_type ON ai_inventory(type)"
    )
    return c


def _now():
    return time.time()


def _validate(item):
    if not isinstance(item, dict):
        raise ValueError("item must be a dict")
    name = (item.get("name") or "").strip()
    if not name:
        raise ValueError("name is required")
    typ = (item.get("type") or "").strip().lower()
    if typ not in _TYPE:
        raise ValueError(f"type must be one of {_TYPE}")
    risk = (item.get("risk_classification") or "low").strip().lower()
    if risk not in _RISK:
        raise ValueError(f"risk_classification must be one of {_RISK}")
    lifecycle = (item.get("lifecycle_state") or "active").strip().lower()
    if lifecycle not in _LIFECYCLE:
        raise ValueError(f"lifecycle_state must be one of {_LIFECYCLE}")
    approval = (item.get("approval_state") or "pending").strip().lower()
    if approval not in _APPROVAL:
        raise ValueError(f"approval_state must be one of {_APPROVAL}")
    return True


def create(item):
    """Create an inventory record. Returns {"ok": bool, "inventory": dict|None, "error": str}."""
    try:
        _validate(item)
    except ValueError as e:
        return {"ok": False, "inventory": None, "error": str(e)}
    iid = str(uuid.uuid4())[:12]
    now = _now()
    row = {
        "inventory_id": iid,
        "agent_id": (item.get("agent_id") or "").strip(),
        "name": item["name"].strip(),
        "type": item["type"].strip().lower(),
        "version": (item.get("version") or "").strip(),
        "provider": (item.get("provider") or "").strip(),
        "capabilities": json.dumps(item.get("capabilities") or []),
        "ownership": (item.get("ownership") or "").strip(),
        "risk_classification": (item.get("risk_classification") or "low").strip().lower(),
        "lifecycle_state": (item.get("lifecycle_state") or "active").strip().lower(),
        "approval_state": (item.get("approval_state") or "pending").strip().lower(),
        "business_id": (item.get("business_id") or "").strip(),
        "execution_identity": (item.get("execution_identity") or "").strip(),
        "governance_metadata": json.dumps(item.get("governance_metadata") or {}),
        "created_at": now,
        "updated_at": now,
    }
    c = _conn()
    c.execute(
        "INSERT INTO ai_inventory VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        tuple(row.values()),
    )
    c.commit()
    c.close()
    return {"ok": True, "inventory": _row_to_dict(row)}


def get(inventory_id):
    """Return an inventory record by id, or None."""
    c = _conn()
    cols = [d[1] for d in c.execute("PRAGMA table_info(ai_inventory)").fetchall()]
    row = c.execute(
        "SELECT * FROM ai_inventory WHERE inventory_id=?", (inventory_id,)
    ).fetchone()
    c.close()
    if row is None:
        return None
    return _row_to_dict(dict(zip(cols, row)))


def list_items(business_id=None, agent_id=None, type_=None, limit=100):
    """List inventory records, optionally filtered."""
    sql = "SELECT * FROM ai_inventory WHERE 1=1"
    params = []
    if business_id:
        sql += " AND business_id=?"
        params.append(business_id)
    if agent_id:
        sql += " AND agent_id=?"
        params.append(agent_id)
    if type_:
        sql += " AND type=?"
        params.append(type_.lower())
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(int(limit))
    c = _conn()
    rows = c.execute(sql, params).fetchall()
    cols = [d[1] for d in c.execute("PRAGMA table_info(ai_inventory)").fetchall()]
    c.close()
    return [_row_to_dict(dict(zip(cols, r))) for r in rows]


def update(inventory_id, changes):
    """Update mutable fields on an inventory record. Returns updated dict or None."""
    allowed = {
        "name", "version", "provider", "capabilities", "ownership",
        "risk_classification", "lifecycle_state", "approval_state",
        "business_id", "execution_identity", "governance_metadata",
    }
    if not changes:
        return get(inventory_id)
    patch = {k: v for k, v in changes.items() if k in allowed}
    if not patch:
        return get(inventory_id)
    if "risk_classification" in patch:
        patch["risk_classification"] = patch["risk_classification"].strip().lower()
        if patch["risk_classification"] not in _RISK:
            raise ValueError(f"risk_classification must be one of {_RISK}")
    if "lifecycle_state" in patch:
        patch["lifecycle_state"] = patch["lifecycle_state"].strip().lower()
        if patch["lifecycle_state"] not in _LIFECYCLE:
            raise ValueError(f"lifecycle_state must be one of {_LIFECYCLE}")
    if "approval_state" in patch:
        patch["approval_state"] = patch["approval_state"].strip().lower()
        if patch["approval_state"] not in _APPROVAL:
            raise ValueError(f"approval_state must be one of {_APPROVAL}")
    if "capabilities" in patch:
        patch["capabilities"] = json.dumps(patch["capabilities"] or [])
    if "governance_metadata" in patch:
        patch["governance_metadata"] = json.dumps(patch["governance_metadata"] or {})
    patch["updated_at"] = _now()
    set_clause = ", ".join(f"{k}=?" for k in patch)
    vals = list(patch.values()) + [inventory_id]
    c = _conn()
    c.execute(f"UPDATE ai_inventory SET {set_clause} WHERE inventory_id=?", vals)
    c.commit()
    c.close()
    return get(inventory_id)


def delete(inventory_id):
    """Delete an inventory record. Returns True if deleted."""
    c = _conn()
    cur = c.execute("DELETE FROM ai_inventory WHERE inventory_id=?", (inventory_id,))
    c.commit()
    c.close()
    return cur.rowcount > 0


def _row_to_dict(row):
    out = dict(row)
    for key in ("capabilities", "governance_metadata"):
        val = out.get(key, "[]")
        try:
            out[key] = json.loads(val) if val else ([] if key == "capabilities" else {})
        except (json.JSONDecodeError, TypeError):
            out[key] = [] if key == "capabilities" else {}
    return out


def _self_test():
    import sys
    tests = []
    try:
        r = create({
            "name": "Test Agent",
            "type": "agent",
            "agent_id": "ceo",
            "business_id": "ai_agency",
            "capabilities": ["briefing", "search"],
            "risk_classification": "low",
            "lifecycle_state": "active",
            "approval_state": "approved",
        })
        tests.append(("create", r["ok"]))
        iid = r["inventory"]["inventory_id"]

        g = get(iid)
        tests.append(("get", g is not None and g["name"] == "Test Agent"))

        lst = list_items(business_id="ai_agency")
        tests.append(("list filter", len(lst) >= 1))

        u = update(iid, {"version": "2.0", "approval_state": "pending"})
        tests.append(("update", u is not None and u["version"] == "2.0" and u["approval_state"] == "pending"))

        d = delete(iid)
        tests.append(("delete", d is True))

        g2 = get(iid)
        tests.append(("deleted", g2 is None))
    except Exception as e:
        tests.append(("exception", False))
        print(f"Exception: {e}")

    failed = [t for t, ok in tests if not ok]
    print("AI Inventory self-test")
    print("-" * 40)
    for t, ok in tests:
        print(f"[{'PASS' if ok else 'FAIL'}] {t}")
    print("-" * 40)
    print(f"Result: {'ALL PASS' if not failed else 'FAILURES'}")
    return 0 if not failed else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())
