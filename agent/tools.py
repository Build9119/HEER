#!/usr/bin/env python3
"""tools.py — HEER unified tool registry (Phase 3.8).

Merges the core vault tools with the Phase-3 module tools:
  mission, developer, github_agent, n8n, deploy, terminal.

Every tool is a callable(name, args, business_id) -> dict. Tools are the
only way HEER acts on the user's behalf. All module tools keep their own
L2/L3 gating; this file is the single dispatch surface.

Run:  python3 -m agent.tools
"""

import datetime as _dt
import json

from .vault import get_vault

# ---------------------------------------------------------------------------
# Core tool implementations
# ---------------------------------------------------------------------------


def tool_search(name, args, business_id=None):
    q = args.get("query") or args.get("q") or ""
    limit = min(int(args.get("limit", 5)), 20)
    v = get_vault(business_id)
    if v is None:
        return {"tool": name, "ok": False, "error": "No vault configured."}
    results = v.search(q, limit=limit)
    return {
        "tool": name,
        "ok": True,
        "results": [
            {
                "title": n["title"],
                "type": n["type"],
                "snippet": n["text"][:300],
            }
            for n in results
        ],
    }


def tool_look(name, args, business_id=None):
    """Full text of a node, by exact title."""
    title = (args.get("title") or args.get("id") or "").strip()
    v = get_vault(business_id)
    if v is None:
        return {"tool": name, "ok": False, "error": "No vault configured."}
    node = v.by_title(title) if title else None
    if not node:
        return {"tool": name, "ok": False, "error": f"No node titled '{title}'."}
    return {
        "tool": name,
        "ok": True,
        "title": node["title"],
        "type": node["type"],
        "rel": node["rel"],
        "text": node["text"],
        "neighbors": [
            v.nodes[n]["title"] for n in v.neighbors(node["id"])
        ],
    }


def tool_clock(name, args, business_id=None):
    now = _dt.datetime.now()
    return {
        "tool": name,
        "ok": True,
        "iso": now.isoformat(timespec="seconds"),
        "date": now.strftime("%A, %d %B %Y"),
        "time": now.strftime("%I:%M %p"),
        "tz": _dt.datetime.now().astimezone().tzinfo or "",
        "unix": int(now.timestamp()),
    }


def tool_echo(name, args, business_id=None):
    return {"tool": name, "ok": True, "echo": args.get("text") or ""}


def tool_remind(name, args, business_id=None):
    """Store a reminder in the notes. Returns the new node id."""
    text = (args.get("text") or "").strip()
    if not text:
        return {"tool": name, "ok": False, "error": "remind needs 'text'."}
    when = args.get("when") or "asap"
    title = args.get("title") or f"Reminder {_dt.datetime.now():%Y-%m-%d %H:%M}"
    body = f"Reminder: {text}\nWhen: {when}\nCreated: {_dt.datetime.now():%Y-%m-%d %H:%M}"
    v = get_vault(business_id)
    if v is None:
        return {"tool": name, "ok": False, "error": "No vault configured."}
    node = v.add_note(title, body)
    return {
        "tool": name,
        "ok": True,
        "title": title,
        "id": node["id"],
        "note": f"Stored in vault as note '{title}'.",
    }


def tool_hubs(name, args, business_id=None):
    limit = min(int(args.get("limit", 5)), 20)
    v = get_vault(business_id)
    if v is None:
        return {"tool": name, "ok": False, "error": "No vault configured."}
    hubs = [
        {"title": v.nodes[nid]["title"], "degree": deg}
        for nid, deg in v.hubs(limit)
    ]
    return {"tool": name, "ok": True, "hubs": hubs}


def tool_stats(name, args, business_id=None):
    v = get_vault(business_id)
    if v is None:
        return {"tool": name, "ok": False, "error": "No vault configured."}
    counts = {}
    for n in v.nodes.values():
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    return {
        "tool": name,
        "ok": True,
        "nodes": len(v.nodes),
        "links": len(v.links),
        "by_type": counts,
    }


# ---------------------------------------------------------------------------
# Core registry
# ---------------------------------------------------------------------------

CORE_TOOLS = {
    "echo": {
        "desc": "Echo text back. Useful for testing.",
        "params": {"text": "string"},
        "fn": tool_echo,
    },
    "clock": {
        "desc": "Current date and time.",
        "params": {},
        "fn": tool_clock,
    },
    "search": {
        "desc": "Search the vault (notes, clients, projects, reports). Returns matching nodes with a snippet.",
        "params": {
            "query": "string — plain text to search for",
            "limit": "int (optional, default 5)",
        },
        "fn": tool_search,
    },
    "look": {
        "desc": "Read the full content of a vault node by title.",
        "params": {"title": "string — exact node title"},
        "fn": tool_look,
    },
    "remind": {
        "desc": "Save a reminder/note into the vault.",
        "params": {
            "text": "string — what to remember",
            "when": "string (optional) — when it's due",
            "title": "string (optional) — node title",
        },
        "fn": tool_remind,
    },
    "hubs": {
        "desc": "Top connected nodes in the vault. Good when the user asks 'what's most important?'",
        "params": {"limit": "int (optional, default 5)"},
        "fn": tool_hubs,
    },
    "stats": {
        "desc": "Vault size and type counts.",
        "params": {},
        "fn": tool_stats,
    },
}


# ---------------------------------------------------------------------------
# Phase-3 module tool merge
# ---------------------------------------------------------------------------

_MODULE_TOOLS = {}


def _register(module_name, tools_dict):
    """Merge a module's tool registry into the unified surface."""
    if not tools_dict:
        return
    for tname, spec in tools_dict.items():
        full = f"{module_name}_{tname}"
        _MODULE_TOOLS[full] = {
            "desc": spec.get("desc", ""),
            "params": spec.get("params", {}),
            "fn": spec.get("fn"),
            "module": module_name,
        }


try:
    from .mission import MISSION_TOOLS
    _register("mission", MISSION_TOOLS)
except Exception:
    pass

try:
    from .developer import DEVELOPER_TOOLS
    _register("developer", DEVELOPER_TOOLS)
except Exception:
    pass

try:
    from .github_agent import GITHUB_TOOLS
    _register("github", GITHUB_TOOLS)
except Exception:
    pass

try:
    from .n8n import N8N_TOOLS
    _register("n8n", N8N_TOOLS)
except Exception:
    pass

try:
    from .deploy import DEPLOY_TOOLS
    _register("deploy", DEPLOY_TOOLS)
except Exception:
    pass

try:
    from .terminal import TERMINAL_TOOLS
    _register("terminal", TERMINAL_TOOLS)
except Exception:
    pass

TOOLS = {**CORE_TOOLS, **_MODULE_TOOLS}


def call_tool(name, args=None, business_id=None):
    """Safely invoke a tool by name (core or module)."""
    args = args or {}
    t = TOOLS.get(name)
    if not t:
        return {"tool": name, "ok": False, "error": f"Unknown tool '{name}'."}
    try:
        return t["fn"](name, args, business_id)
    except Exception as e:  # never let a tool crash the conversation
        return {"tool": name, "ok": False, "error": f"Tool error: {e}"}


def tool_descriptions():
    return [
        {"name": name, "desc": t["desc"], "params": t["params"],
         "module": t.get("module", "core")}
        for name, t in TOOLS.items()
    ]


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 -m agent.tools <tool> [json-args]")
        print("Tools: " + ", ".join(sorted(TOOLS)))
        return
    name = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    print(json.dumps(call_tool(name, args), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()