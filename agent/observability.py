#!/usr/bin/env python3
"""observability.py — HEER structured logging + metrics export.

Provides:
  - log_event(): structured JSON log record to stderr
  - metrics(): aggregated metrics from execution engine, audit, approvals,
    and AI inventory

Run:  python3 -m agent.observability --self-test
"""

import json
import os
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from . import ai_inventory, audit, data, execution_engine, approvals


def log_event(event, payload=None, **kwargs):
    """Emit a structured JSON log record to stderr."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        "payload": payload or {},
    }
    record.update(kwargs)
    sys.stderr.write(json.dumps(record, default=str) + "\n")


def metrics():
    """Aggregated metrics from all HEER subsystems."""
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution": execution_engine.metrics(),
        "audit": audit.metrics(),
        "approvals": {"pending": len(approvals.pending_approvals())},
        "ai_inventory": {"total": len(ai_inventory.list_items(limit=1000))},
    }
    return out


def _self_test():
    log_event("self_test_start")
    m = metrics()
    ok = isinstance(m, dict) and "execution" in m and "audit" in m
    log_event("self_test_complete", ok=ok, metrics=m)
    print(f"[{'PASS' if ok else 'FAIL'}] observability metrics aggregation")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())
