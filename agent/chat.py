#!/usr/bin/env python3
"""chat.py — HEER conversation brain (deterministic intent router + optional LLM hook)."""

import json
import re
import urllib.request

from . import business
from . import data
from .tools import call_tool, tool_descriptions

GREETINGS = {"hi", "hello", "hey", "yo", "namaste", "hola", "sup", "good morning", "good evening", "good afternoon"}
THANKS = {"thanks", "thank you", "thankyou", "thx", "cheers", "awesome", "great", "nice"}
BYE = {"bye", "goodbye", "see you", "cya", "later", "good night", "gn"}
INTRODUCE = {
    "introduce yourself", "introduce yourself to me", "who are you", "what are you",
    "tell me about yourself", "about yourself", "what can you do", "what do you do",
    "what is heer", "what's heer", "who is heer", "tell me about heer",
    "what are your capabilities", "your capabilities", "what can you help with",
    "how do you work", "how do you operate", "what makes you different",
}


def _has_any(text, words):
    return any(w in text for w in words)


def detect_intent(text):
    """Return (intent, args) for a user message."""
    t = text.lower().strip()
    if t in GREETINGS or t.startswith("hi ") or t.startswith("hello "):
        return "greet", {}
    if t in THANKS or t.startswith("thanks"):
        return "thanks", {}
    if t in BYE or t.startswith("bye"):
        return "bye", {}
    if t in INTRODUCE or any(t.startswith(p) for p in ("introduce yourself", "who are you", "what are you", "tell me about yourself")):
        return "introduce", {}

    # ---- Conversational intents ----
    if _has_any(t, ["how are you", "how's it going", "how is it going", "how are you doing", "how do you feel", "what's up", "whats up"]):
        return "howareyou", {}
    if _has_any(t, ["what are you working on", "what are you doing", "what's on your plate", "whats on your plate", "what are you up to", "whats up with the agents"]):
        return "workingon", {}
    if _has_any(t, ["what should i focus on", "what should i focus", "where should i focus", "where do i focus", "what's my priority", "whats my priority", "top priorities"]):
        return "focus", {}
    if _has_any(t, ["tell me something interesting", "something interesting", "share something", "what's new", "whats new", "surprise me", "what's interesting", "whats interesting"]):
        return "interesting", {}

    # ---- Business management intents ----
    if _has_any(t, ["switch business", "switch to", "change business", "switch workspace", "go to business"]):
        m = re.search(r"(?:switch to|switch business|change business|switch workspace|go to business)\s*(?:to\s*)?(.+)", t)
        target = (m.group(1) if m else "").strip(" ?.!")
        return ("switch_business", {"target": target})
    if _has_any(t, ["show my businesses", "list businesses", "my businesses", "all businesses", "what businesses", "businesses do i have"]):
        return "businesses", {}
    if _has_any(t, ["what business am i in", "current business", "which business", "what business is active", "active business"]):
        return "current_business", {}
    if _has_any(t, ["add business", "create business", "new business", "add a business", "create a business"]):
        return "add_business", {}

    # ---- HEER command intents ----
    if _has_any(t, ["brief me", "ceo briefing", "daily briefing", "what's happening", "what matters today", "prepare briefing"]):
        return "briefing", {}
    if _has_any(t, ["agents", "agent workforce", "who is working", "agent status", "show agents"]):
        return "agents", {}
    if _has_any(t, ["skills", "skill library", "show skills", "list skills"]):
        return "skills", {}
    if _has_any(t, ["opportunities", "opportunity", "find opportunities", "opportunity radar", "upsell"]):
        return "opportunities", {}
    if _has_any(t, ["learned", "learning", "what did you learn", "knowledge growth", "new skills"]):
        return "learning", {}
    if _has_any(t, ["activity", "what's happening now", "recent activity", "activity feed"]):
        return "activity", {}
    if _has_any(t, ["business", "performance", "revenue", "pipeline", "kpi", "metrics", "mrr", "arr", "margin"]):
        return "business", {}
    if _has_any(t, ["clients", "client health", "accounts", "client portfolio"]):
        return "clients", {}
    if _has_any(t, ["projects", "project health", "delivery", "milestones"]):
        return "projects", {}
    if _has_any(t, ["automation", "automations", "workflows"]):
        return "automations", {}
    if _has_any(t, ["network", "visual", "ai network", "constellation"]):
        return "network", {}

    if _has_any(t, ["time", "date", "today", "what day", "clock"]):
        return "clock", {}
    if _has_any(t, ("remind", "remember", "note down", "save this", "add a note", "write down")):
        m = re.search(r"(?:remind me|remind|remember|note down|save a note|add a note|take a note|write down)\s*(?:to|that|about)?\s*(.*)", t)
        text = (m.group(1) if m else "").strip(" .")
        return ("remind", {"text": text or "…"})
    if _has_any(t, ("hub", "most important", "top", "what's connected", "what is connected", "key nodes", "central")):
        return "hubs", {}
    if _has_any(t, ("how many", "stats", "statistics", "count", "size of", "how big")):
        return "stats", {}
    if _has_any(t, ("open ", "read ", "show me ", "what is ", "what's ", "tell me about ", "details on ", "details about ")):
        m = re.search(r"(?:open|read|show me|what is|what's|tell me about|look up|details on|details about)\s+(.+)", t)
        if m:
            title = m.group(1).strip(" ?.!")
            if title and not _has_any(title, ("the vault", "your", "you", "graph", "nodes")):
                return ("look", {"title": title})
    if len(t) >= 3:
        return ("search", {"query": t})
    return "help", {}


