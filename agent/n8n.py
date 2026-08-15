#!/usr/bin/env python3
"""n8n.py — HEER Automation Agent (Phase 3.5).

Tools:
  n8n (L2): validate + generate n8n workflow specs.

Demo mode: workflow is validated and rendered as a dry-run artifact with
no external service. Real mode (HEER_EXECUTION=1) returns the validated
workflow JSON ready for n8n import.

Run:  python3 -m agent.n8n --self-test
"""

import json
import os

from . import data

_EXECUTION_ON = "1"

WORKFLOW_TEMPLATES = {
    "ci_sync": {
        "description": "Sync CI status to a channel on workflow completion.",
        "steps": [
            {"node": "webhook", "config": {"path": "/ci-sync", "method": "POST"}},
            {"node": "filter", "config": {"conditions": [{"field": "conclusion", "op": "equals", "value": "success"}]}},
            {"node": "http", "config": {"method": "POST", "url": "{{NOTIFY_WEBHOOK_URL}}", "headers": {}}},
        ],
        "outputs": [{"kind": "notify", "target": "channel#ci"}],
    },
    "market_intel_daily": {
        "description": "Daily market intelligence scan for the AI Agency.",
        "steps": [
            {"node": "schedule", "config": {"cron": "0 7 * * 1-5"}},
            {"node": "http", "config": {"method": "GET", "url": "{{INTEL_SOURCE_URL}}", "headers": {}}},
            {"node": "function", "config": {"code": "extract top 3 signals"}},
            {"node": "http", "config": {"method": "POST", "url": "{{INTEL_OUT_WEBHOOK}}", "headers": {}}},
        ],
        "outputs": [{"kind": "n8n", "target": "business_intel"}],
    },
    "lead_followup": {
        "description": "Follow up on opportunities not contacted in 7 days.",
        "steps": [
            {"node": "schedule", "config": {"cron": "0 9 * * 1-5"}},
            {"node": "http", "config": {"method": "GET", "url": "{{CRM_URL}}/stale-opportunities", "headers": {}}},
            {"node": "function", "config": {"code": "build follow-up message per lead"}},
            {"node": "http", "config": {"method": "POST", "url": "{{EMAIL_SERVICE}}/send", "headers": {}}},
        ],
        "outputs": [{"kind": "notify", "target": "sales#followup"}],
    },
}


def _execution_enabled():
    return data.env("HEER_EXECUTION", "0") == _EXECUTION_ON


def validate_workflow(wf):
    """Validate a workflow dict. Returns (ok, errors)."""
    errors = []
    if not isinstance(wf, dict):
        return False, ["workflow must be an object"]
    if not wf.get("name"):
        errors.append("name is required")
    if wf.get("trigger") not in ("schedule", "webhook", "manual"):
        errors.append("trigger must be one of: schedule, webhook, manual")
    if not isinstance(wf.get("steps"), list) or not wf["steps"]:
        errors.append("steps must be a non-empty list")
    for i, step in enumerate(wf.get("steps", [])):
        if not isinstance(step, dict):
            errors.append(f"step {i}: must be an object")
            continue
        if step.get("node") not in ("http", "webhook", "function", "filter",
                                    "schedule", "notify"):
            errors.append(f"step {i}: unknown node type '{step.get('node')}'")
    if not isinstance(wf.get("outputs"), list) or not wf["outputs"]:
        errors.append("outputs must be a non-empty list")
    for i, step in enumerate(wf.get("steps", [])):
        if step.get("node") == "schedule" and not step.get("config", {}).get("cron"):
            errors.append(f"step {i}: schedule step requires a cron expression")
    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# n8n (L2)
# ---------------------------------------------------------------------------


