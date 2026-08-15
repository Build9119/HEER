#!/usr/bin/env python3
"""orchestrator.py — HEER Agent Orchestrator (Phase 3.9).

Pipeline: route → plan → approve → execute → verify → audit → respond.

- route():  keyword-scored intent classification against agent registry
- plan():   select minimal tool set for the matched agent
- execute(): run each tool through the approval engine and dispatch
             (L0 auto-passes; L1+ go pending)
- handle(): full pipeline + audit record
- handle_mission(): mission-aware execution — builds a task DAG from the
             request and runs it through the mission layer
- --self-test CLI: canned scenarios (read / prepare-approval / pending /
             mission)
"""

import json
import time

from . import approvals, audit, heer, mission, registry
from .tools import call_tool as _call_tool

# payload accessors: registry tool id -> heer payload function
_PAYLOAD_TOOLS = {
    "briefing": heer.briefing_payload,
    "clients": heer.clients_payload,
    "projects": heer.projects_payload,
    "business_intel": heer.business_payload,
    "opportunities": heer.opportunities_payload,
    "skills_payload": heer.skills_payload,
    "learning_payload": heer.learning_payload,
    "activity_payload": heer.activity_payload,
    "network_payload": heer.network_payload,
    "automations_payload": heer.automations_payload,
    "status_payload": heer.status_payload,
}

# vault tools that take args
_VAULT_TOOLS = {"echo", "clock", "search", "look", "remind", "hubs", "stats"}

# Phase-3 module tools (all dispatched through the unified tools registry)
_MODULE_TOOLS = {
    "mission_create", "mission_list", "mission_get",
    "developer_code_read", "developer_code_write", "developer_test_run",
    "github_github_read", "github_github_write",
    "n8n_n8n",
    "deploy_docker",
    "terminal_terminal_exec",
}

# Mission intent keywords — route to the mission-aware path
_MISSION_KEYWORDS = ("mission", "task graph", "task dag", "workflow",
                     "multi-step", "pipeline")


def route(request):
    """Classify a request to the best-fit agent.

    Returns (agent_id, matched_intent, score).
    """
    text = request.lower()
    best_agent = registry.DEFAULT_AGENT
    best_word = ""
    best_score = 0
    for agent_id, t in registry.AGENT_REGISTRY.items():
        for intent in t[5]:
            if intent in text:
                score = len(intent.split())
                if score > best_score:
                    best_score, best_agent, best_word = score, agent_id, intent
    return best_agent, best_word or best_agent, best_score


def plan(agent_id, request):
    """Return the minimal ordered list of (tool_name, args) for an agent."""
    agent = registry.agent_def(agent_id)
    if agent is None:
        return []
    steps = []
    for t in agent["tools"]:
        if t in _PAYLOAD_TOOLS:
            steps.append((t, {}))
        elif t in _VAULT_TOOLS:
            if t in ("search", "look"):
                steps.append((t, {"query": request[:100]}))
            else:
                steps.append((t, {}))
        elif t in _MODULE_TOOLS:
            steps.append((t, {}))
    return steps


def _dispatch(tool_name, args, business_id):
    """Execute one tool and return its output (never raises)."""
    if tool_name in _PAYLOAD_TOOLS:
        try:
            return {"ok": True, "tool": tool_name, "data": _PAYLOAD_TOOLS[tool_name]()}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "tool": tool_name, "error": str(e)}
    # Everything else (vault + module tools) goes through the unified registry
    return _call_tool(tool_name, args, business_id)


def execute(plan_steps, business_id, request_id):
    """Run each planned step through the approval engine.

    Returns {"results": [...], "approvals": [...], "blocked": bool}
    """
    results, approvals_out = [], []
    for tool_name, args in plan_steps:
        tdef = registry.tool_def(tool_name)
        level = tdef["approval_level"] if tdef else 0
        check = approvals.check(level, action=f"{tool_name} {json.dumps(args)[:200]}",
                                agent_id="orchestrator", request_id=request_id)
        if not check["approved"]:
            approvals_out.append({**check, "tool": tool_name})
            results.append({"tool": tool_name, "status": "pending_approval",
                            "approval_id": check["approval_id"]})
            continue
        start = time.time()
        out = _dispatch(tool_name, args, business_id)
        results.append({**out, "status": "executed", "lat_ms": int((time.time() - start) * 1000)})
    return {"results": results, "approvals": approvals_out,
            "blocked": any(r.get("status") == "pending_approval" for r in results)}


def _is_mission_request(request):
    text = request.lower()
    return any(k in text for k in _MISSION_KEYWORDS)