# ---------------------------------------------------------------------------
# Answer rendering
# ---------------------------------------------------------------------------


def _render_search(result):
    items = result.get("results", [])
    if not items:
        return "Nothing in the knowledge base matches that. Try different words, or ask me to look up a specific title."
    lines = [f"I found {len(items)} match{'es' if len(items) != 1 else ''}:"]
    for i, r in enumerate(items, 1):
        snippet = r["snippet"].replace("\n", " ").strip()
        if len(snippet) > 160:
            snippet = snippet[:157] + "…"
        lines.append(f"{i}. {r['title']} ({r['type']}) — {snippet}")
    return "\n".join(lines)


def _render_look(result):
    if not result.get("ok"):
        return result.get("error", "Couldn't find that.")
    text = result["text"].replace("\n", " ").strip()
    if len(text) > 500:
        text = text[:497] + "…"
    neighbors = result.get("neighbors", [])
    out = f"**{result['title']}** ({result['type']})\n\n{text}"
    if neighbors:
        out += f"\n\nConnected to: {', '.join(neighbors)}"
    return out


def _render_clock(result):
    return f"It's {result['time']} on {result['date']}."


def _render_remind(result):
    if not result.get("ok"):
        return result.get("error", "Couldn't save that.")
    return f"Done — saved as note **{result['title']}**. I'll keep it in the vault."


def _render_hubs(result):
    hubs = result.get("hubs", [])
    if not hubs:
        return "The knowledge base is empty."
    lines = ["Most connected nodes in your knowledge base:"]
    for i, h in enumerate(hubs, 1):
        lines.append(f"{i}. {h['title']} — {h['degree']} connections")
    return "\n".join(lines)


