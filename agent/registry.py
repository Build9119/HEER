#!/usr/bin/env python3
"""registry.py — HEER Agent & Tool Registries (Phase 1, compact).

Operational layer for agent/orchestrator.py. The 15 fixture agents in
heer.py are untouched; this is the executable agent registry.
"""

# Approval levels: 0=Read 1=Prepare 2=Execute 3=Critical
APPROVAL_NAMES = {0: "READ", 1: "PREPARE", 2: "EXECUTE", 3: "CRITICAL"}

# Compact tool registry: name -> (risk, approval_level, enabled)
TOOL_REGISTRY = {
    "echo": ("none", 0, True), "clock": ("none", 0, True),
    "search": ("low", 0, True), "look": ("low", 0, True),
    "remind": ("low", 1, True), "hubs": ("low", 0, True),
    "stats": ("low", 0, True),
    "briefing": ("low", 0, True), "clients": ("low", 0, True),
    "projects": ("low", 0, True), "business_intel": ("low", 0, True),
    "opportunities": ("low", 0, True), "skills_payload": ("low", 0, True),
    "learning_payload": ("low", 0, True), "activity_payload": ("low", 0, True),
    "network_payload": ("low", 0, True), "automations_payload": ("low", 0, True),
    "status_payload": ("low", 0, True),
    # Phase 3 — Execution tools (registered disabled until wired; enabled
    # in Phase 3.8 after tool handlers exist)
    "code_read": ("low", 0, False),
    "code_write": ("medium", 1, False),
    "test_run": ("medium", 1, False),
    "github_read": ("low", 0, False),
    "github_write": ("medium", 2, False),
    "docker": ("high", 2, False),
    "n8n": ("medium", 2, False),
    "terminal_exec": ("critical", 3, False),
    # Phase 2 — AI Agency Core (for future wiring)
    "web_search": ("low", 0, False), "proposal_draft": ("low", 1, False),
    "roi_calc": ("low", 0, False), "crm_read": ("low", 0, False),
    "crm_write": ("medium", 2, False),
}

def tool_def(name):
    r, a, e = TOOL_REGISTRY.get(name, (None, None, False))
    return {"name": name, "risk_level": r, "approval_level": a, "enabled": e}

def enabled_tools():
    return {k for k, v in TOOL_REGISTRY.items() if v[2]}

def tools_for_agent(agent_id):
    a = AGENT_REGISTRY.get(agent_id)
    if a is None:
        return {}
    # tuple layout: (name, role, approval_level, autonomy, tools, intents)
    return {t: tool_def(t) for t in a[4] if t in TOOL_REGISTRY and TOOL_REGISTRY[t][2]}