def handle_mission(request, business_id=None, request_id=""):
    """Mission-aware path: build a task DAG from the request and execute it.

    Returns a structured response with the mission payload + execution plan.
    """
    start = time.time()
    rid = request_id or f"req-{int(time.time() * 1000)}"

    # Build a mission from the request (goal = request, tasks = empty for now;
    # the caller can add tasks via mission_create with explicit task defs).
    m = mission.create_mission(request[:60], request, owner="Pankaj")
    plan = mission.resolve(m["id"])

    result = {
        "intent": "mission",
        "agent_id": "mission",
        "agent_name": "Mission & Task-Graph",
        "score": 1,
        "blocked": False,
        "approvals": [],
        "results": [{
            "tool": "mission_create",
            "status": "executed",
            "ok": True,
            "mission": mission.mission_payload(m["id"]),
            "execution_plan": plan,
        }],
        "request_id": rid,
        "lat_ms": int((time.time() - start) * 1000),
    }
    audit.record(
        request=request, intent="mission", agent_id="mission",
        tools=["mission_create"], inputs={"request": request}, outputs=result,
        approval={"blocked": False}, success=True, lat_ms=result["lat_ms"],
    )
    return result


def handle(request, business_id=None, request_id=""):
    """Full orchestrator pipeline. Returns a structured response dict."""
    start = time.time()

    # Mission-aware routing: requests mentioning missions/task-graphs go
    # through the mission layer instead of the classic agent pipeline.
    if _is_mission_request(request):
        return handle_mission(request, business_id, request_id)

    agent_id, intent, score = route(request)
    agent = registry.agent_def(agent_id) or {}
    rid = request_id or f"req-{int(time.time() * 1000)}"

    # Agent-level approval gate: L1+ agents pend the whole action before
    # any tool is run (matches HEER human-approval levels).
    gate = approvals.check(
        agent.get("approval_level", 0),
        action=f"{agent_id}: {request[:300]}",
        agent_id=agent_id, request_id=rid,
    )
    if not gate["approved"]:
        result = {
            "intent": intent, "agent_id": agent_id,
            "agent_name": agent.get("name", agent_id), "score": score,
            "blocked": True, "approvals": [{**gate, "agent": agent_id}],
            "results": [], "request_id": rid,
            "lat_ms": int((time.time() - start) * 1000),
        }
        audit.record(
            request=request, intent=intent, agent_id=agent_id,
            tools=[], inputs={"request": request}, outputs=result,
            approval={"blocked": True, "approval_id": gate["approval_id"]},
            success=True, lat_ms=result["lat_ms"],
        )
        return result

    plan_steps = plan(agent_id, request)
    exec_result = execute(plan_steps, business_id, rid)
    ok = exec_result["blocked"] is False
    audit.record(
        request=request, intent=intent, agent_id=agent_id,
        tools=[t for t, _ in plan_steps],
        inputs={"request": request}, outputs=exec_result,
        approval={"blocked": exec_result["blocked"]},
        success=ok, lat_ms=int((time.time() - start) * 1000),
    )
    return {
        "intent": intent,
        "agent_id": agent_id,
        "agent_name": agent.get("name", agent_id),
        "score": score,
        "blocked": exec_result["blocked"],
        "approvals": exec_result["approvals"],
        "results": exec_result["results"],
        "request_id": rid,
        "lat_ms": int((time.time() - start) * 1000),
    }


# ---------------------------------------------------------------------------
# CLI self-test
# ---------------------------------------------------------------------------

def _self_test():
    print("HEER Orchestrator self-test\n" + "-" * 40)
    scenarios = [
        ("Prepare tomorrow's CEO briefing", "ceo", False),
        ("Draft a proposal for Meridian Bank Group", "proposal", True),
        ("Create the GitHub implementation plan for the project", "github", True),
    ]
    passed = True
    for request, expect_agent, expect_blocked in scenarios:
        r = handle(request)
        verdict = "PASS" if (r["agent_id"] == expect_agent and r["blocked"] == expect_blocked) else "FAIL"
        if verdict == "FAIL":
            passed = False
        print(f"[{verdict}] agent={r['agent_id']} blocked={r['blocked']} "
              f"tools={len(r['results'])} request='{request[:50]}'")

    # Mission-aware scenario
    r5 = handle("Create a mission to launch the AI Agency website")
    ok5 = (r5["agent_id"] == "mission" and r5["blocked"] is False
           and r5["results"][0]["tool"] == "mission_create"
           and r5["results"][0]["ok"] is True
           and "mission" in r5["results"][0])
    if not ok5:
        passed = False
    print(f"[{'PASS' if ok5 else 'FAIL'}] mission-aware routing "
          f"agent={r5['agent_id']} mission={r5['results'][0].get('mission', {}).get('id', '?')}")

    print("-" * 40)
    print(f"Result: {'ALL PASS' if passed else 'FAILURES'} "
          f"| pending approvals: {len(approvals.pending_approvals())}")
    return 0 if passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())