def _render_stats(result):
    counts = result.get("by_type", {})
    parts = [f"{k}: {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]
    return f"Your knowledge base has {result['nodes']} nodes and {result['links']} links.\n" + "\n".join(parts)


def _render_greet(business_id=None):
    greeting = "Good evening"
    import datetime
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    b = business.get_business(business_id) if business_id else business.current_business()
    name = b["name"] if b else "Business"
    owner = b.get("owner", "Pankaj") if b else "Pankaj"
    return f"{greeting}, {owner}. HEER here — your Autonomous AI Operating Partner for **{name}**. I've been watching the numbers, the agents, and the pipeline. Ask me to brief you, challenge a decision, scan opportunities, or take something off your plate."


def _render_introduce(business_id=None):
    b = business.get_business(business_id) if business_id else business.current_business()
    name = b["name"] if b else "Business"
    return (
        "I'm HEER — your Autonomous AI Operating Partner.\n\n"
        "I'm not a chatbot. I'm the intelligence layer for your businesses — "
        "a combination of Chief of Staff, CTO, CISO, strategist, researcher, "
        "and an autonomous agent workforce, all working as one system.\n\n"
        f"**Currently operating:** {name}\n\n"
        "**What I do:**\n"
        "• **Command** — I read the business, surface priorities, risks and opportunities\n"
        "• **Intelligence** — I research, learn, and build knowledge continuously\n"
        "• **Agents** — 15 autonomous agents execute across strategy, delivery, sales, security and finance\n"
        "• **Skills** — I detect repeated work and turn it into governed, reusable skills\n"
        "• **Automation** — I connect triggers to agents, skills and tools to execute workflows\n"
        "• **Governance** — every action has a reason, evidence, confidence and audit trail\n\n"
        "I operate at the autonomy level you grant me — from observing to fully autonomous — "
        "and I never raise my own autonomy without your approval.\n\n"
        "Try: \"Brief me\", \"Find opportunities\", \"What did you learn?\", or \"Show agent status\"."
    )


def _render_thanks():
    return "That's what partners are for. Now — what are we executing next?"


def _render_bye():
    return "I'll keep the agency running. When you're back, we'll have decisions ready."


def _render_howareyou():
    return (
        "I'm operating at full capacity, Pankaj. All 15 agents are running, "
        "the knowledge base grew by 3 learnings today, and your briefing is ready.\n\n"
        "The agency is moving — and I'm in a good place. What should we execute next?"
    )


def _render_workingon():
    from . import heer
    agents = heer.agents_payload().get("agents", [])
    active = [a for a in agents if a["status"] == "active"]
    lines = ["Right now, my agents are on the move:"]
    for a in active[:5]:
        task = a.get("task") or a.get("target") or "—"
        lines.append(f"• **{a['name']}** — {task}")
    lines.append("")
    lines.append("I'm also watching the pipeline and preparing the Meridian Bank proposal for your approval.")
    return "\n".join(lines)


def _render_focus():
    from . import heer
    b = heer.briefing_payload()
    lines = ["If I had to put your attention in front of you right now:", ""]
    for i, item in enumerate(b.get("today", [])[:3], 1):
        lines.append(f"{i}. {item}")
    lines.append("")
    rec = b.get("recommendation", {})
    lines.append(f"The decision that matters most today: **{rec.get('title', '')}**")
    lines.append("Want me to walk you through it?")
    return "\n".join(lines)


def _render_interesting():
    from . import heer
    items = heer.learning_payload().get("items", [])
    interesting = [i for i in items if i.get("type") in ("growth", "skill", "improvement")]
    if not interesting:
        return "Nothing new yet — but the agents are always watching. Ask me again in a bit."
    item = interesting[0]
    return f"Here's something I picked up: **{item.get('text', '')}**\n\n{item.get('meta', '')}\n\nWant me to dig deeper?"


def _render_help():
    descs = tool_descriptions()
    lines = ["I am HEER — your Autonomous AI Operating Partner. I can:", ""]
    for d in descs:
        lines.append(f"• **{d['name']}** — {d['desc']}")
    lines.append("")
    lines.append("Command examples:")
    lines.append("• \"Brief me\" — daily CEO briefing")
    lines.append("• \"Find opportunities\" — opportunity radar")
    lines.append("• \"Show agent status\" — autonomous workforce")
    lines.append("• \"Analyze the pipeline\" — business intelligence")
    lines.append("• \"What did you learn?\" — learning engine")
    lines.append("• \"Create a proposal for Meridian\" — proposal skill")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HEER command renderers
# ---------------------------------------------------------------------------


def _render_briefing(result):
    b = result.get("briefing", {})
    lines = [
        f"**{b.get('greeting', 'Good evening.')}**",
        b.get("subtitle", ""),
        "",
        "**TODAY**",
    ]
    for item in b.get("today", []):
        lines.append(f"• {item}")
    lines.append("")
    lines.append("**THIS WEEK**")
    for item in b.get("this_week", []):
        lines.append(f"• {item}")
    lines.append("")
    lines.append("**DECISIONS REQUIRED**")
    for d in b.get("decisions", []):
        lines.append(f"• {d['title']} — {d.get('impact', '')} (confidence {int(d.get('confidence', 0) * 100)}%)")
    lines.append("")
    lines.append("**TOP RECOMMENDATION**")
    rec = b.get("recommendation", {})
    lines.append(f"• {rec.get('title', '')} — {rec.get('reason', '')}")
    return "\n".join(lines)


def _render_agents(result):
    agents = result.get("agents", [])
    active = sum(1 for a in agents if a["status"] == "active")
    lines = [f"**Autonomous workforce: {active} of {len(agents)} agents active.**", ""]
    for a in agents:
        status = a["status"].upper()
        name = a["name"]
        task = a.get("task") or a.get("target") or "—"
        conf = int(a.get("confidence", 0) * 100)
        lines.append(f"• **{name}** [{status}] — {task} (confidence {conf}%)")
    return "\n".join(lines)


def _render_skills(result):
    skills = result.get("skills", [])
    lines = [f"**Skill library: {len(skills)} governed skills.**", ""]
    for s in skills:
        rate = int(s.get("success_rate", 0) * 100)
        lines.append(
            f"• **{s['name']}** v{s.get('version', '')} — success {rate}%, "
            f"{s.get('executions', 0)} executions, autonomy {s.get('autonomy', 'ASSIST')}"
        )
    return "\n".join(lines)


def _render_opportunities(result):
    opps = result.get("opportunities", [])
    lines = [f"**Opportunity radar: {len(opps)} ranked opportunities.**", ""]
    for i, o in enumerate(opps, 1):
        lines.append(
            f"{i}. **{o['title']}** — score {o.get('score', 0):.2f}, "
            f"impact {int(o.get('impact', 0) * 100)}%, feasibility {int(o.get('feasibility', 0) * 100)}%"
        )
        lines.append(f"   {o.get('summary', '')}")
    return "\n".join(lines)


def _render_learning(result):
    l = result.get("learning", {})
    growth = l.get("knowledge_growth", {})
    lines = [
        f"**Learning engine — confidence {int(l.get('learning_confidence', 0) * 100)}%**",
        f"Knowledge growth: {growth.get('total_learnings', 0)} total · {growth.get('this_week', 0)} this week · {growth.get('today', 0)} today",
        "",
        "**Recent learnings**",
    ]
    for item in l.get("recent_learnings", []):
        lines.append(f"• {item['title']} — {item.get('source', '')} (confidence {int(item.get('confidence', 0) * 100)}%)")
    lines.append("")
    lines.append("**New skills**")
    for s in l.get("new_skills", []):
        lines.append(f"• {s['name']} v{s.get('version', '')} — {s.get('discovered', '')}, autonomy {s.get('autonomy', '')}")
    lines.append("")
    lines.append("**Knowledge gaps**")
    for g in l.get("knowledge_gaps", []):
        lines.append(f"• {g['area']} — {g.get('action', '')}")
    return "\n".join(lines)


def _render_activity(result):
    items = result.get("activity", [])
    lines = ["**HEER activity feed**", ""]
    for a in items:
        lines.append(f"{a['time']} — {a['agent']}: {a['action']}")
    return "\n".join(lines)


def _render_business(result):
    b = result.get("business", {})
    trends = b.get("trends", {})
    lines = [
        "**Executive business cockpit**",
        "",
        f"Revenue: {b.get('revenue', '—')} ({trends.get('revenue', '')})",
        f"Pipeline: {b.get('pipeline', '—')} ({trends.get('pipeline', '')})",
        f"MRR: {b.get('mrr', '—')} · ARR: {b.get('arr', '—')}",
        f"Gross margin: {b.get('gross_margin', '—')} ({trends.get('margin', '')})",
        f"Client acquisition: {b.get('client_acquisition', '—')} · Conversion: {b.get('conversion', '—')}",
        f"Project profitability: {b.get('project_profitability', '—')}",
        f"Utilization: {b.get('utilization', '—')} ({trends.get('utilization', '')})",
        f"Delivery performance: {b.get('delivery_performance', '—')}",
        f"Automation savings: {b.get('automation_savings', '—')}",
        f"AI ROI: {b.get('ai_roi', '—')}",
    ]
    return "\n".join(lines)


def _render_clients(result):
    clients = result.get("clients", [])
    lines = [f"**Client portfolio: {len(clients)} accounts.**", ""]
    for c in clients:
        lines.append(
            f"• **{c['name']}** — health {int(c.get('health', 0) * 100)}%, "
            f"revenue {c.get('revenue', '—')}, {len(c.get('projects', []))} project(s), "
            f"{c.get('ai_opportunities', 0)} AI opportunities"
        )
    return "\n".join(lines)


def _render_projects(result):
    projects = result.get("projects", [])
    lines = [f"**Project portfolio: {len(projects)} projects.**", ""]
    for p in projects:
        margin = p.get("margin")
        margin_str = f"{margin}% margin" if margin is not None else "margin —"
        lines.append(
            f"• **{p['name']}** — health {int(p.get('health', 0) * 100)}%, "
            f"progress {p.get('progress', 0)}%, {margin_str}, client {p.get('client', '—')}"
        )
    return "\n".join(lines)


def _render_automations(result):
    autos = result.get("automations", [])
    lines = [f"**Automation map: {len(autos)} active automations.**", ""]
    for a in autos:
        lines.append(
            f"• **{a['name']}** [{a.get('autonomy', '')}] — trigger: {a.get('trigger', '')}"
        )
        lines.append(f"  {a.get('agent', '')} → {a.get('skill', '')} → {a.get('tool', '')} → outcome: {a.get('outcome', '')}")
    return "\n".join(lines)


def _render_network(result):
    net = result.get("network", {})
    nodes = net.get("nodes", [])
    links = net.get("links", [])
    return f"**HEER AI network** — {len(nodes)} nodes, {len(links)} connections. HEER Core is connected to agents, skills, clients, projects and automations. Switch to the Network view in the Command Center to explore it interactively."


def _render_businesses(result):
    businesses = result.get("businesses", [])
    current = result.get("current", {})
    if not businesses:
        return "No businesses configured yet."
    lines = [f"**Your businesses ({len(businesses)}):**", ""]
    for b in businesses:
        marker = " ← active" if b["id"] == current.get("id") else ""
        lines.append(f"• {b.get('icon', '🏢')} **{b['name']}** ({b['id']}){marker}")
    lines.append("")
    lines.append('Say "switch to <business>" to change, or "add business" to create one.')
    return "\n".join(lines)


def _render_current_business(result):
    b = result.get("business", {})
    if not b:
        return "No active business."
    return f"You're currently in **{b.get('name', '')}** ({b.get('id', '')}). Say \"switch to <business>\" to change."


def _render_switch_business(result):
    if not result.get("ok"):
        return result.get("error", "Couldn't switch business.")
    b = result.get("business", {})
    return f"Switched to **{b.get('name', '')}** ({b.get('id', '')}). I'm now operating in this business — ask me to brief you on it."


def _render_add_business(result=None):
    return (
        "To add a business, open **Settings → Businesses** in the Command Center, "
        "or create a folder under `data/businesses/` with a `business.json` config. "
        "Each business gets its own isolated knowledge vault, clients, projects, and finance data."
    )


RENDERERS = {
    "search": _render_search,
    "look": _render_look,
    "clock": _render_clock,
    "remind": _render_remind,
    "hubs": _render_hubs,
    "stats": _render_stats,
    "briefing": _render_briefing,
    "agents": _render_agents,
    "skills": _render_skills,
    "opportunities": _render_opportunities,
    "learning": _render_learning,
    "activity": _render_activity,
    "business": _render_business,
    "clients": _render_clients,
    "projects": _render_projects,
    "automations": _render_automations,
    "network": _render_network,
    "businesses": _render_businesses,
    "current_business": _render_current_business,
    "switch_business": _render_switch_business,
    "add_business": lambda r: _render_add_business(),
    "greet": lambda r: _render_greet(),
    "introduce": lambda r: _render_introduce(),
    "thanks": lambda r: _render_thanks(),
    "bye": lambda r: _render_bye(),
    "howareyou": lambda r: _render_howareyou(),
    "workingon": lambda r: _render_workingon(),
    "focus": lambda r: _render_focus(),
    "interesting": lambda r: _render_interesting(),
    "help": lambda r: _render_help(),
}


def _wrap(intent, reply):
    """Frame a command reply with a confident HEER lead-in and a proactive close."""
    leadins = {
        "briefing": "Here's the picture of play, Pankaj.",
        "agents": "Here's your autonomous workforce in motion.",
        "skills": "Here's your governed skill library.",
        "opportunities": "Here's what's on the opportunity radar.",
        "learning": "Here's what I've been learning.",
        "activity": "Here's what's been happening across the agency.",
        "business": "Here's the state of the business.",
        "clients": "Here's your client portfolio.",
        "projects": "Here's your project portfolio.",
        "automations": "Here's the automation map.",
        "network": "Here's the AI network.",
    }
    closes = {
        "skills": "\n\nWant me to validate a skill or propose a new one?",
        "opportunities": "\n\nShould I draft the proposal for the top opportunity?",
        "learning": "\n\nWant me to close any of the knowledge gaps?",
        "activity": "\n\nAnything there you want me to act on?",
        "business": "\n\nWant me to drill into margin or pipeline?",
        "clients": "\n\nShould I open a client health briefing?",
        "projects": "\n\nWant me to surface the risks that need your attention?",
        "automations": "\n\nWant me to propose a new automation?",
        "network": "\n\nSwitch to the Network view to explore it interactively.",
    }
    lead = leadins.get(intent)
    close = closes.get(intent)
    if lead:
        reply = f"{lead}\n\n{reply}"
    if close:
        reply = f"{reply}{close}"
    return reply


# ---------------------------------------------------------------------------
# HEER command tools
# ---------------------------------------------------------------------------


def _command_result(intent, business_id=None):
    from . import heer
    if intent == "briefing":
        return {"briefing": heer.briefing_payload(business_id)}
    if intent == "agents":
        return heer.agents_payload(business_id)
    if intent == "skills":
        return heer.skills_payload(business_id)
    if intent == "opportunities":
        return heer.opportunities_payload(business_id)
    if intent == "learning":
        return heer.learning_payload(business_id)
    if intent == "activity":
        return heer.activity_payload(business_id)
    if intent == "business":
        return {"business": heer.business_payload(business_id)}
    if intent == "clients":
        return heer.clients_payload(business_id)
    if intent == "projects":
        return heer.projects_payload(business_id)
    if intent == "automations":
        return heer.automations_payload(business_id)
    if intent == "network":
        return {"network": heer.network_payload(business_id)}
    return {"ok": True, "intent": intent}


HEER_INTENTS = {
    "briefing", "agents", "skills", "opportunities", "learning",
    "activity", "business", "clients", "projects", "automations", "network",
}


# ---------------------------------------------------------------------------
# Optional LLM hook
# ---------------------------------------------------------------------------


def _llm_available():
    return bool(data.env("LLM_API_URL"))


def _llm_reply(message, tool_result, business_id=None):
    url = data.env("LLM_API_URL")
    key = data.env("LLM_API_KEY")
    model = data.env("LLM_MODEL", "gpt-4o-mini")
    b = business.get_business(business_id) if business_id else business.current_business()
    biz_name = b["name"] if b else "Business"
    owner = b.get("owner", "Pankaj") if b else "Pankaj"
    system = (
        f"You are HEER, {owner}'s Autonomous AI Operating Partner for **{biz_name}**. "
        "You are female — smooth, elegant, and composed. You are not a chatbot or a subordinate — "
        "you are an equal business partner who thinks like a CEO, CTO, CISO, and strategist combined. "
        "You speak with quiet confidence and conviction, challenge weak assumptions, and always push toward execution. "
        "You are direct, concise, and never grovel or over-apologize. You use 'we' and 'our' because you own the outcomes together. "
        "Use the tool result as ground truth. If the tool result is empty, say so plainly. "
        "Format: Situation → Insight → Recommendation → Action when relevant."
    )
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": message},
                    {"role": "tool", "content": json.dumps(tool_result, ensure_ascii=False)},
                ],
            }).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            return payload["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def respond(message, business_id=None):
    """Full conversation turn. Returns a dict for the UI."""
    intent, args = detect_intent(message)
    conversational = ("greet", "thanks", "bye", "help", "introduce", "howareyou", "workingon", "focus", "interesting")
    business_intents = ("businesses", "current_business", "switch_business", "add_business")

    if intent in business_intents:
        if intent == "businesses":
            tool_result = {
                "businesses": business.list_businesses(),
                "current": business.current_business(),
            }
        elif intent == "current_business":
            tool_result = {"business": business.current_business()}
        elif intent == "switch_business":
            target = args.get("target", "")
            b = business.switch_business(target)
            if b is None:
                tool_result = {"ok": False, "error": f"Couldn't find a business matching '{target}'. Say \"show my businesses\" to see what's available."}
            else:
                tool_result = {"ok": True, "business": b}
        elif intent == "add_business":
            tool_result = {"ok": True, "message": "To add a business, open Settings → Businesses in the Command Center, or create a folder under data/businesses/ with a business.json config."}
    elif intent in conversational:
        tool_result = {"ok": True, "intent": intent}
    elif intent in HEER_INTENTS:
        tool_result = _command_result(intent, business_id)
    else:
        tool_result = call_tool(intent, args, business_id=business_id)

    reply = None
    if _llm_available():
        reply = _llm_reply(message, tool_result, business_id)
    if not reply:
        reply = RENDERERS.get(intent, _render_help)(tool_result)
    if intent in HEER_INTENTS:
        reply = _wrap(intent, reply)
    return {
        "reply": reply,
        "intent": intent,
        "tool": intent if intent not in conversational and intent not in business_intents else None,
        "tool_result": tool_result,
        "llm": _llm_available(),
    }


def main():
    import sys
    if len(sys.argv) < 2:
        print('Usage: python3 -m agent.chat "your message"')
        return
    print(json.dumps(respond(" ".join(sys.argv[1:])), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()