# Agent registry: id -> (name, role, approval_level, autonomy, tools, intents)
AGENT_REGISTRY = {
    "ceo": ("CEO / Strategy Agent", "STRATEGY", 0, 2,
            ["briefing", "business_intel", "clients", "projects", "opportunities", "search"],
            ["strategy", "strategic", "priority", "okr", "growth", "positioning", "briefing",
             "executive", "business model", "verticals should we target", "next quarter",
             "which vertical", "which industry", "target this quarter"]),
    "sales": ("AI Agency Sales Agent", "SALES", 1, 2,
              ["opportunities", "clients", "search", "look"],
              ["lead", "leads", "prospect", "target account", "icp", "qualification",
               "outreach", "pipeline", "opportunit", "won", "lost", "sales",
               "manufacturing companies", "find companies", "decision maker"]),
    "discovery": ("AI Discovery / Consulting Agent", "CONSULTING", 0, 2,
                  ["clients", "projects", "search", "look", "opportunities"],
                  ["discovery", "consult", "process", "pain point", "current state",
                   "opportunity discovery", "transformation", "roadmap", "assess"]),
    "architect": ("AI Solution Architect", "ARCHITECT", 0, 1,
                  ["search", "look", "projects"],
                  ["architecture", "solution design", "rag", "model selection", "integration",
                   "langgraph", "crewai", "mcp", "vector database", "cost optimization"]),
    "proposal": ("Proposal Agent", "PROPOSAL", 1, 2,
                 ["clients", "projects", "opportunities", "business_intel"],
                 ["proposal", "sow", "statement of work", "scope document", "pricing",
                  "executive summary", "quote", "draft proposal"]),
    "roi": ("ROI / Business Case Agent", "FINANCE-ROI", 0, 1,
            ["business_intel", "projects", "opportunities"],
            ["roi", "business case", "payback", "annual savings", "profitability",
             "cost savings", "margin", "recurring revenue", "automation savings"]),
    "developer": ("Developer Agent", "ENGINEERING", 1, 2,
                  ["search", "look", "projects", "code_read", "code_write", "test_run"],
                  ["write code", "code", "debug", "refactor", "implement", "build the",
                   "develop the", "script", "function", "fix the"]),
    "automation": ("Automation Agent", "AUTOMATION", 1, 2,
                   ["search", "look", "automations_payload", "n8n"],
                   ["automation", "workflow", "n8n", "webhook", "scheduled job",
                    "integration", "sync", "trigger"]),
    "github": ("GitHub / Engineering Agent", "ENGINEERING-OPS", 2, 2,
               ["search", "look", "github_read", "github_write"],
               ["github", "repository", "repo", "pull request", "pr", "issue",
                "branch", "ci/cd", "merge", "implementation plan", "create the github"]),
    "devops": ("DevOps / Deployment Agent", "ENGINEERING-OPS", 2, 2,
               ["search", "look", "docker", "terminal_exec"],
               ["deploy", "deployment", "devops", "pipeline", "ci", "container",
                "docker", "kubernetes", "build the image", "rollback", "release"]),
    "qa": ("QA / Testing Agent", "ENGINEERING-QA", 1, 2,
           ["search", "look", "test_run"],
           ["test", "testing", "qa", "regression", "smoke test", "quality gate",
            "verify", "validate the build", "run the tests"]),
    "delivery": ("Project Delivery Agent", "DELIVERY", 1, 3,
                 ["projects", "clients", "activity_payload"],
                 ["project status", "project", "milestone", "delivery", "at risk",
                  "blocker", "deadline", "uat", "handover", "risk", "deliverable"]),
    "finance": ("Finance Agent", "FINANCE", 0, 1,
                ["business_intel", "projects", "opportunities"],
                ["revenue", "pipeline value", "mrr", "arr", "cloud cost", "api cost",
                 "profit", "margin", "losing money", "profitability", "cost", "finance"]),
    "marketing": ("Marketing Agent", "MARKETING", 1, 2,
                  ["clients", "projects", "search", "look"],
                  ["linkedin", "content", "case study", "marketing", "campaign",
                   "landing page", "lead magnet", "webinar", "demo script"]),
    "governance": ("AI Governance Agent", "GOVERNANCE", 3, 4,
                   ["skills_payload", "learning_payload", "search", "look"],
                   ["governance", "ai inventory", "risk assessment", "policy", "control",
                    "incident", "compliance", "audit evidence", "42001", "soc 2",
                    "prompt injection", "human oversight"]),
}

# Unmatched requests fall back to the CEO agent: L0 (read-only), so unknown
# questions auto-execute a harmless executive read rather than pending.
DEFAULT_AGENT = "ceo"

def agent_def(agent_id):
    a = AGENT_REGISTRY.get(agent_id)
    if a is None:
        return None
    return {
        "id": agent_id, "name": a[0], "role": a[1],
        "approval_level": a[2], "autonomy": a[3],
        "tools": list(a[4]),
        "intents": list(a[5]),
        "status": "active",
    }

def all_agents():
    """All registered agents as payload dicts (never None — keys are valid)."""
    out = []
    for agent_id, t in AGENT_REGISTRY.items():
        out.append({
            "id": agent_id, "name": t[0], "role": t[1],
            "approval_level": t[2], "autonomy": t[3],
            "tools": list(t[4]), "intents": list(t[5]),
            "status": "active",
        })
    return out

def agents_payload():
    reg = all_agents()
    return {
        "agents": reg,
        "autonomy_levels": [
            {"level": 0, "name": "OBSERVE"}, {"level": 1, "name": "RECOMMEND"},
            {"level": 2, "name": "ASSIST"}, {"level": 3, "name": "EXECUTE"},
            {"level": 4, "name": "AUTONOMOUS"}, {"level": 5, "name": "ADAPTIVE"},
        ],
        "active_count": sum(1 for a in reg if a["status"] == "active"),
        "total": len(reg),
    }

def registry_payload():
    return {
        "agents": all_agents(),
        "tools": {k: {"risk_level": v[0], "approval_level": v[1], "enabled": v[2]}
                  for k, v in TOOL_REGISTRY.items()},
    }