def n8n(workflow=None, trigger=None, name=None, steps=None, business_id=None):
    """Validate and generate an n8n workflow spec."""
    if workflow is None and (trigger or name or steps):
        workflow = {
            "name": name or f"Workflow {trigger or 'manual'}",
            "trigger": trigger or "manual",
            "inputs": [],
            "steps": steps or [],
            "outputs": [{"kind": "n8n", "target": "n8n_instance"}],
            "error": {"retry": 0, "notify": ""},
            "logging": {"enabled": True, "level": "info"},
        }
    if isinstance(workflow, str):
        try:
            workflow = json.loads(workflow)
        except json.JSONDecodeError as e:
            return {"ok": False, "error": f"Invalid workflow JSON: {e}"}

    valid, errors = validate_workflow(workflow)
    if not valid:
        return {"ok": False, "error": "Workflow validation failed.",
                "errors": errors}

    if _execution_enabled():
        return {
            "ok": True, "workflow": workflow, "mode": "executed",
            "status": "validated",
            "summary": f"Workflow '{workflow['name']}' is valid and ready for n8n import.",
            "import_url": "/workflows/import",
        }

    return {
        "ok": True, "workflow": workflow, "mode": "dry_run",
        "status": "validated",
        "summary": f"Workflow '{workflow['name']}' is valid "
                   "(HEER_EXECUTION=0 — dry-run only).",
        "would_import": True,
    }


def workflow_payload(name=None):
    """List available workflow templates with metadata."""
    out = []
    for key, wf in WORKFLOW_TEMPLATES.items():
        if name and key != name:
            continue
        out.append({
            "id": key,
            "name": key,
            "description": wf["description"],
            "trigger": next((s["config"].get("cron") and "schedule"
                             for s in wf["steps"] if s["node"] == "schedule"),
                            "webhook/manual"),
            "step_count": len(wf["steps"]),
        })
    return {"workflows": out, "total": len(out)}


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


def call_n8n_tool(name, args=None, business_id=None):
    args = args or {}
    if name == "n8n":
        r = n8n(workflow=args.get("workflow"), trigger=args.get("trigger"),
                name=args.get("name"), steps=args.get("steps"), business_id=business_id)
        return {"tool": name, **r}
    return {"tool": name, "ok": False, "error": f"Unknown n8n tool '{name}'."}


N8N_TOOLS = {
    "n8n": {
        "desc": "Validate and generate n8n workflow specs (L2 approval for import).",
        "params": {
            "name": "string (optional)",
            "trigger": "schedule|webhook|manual",
            "steps": "list of {node, config}",
            "workflow": "full workflow dict (optional, overrides parts)",
        },
        "fn": lambda name, args, business_id=None: call_n8n_tool(name, args, business_id),
    },
}


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------


def _self_test():
    print("HEER Automation (n8n) Agent self-test\n" + "-" * 40)
    results = []

    wf = {"name": "Test Sync", "trigger": "webhook",
          "inputs": [], "steps": [{"node": "webhook", "config": {"path": "/t", "method": "POST"}}],
          "outputs": [{"kind": "n8n", "target": "x"}],
          "error": {"retry": 0}, "logging": {"enabled": True, "level": "info"}}
    r1 = n8n(workflow=wf)
    ok1 = r1.get("ok") is True and r1.get("mode") == "dry_run"
    results.append(("n8n validates valid workflow (dry-run)", ok1))

    bad = {"name": "Bad", "trigger": "bogus", "steps": [], "outputs": []}
    r2 = n8n(workflow=bad)
    ok2 = r2.get("ok") is False and "errors" in r2
    results.append(("n8n rejects invalid workflow", ok2))

    r3 = n8n(trigger="schedule", name="Daily Scan",
             steps=[{"node": "schedule", "config": {"cron": "0 8 * * *"}},
                    {"node": "http", "config": {"method": "GET", "url": "https://example.com"}}])
    ok3 = (r3.get("ok") is True and r3.get("workflow", {}).get("trigger") == "schedule"
           and len(r3.get("workflow", {}).get("steps", [])) == 2)
    results.append(("n8n build-from-parts", ok3))

    bad_sched = {"name": "No Cron", "trigger": "schedule",
                 "steps": [{"node": "schedule", "config": {}}],
                 "outputs": [{"kind": "n8n", "target": "x"}]}
    r4 = n8n(workflow=bad_sched)
    ok4 = r4.get("ok") is False and any("cron" in e for e in r4.get("errors", []))
    results.append(("n8n requires cron on schedule steps", ok4))

    r5 = workflow_payload()
    ok5 = r5.get("total", 0) >= 2 and all("id" in w for w in r5["workflows"])
    results.append(("workflow_payload lists templates", ok5))

    for label, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    print("-" * 40)
    print(f"Result: {'ALL PASS' if all(ok for _, ok in results) else 'FAILURES'}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())