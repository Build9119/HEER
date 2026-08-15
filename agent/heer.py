#!/usr/bin/env python3
"""heer.py — HEER Autonomous AI Agency Operating System.

Intelligence layer: agent workforce, skill library, learning engine,
executive briefing, opportunity radar, activity feed, client/project
intelligence, and automation map. All data is derived from the vault
(demo fixtures in demo mode) so HEER feels alive with real context.

Run:  python3 -m agent.heer
"""

import datetime as _dt
import json
import os
import re

from . import business
from . import data
from . import jarvis_skills
from . import vault

# ---------------------------------------------------------------------------
# Vault (per-business, cached)
# ---------------------------------------------------------------------------


def get_vault(business_id=None):
    """The active business's vault (or a specific business's vault)."""
    return vault.get_vault(business_id)


# ---------------------------------------------------------------------------
# Autonomy levels
# ---------------------------------------------------------------------------

AUTONOMY_LEVELS = [
    {"level": 0, "name": "OBSERVE", "desc": "Only monitor."},
    {"level": 1, "name": "RECOMMEND", "desc": "Analyze and recommend."},
    {"level": 2, "name": "ASSIST", "desc": "Prepare actions but require approval."},
    {"level": 3, "name": "EXECUTE", "desc": "Execute approved workflows."},
    {"level": 4, "name": "AUTONOMOUS", "desc": "Execute within predefined boundaries."},
    {"level": 5, "name": "ADAPTIVE", "desc": "Learn, optimize and improve within governance boundaries."},
]


def autonomy_name(level):
    for a in AUTONOMY_LEVELS:
        if a["level"] == level:
            return a["name"]
    return "OBSERVE"


# ---------------------------------------------------------------------------
# Agent workforce
# ---------------------------------------------------------------------------

AGENTS = [
    {
        "id": "strategy",
        "name": "AI Strategy Agent",
        "role": "STRATEGY",
        "status": "active",
        "mission": "Align AI initiatives with the agency's strategic objectives.",
        "task": "Evaluating AI-GOS market positioning against competitor whitepapers.",
        "tools": ["vault", "research", "analytics"],
        "skills": ["market_scan", "positioning_review"],
        "confidence": 0.92,
        "last_action": "Completed competitive analysis of 4 AI governance platforms.",
        "next_action": "Draft strategic recommendation for AI-GOS v2 positioning.",
        "impact": "Strategic direction for the flagship AI-GOS product.",
        "autonomy": 2,
    },
    {
        "id": "research",
        "name": "Research & Intelligence Agent",
        "role": "RESEARCH",
        "status": "active",
        "mission": "Continuously gather, validate and synthesize market intelligence.",
        "task": "Scanning the AI governance market for emerging compliance trends.",
        "tools": ["web_research", "vault_search", "source_eval"],
        "skills": ["market_scan", "competitor_analysis"],
        "confidence": 0.91,
        "last_action": "Completed competitor analysis of AI governance platforms.",
        "next_action": "Synthesize findings into a market intelligence brief.",
        "impact": "Informed the AI-GOS whitepaper with current market data.",
        "autonomy": 3,
    },
    {
        "id": "sales",
        "name": "Business Development Agent",
        "role": "SALES",
        "status": "active",
        "mission": "Identify and qualify new revenue opportunities.",
        "task": "Reviewing Meridian Bank's expansion potential for AI automation.",
        "tools": ["crm", "proposal_gen", "email"],
        "skills": ["proposal_generation", "opportunity_scoring"],
        "confidence": 0.88,
        "last_activity": "Flagged 3 upsell opportunities across the client portfolio.",
        "next_action": "Draft expansion proposal for Meridian Bank Group.",
        "impact": "Pipeline growth — 3 new opportunities identified this week.",
        "autonomy": 2,
    },
    {
        "id": "client",
        "name": "Client Success Agent",
        "role": "CLIENT",
        "status": "active",
        "mission": "Protect and grow client relationships.",
        "task": "Monitoring account health across all active clients.",
        "tools": ["client_db", "sentiment_analysis", "health_scoring"],
        "skills": ["account_health", "risk_detection"],
        "confidence": 0.9,
        "last_activity": "Flagged Northwind Health delivery risk for review.",
        "next_action": "Prepare client health briefing for the weekly review.",
        "impact": "Early risk detection on 2 client accounts.",
        "autonomy": 2,
    },
    {
        "id": "delivery",
        "name": "AI Delivery Agent",
        "role": "DELIVERY",
        "status": "active",
        "mission": "Ensure flawless delivery of AI engagements.",
        "task": "Monitoring AI-GOS delivery milestones and quality gates.",
        "tools": ["project_tracker", "qa", "milestone_check"],
        "skills": ["delivery_management", "risk_mitigation"],
        "confidence": 0.87,
        "last_action": "Validated AI-GOS delivery milestone 3.",
        "next_action": "Review Radius Systems delivery risks.",
        "impact": "On-time delivery for 2 of 3 active projects.",
        "autonomy": 3,
    },
    {
        "id": "product",
        "name": "Product Strategy Agent",
        "role": "PRODUCT",
        "status": "active",
        "mission": "Shape the product roadmap from market and client signals.",
        "task": "Evaluating the AI-GOS security module roadmap.",
        "tools": ["roadmap", "client_feedback", "market_scan"],
        "skills": ["product_strategy", "roadmap_planning"],
        "confidence": 0.85,
        "last_action": "Prioritized AI-GOS security module features.",
        "next_action": "Validate roadmap against client feedback.",
        "impact": "AI-GOS security module roadmap defined.",
        "autonomy": 2,
    },
    {
        "id": "automation",
        "name": "Automation Architect",
        "role": "AUTOMATION",
        "status": "active",
        "mission": "Design and deploy automation across the agency.",
        "task": "Mapping recurring workflows for automation.",
        "tools": ["workflow_engine", "integration_hub", "n8n"],
        "skills": ["workflow_design", "integration_build"],
        "confidence": 0.93,
        "last_action": "Detected a reusable proposal-generation workflow.",
        "next_action": "Propose converting the workflow into an autonomous skill.",
        "impact": "3 workflows identified for automation this month.",
        "autonomy": 3,
    },
    {
        "id": "engineering",
        "name": "AI Engineering Agent",
        "role": "ENGINEERING",
        "status": "active",
        "mission": "Build and maintain the AI engineering stack.",
        "task": "Reviewing model routing for cost optimization.",
        "tools": ["code_repo", "model_router", "ci_cd"],
        "skills": ["model_routing", "rag_optimization"],
        "confidence": 0.89,
        "last_action": "Optimized RAG retrieval for the knowledge base.",
        "next_action": "Evaluate open-source model candidates.",
        "impact": "Reduced inference cost by 18% this quarter.",
        "autonomy": 3,
    },
    {
        "id": "security",
        "name": "Cybersecurity Agent",
        "role": "SECURITY",
        "status": "watch",
        "mission": "Protect the agency's data, systems and client information.",
        "task": "Monitoring access patterns and data boundaries.",
        "tools": ["audit_log", "policy_engine", "secret_vault"],
        "skills": ["threat_detection", "policy_enforcement"],
        "confidence": 0.96,
        "last_action": "No anomalies detected in the last 24 hours.",
        "next_action": "Review tool permission changes.",
        "impact": "Zero security incidents this quarter.",
        "autonomy": 4,
    },
    {
        "id": "governance",
        "name": "AI Governance Agent",
        "role": "GOVERNANCE",
        "status": "active",
        "mission": "Ensure every AI action is governed, auditable and compliant.",
        "task": "Auditing autonomous actions for compliance.",
        "tools": ["audit_trail", "compliance_checker", "approval_flow"],
        "skills": ["governance_audit", "risk_assessment"],
        "confidence": 0.95,
        "last_action": "Audited 14 autonomous actions — all compliant.",
        "next_action": "Review skill permission boundaries.",
        "impact": "Full audit trail maintained for every autonomous action.",
        "autonomy": 4,
    },
    {
        "id": "finance",
        "name": "Financial Intelligence Agent",
        "role": "FINANCE",
        "status": "active",
        "mission": "Monitor the financial health of the agency.",
        "target": "Analyzing project margins and revenue trends.",
        "tools": ["finance_db", "margin_analyzer", "forecast"],
        "skills": ["margin_analysis", "revenue_forecast"],
        "confidence": 0.89,
        "last_action": "Detected margin pressure on one project.",
        "next_action": "Recommend margin recovery actions.",
        "impact": "Identified 2 margin risks in the active portfolio.",
        "autonomy": 2,
    },
    {
        "id": "marketing",
        "name": "Marketing & GTM Agent",
        "role": "MARKETING",
        "status": "idle",
        "mission": "Drive go-to-market and brand growth.",
        "target": "Preparing the AI-GOS launch narrative.",
        "tools": ["content_gen", "social", "campaign_tracker"],
        "skills": ["content_creation", "gtm_planning"],
        "confidence": 0.82,
        "last_action": "Drafted AI-GOS launch messaging.",
        "next_action": "Schedule launch campaign.",
        "impact": "AI-GOS launch narrative ready.",
        "autonomy": 2,
    },
    {
        "id": "project",
        "name": "Project Management Agent",
        "role": "PROJECT",
        "status": "active",
        "mission": "Keep every project on track, on budget and on margin.",
        "target": "Monitoring 3 active projects.",
        "tools": ["project_tracker", "risk_register", "resource_planner"],
        "skills": ["project_health", "risk_mitigation"],
        "confidence": 0.9,
        "last_action": "Updated project health for all active projects.",
        "next_action": "Flag Radius Systems timeline risk.",
        "impact": "2 projects on track, 1 needs attention.",
        "autonomy": 3,
    },
    {
        "id": "qa",
        "name": "Quality & Validation Agent",
        "role": "QA",
        "status": "active",
        "mission": "Validate every skill, workflow and deliverable.",
        "target": "Validating the new proposal-generation skill.",
        "tools": ["test_harness", "validation_engine", "skill_tester"],
        "skills": ["skill_validation", "deliverable_qa"],
        "confidence": 0.97,
        "last_action": "Validated Enterprise_AI_Assessment_v2 skill.",
        "next_action": "Validate the proposal-generation skill.",
        "impact": "96% skill success rate across the library.",
        "autonomy": 3,
    },
    {
        "id": "ceo",
        "name": "Executive Chief-of-Staff Agent",
        "role": "CEO",
        "status": "active",
        "mission": "Synthesize everything into executive decisions.",
        "target": "Preparing the daily CEO briefing.",
        "tools": ["all_agents", "briefing_engine", "decision_support"],
        "skills": ["ceo_briefing", "decision_support"],
        "confidence": 0.92,
        "last_action": "Prepared the daily CEO briefing.",
        "next_action": "Surface 2 decisions requiring approval.",
        "impact": "One unified view of the entire agency.",
        "autonomy": 2,
    },
]


# ---------------------------------------------------------------------------
# Skill library
# ---------------------------------------------------------------------------

SKILLS = [
    {
        "id": "enterprise_ai_assessment",
        "name": "Enterprise AI Assessment",
        "purpose": "Assess a client's AI readiness and produce a structured assessment report.",
        "version": "2.4",
        "success_rate": 0.96,
        "executions": 48,
        "last_validated": "Today",
        "autonomy": 2,
        "inputs": ["client profile", "current stack", "business goals"],
        "tools": ["vault_search", "assessment_template", "report_gen"],
        "workflow": ["Gather client context", "Map AI opportunities", "Score readiness", "Generate report"],
        "decision_logic": "Score each opportunity by Impact × Feasibility × Urgency × Strategic Value.",
        "output": "Structured AI readiness assessment report.",
        "validation": "QA Agent validates against 12 quality gates.",
        "dependencies": ["vault", "report_gen"],
        "permissions": ["read:clients", "read:projects", "write:reports"],
        "risk": "low",
        "owner": "Delivery Agent",
        "status": "validated",
    },
    {
        "id": "proposal_generation",
        "name": "Proposal Generation",
        "purpose": "Generate a client proposal from engagement context and pricing principles.",
        "version": "1.8",
        "success_rate": 0.92,
        "executions": 31,
        "last_validated": "Yesterday",
        "autonomy": 2,
        "inputs": ["client context", "scope", "pricing model"],
        "tools": ["pricing_engine", "proposal_template", "vault_search"],
        "workflow": ["Extract client context", "Map scope to services", "Apply pricing principles", "Draft proposal"],
        "decision_logic": "Select pricing model from the pricing principles note.",
        "output": "Client-ready proposal document.",
        "validation": "QA Agent validates pricing consistency.",
        "dependencies": ["vault_search", "pricing_engine"],
        "permissions": ["read:clients", "read:notes", "write:proposals"],
        "risk": "medium",
        "owner": "Sales Agent",
        "last_validation": "Yesterday",
    },
    {
        "id": "market_scan",
        "name": "Market Scan",
        "purpose": "Scan the market for competitors, trends and opportunities.",
        "version": "3.1",
        "success_rate": 0.94,
        "executions": 22,
        "last_validated": "3 days ago",
        "autonomy": 3,
        "inputs": ["market segment", "keywords", "time horizon"],
        "tools": ["market_research", "source_eval", "synthesis"],
        "workflow": ["Formulate research question", "Gather sources", "Evaluate credibility", "Synthesize findings"],
        "decision": "Rank sources by credibility and recency.",
        "output": "Market intelligence brief with cited sources.",
        "validation": "Research Agent validates source credibility.",
        "dependencies": ["market_research", "source_eval"],
        "permissions": ["read:market", "write:reports"],
        "risk": "low",
        "owner": "Research Agent",
        "last_validation": "3 days ago",
    },
    {
        "id": "client_health",
        "name": "Client Health Assessment",
        "purpose": "Assess the health of a client account across multiple dimensions.",
        "version": "1.2",
        "success_rate": 0.9,
        "executions": 15,
        "last_validated": "This week",
        "autonomy": 2,
        "inputs": ["client id"],
        "tools": ["client_db", "sentiment_analysis", "health_scoring"],
        "workflow": ["Load client data", "Score health dimensions", "Flag risks", "Generate report"],
        "decision": "Health score = weighted average of delivery, sentiment, revenue, risk.",
        "output": "Client health report with risk flags.",
        "validation": "Client Success Agent reviews flags.",
        "dependencies": ["client_db", "sentiment_analysis"],
        "permissions": ["read:clients"],
        "risk": "low",
        "owner": "Client Success Agent",
        "last_validation": "This week",
    },
    {
        "id": "margin_analysis",
        "name": "Margin Analysis",
        "purpose": "Analyze project profitability and detect margin erosion.",
        "version": "1.0",
        "success_rate": 0.88,
        "executions": 9,
        "last_validated": "This week",
        "autonomy": 2,
        "inputs": ["project id", "financial data"],
        "tools": ["financial_db", "margin_analyzer"],
        "workflow": ["Load project financials", "Compute margin", "Compare to baseline", "Flag deviations"],
        "decision": "Flag when margin drops below 25%.",
        "output": "Margin analysis with risk flags.",
        "validation": "Financial Intelligence Agent reviews.",
        "dependencies": ["financial_db"],
        "permissions": ["read:finance"],
        "risk": "medium",
        "owner": "Financial Intelligence Agent",
        "last_validation": "This week",
    },
    {
        "id": "ceo_briefing",
        "name": "CEO Briefing",
        "purpose": "Synthesize the agency's state into a daily executive briefing.",
        "version": "2.1",
        "success_rate": 0.95,
        "executions": 40,
        "last_validated": "Today",
        "autonomy": 2,
        "inputs": ["all agent states", "vault context"],
        "tools": ["all_agents", "briefing_engine"],
        "workflow": ["Collect agent states", "Aggregate insights", "Rank by importance", "Generate briefing"],
        "output": "Daily CEO briefing with priorities, decisions, risks, opportunities.",
        "validation": "CEO Agent validates completeness.",
        "dependencies": ["all_agents"],
        "permissions": ["read:all"],
        "risk": "low",
        "owner": "Chief-of-Staff Agent",
        "last_validation": "Today",
    },
]

# Merge downloaded JARVIS skills into the HEER skill library.
# Each JARVIS skill is loaded from `.agents/skills/*/SKILL.md` and
# converted into HEER's skill-dict format by agent.jarvis_skills.
_JARVIS_SKILLS = jarvis_skills.get_jarvis_skills()
if _JARVIS_SKILLS:
    # Avoid duplicate ids — JARVIS skills take precedence if an id collides.
    _existing_ids = {s["id"] for s in SKILLS}
    for _js in _JARVIS_SKILLS:
        if _js["id"] not in _existing_ids:
            SKILLS.append(_js)
            _existing_ids.add(_js["id"])


# ---------------------------------------------------------------------------
# Learning engine
# ---------------------------------------------------------------------------

LEARNING = {
    "knowledge_growth": {
        "total_learnings": 128,
        "this_week": 14,
        "today": 3,
        "growth_rate": "+12% this week",
    },
    "recent_learnings": [
        {
            "title": "Meridian Bank prefers compliance-first AI proposals",
            "source": "Client engagement analysis",
            "confidence": 0.92,
            "type": "client_preference",
            "when": "2 hours ago",
        },
        {
            "title": "AI-GOS security module is the top requested feature",
            "source": "Client feedback synthesis",
            "confidence": 0.89,
            "type": "product_signal",
            "when": "5 hours ago",
        },
        {
            "title": "Proposal acceptance rate improves 23% with pricing anchors",
            "source": "Proposal outcome analysis",
            "confidence": 0.87,
            "type": "skill_improvement",
            "when": "Yesterday",
        },
        {
            "title": "Northwind Health prefers phased AI rollouts",
            "source": "Delivery retrospective",
            "confidence": 0.85,
            "type": "client_preference",
            "when": "Yesterday",
        },
    ],
    "new_skills": [
        {
            "name": "Proposal Generation",
            "version": "1.8",
            "discovered": "Detected from 7 repeated proposal workflows",
            "status": "registered",
            "autonomy": "ASSIST",
        },
        {
            "name": "Client Health Assessment",
            "version": "1.2",
            "discovered": "Created from recurring health reviews",
            "status": "registered",
            "autonomy": "ASSIST",
        },
    ],
    "skill_improvements": [
        {
            "skill": "Enterprise AI Assessment",
            "from": "v2.3",
            "to": "v2.4",
            "improvement": "Success rate 92% → 96%",
            "when": "Today",
        },
        {
            "skill": "Market Scan",
            "from": "v2.9",
            "to": "v3.0",
            "improvement": "Source credibility scoring added",
            "when": "3 days ago",
        },
    ],
    "knowledge_gaps": [
        {
            "area": "Radius Systems' internal AI adoption roadmap",
            "why": "Not documented in any project note",
            "impact": "Cannot assess expansion potential",
            "action": "Ask Pankaj for the roadmap",
        },
        {
            "area": "Verdant Retail's current automation stack",
            "why": "No technical inventory on file",
            "impact": "Cannot identify automation opportunities",
            "action": "Request stack inventory",
        },
    ],
    "conflicts": [
        {
            "topic": "AI-GOS pricing model",
            "conflict": "Pricing note suggests value-based; proposal uses hourly",
            "impact": "Proposal margin may be understated",
            "action": "Reconcile with Pankaj",
        },
    ],
    "outdated": [
        {
            "topic": "Market scan for AI governance",
            "age": "3 months",
            "action": "Re-run market scan",
        },
    ],
    "learning_confidence": 0.91,
}


# ---------------------------------------------------------------------------
# Opportunity radar
# ---------------------------------------------------------------------------

OPPORTUNITIES = [
    {
        "id": "opp_1",
        "title": "Meridian Bank — Compliance AI Automation",
        "category": "AI Agent Opportunity",
        "impact": 0.9,
        "feasibility": 0.85,
        "urgency": 0.7,
        "strategic_value": 0.95,
        "score": 0.86,
        "client": "Meridian Bank Group",
        "summary": "Three compliance processes are suitable for AI automation.",
        "action": "Draft a compliance automation proposal.",
    },
    {
        "id": "opp_2",
        "title": "Northwind Health — Delivery Optimization",
        "category": "Process Optimization",
        "impact": 0.8,
        "feasibility": 0.9,
        "urgency": 0.6,
        "strategic_value": 0.8,
        "score": 0.78,
        "client": "Northwind Health",
        "summary": "Delivery timeline can be compressed with workflow automation.",
        "action": "Propose delivery optimization engagement.",
    },
    {
        "id": "opp_3",
        "title": "AI-GOS Security Module — Product Expansion",
        "category": "Product Opportunity",
        "impact": 0.85,
        "feasibility": 0.75,
        "urgency": 0.65,
        "strategic_value": 0.9,
        "score": 0.79,
        "client": "Internal",
        "summary": "Security module is the top requested feature across clients.",
        "action": "Accelerate security module roadmap.",
    },
    {
        "id": "opp_4",
        "title": "Verdant Retail — AI Upsell",
        "category": "Upsell Opportunity",
        "impact": 0.7,
        "feasibility": 0.8,
        "urgency": 0.5,
        "strategic_value": 0.75,
        "score": 0.69,
        "client": "Verdant Retail",
        "summary": "Two additional AI use cases identified in retail operations.",
        "action": "Schedule upsell conversation.",
    },
    {
        "id": "opp_5",
        "title": "Finedge Capital — Data Opportunity",
        "category": "Data Opportunity",
        "impact": 0.75,
        "feasibility": 0.7,
        "urgency": 0.55,
        "strategic_value": 0.8,
        "score": 0.7,
        "client": "Finedge Capital",
        "summary": "Unstructured data can power a client intelligence dashboard.",
        "action": "Propose data modernization engagement.",
    },
]


# ---------------------------------------------------------------------------
# Activity feed
# ---------------------------------------------------------------------------

ACTIVITY = [
    {"time": "19:42", "agent": "Research Agent", "action": "Completed competitor analysis of AI governance platforms.", "type": "research"},
    {"time": "19:44", "agent": "HEER", "action": "Detected a reusable proposal-generation workflow.", "type": "learning"},
    {"time": "19:46", "agent": "HEER", "action": "New skill generated: Proposal_Generation_v1.8.", "type": "skill"},
    {"time": "19:47", "agent": "QA Agent", "action": "Validated the Proposal Generation skill.", "type": "qa"},
    {"time": "19:48", "agent": "HEER", "action": "Skill registered with ASSIST autonomy.", "type": "governance"},
    {"time": "19:35", "agent": "Financial Intelligence Agent", "action": "Detected margin pressure on one project.", "type": "finance"},
    {"time": "19:30", "agent": "Client Success Agent", "action": "Flagged Northwind Health delivery timeline for review.", "type": "client"},
    {"time": "19:22", "agent": "Automation Architect", "action": "Mapped 3 workflows suitable for automation.", "type": "automation"},
    {"time": "19:15", "agent": "Research Agent", "action": "Synthesized market intelligence brief.", "type": "research"},
    {"time": "19:08", "agent": "Chief-of-Staff Agent", "action": "Prepared the daily CEO briefing.", "type": "executive"},
    {"time": "18:55", "agent": "Cybersecurity Agent", "action": "No anomalies detected in the last 24 hours.", "type": "security"},
    {"time": "18:40", "agent": "AI Engineering Agent", "action": "Optimized RAG query for the AI-GOS knowledge base.", "type": "engineering"},
]


# ---------------------------------------------------------------------------
# Client intelligence
# ---------------------------------------------------------------------------

def _client_intel(business_id=None):
    v = get_vault(business_id)
    if v is None:
        return []
    clients = []
    for nid, node in v.nodes.items():
        if node["type"] != "clients":
            continue
        text = node["text"]
        name = node["title"]
        health = _score_health(text)
        clients.append({
            "id": node["id"],
            "name": name,
            "health": health,
            "revenue": _extract_revenue(text),
            "projects": _extract_projects(v, name),
            "risks": _extract_risks(text),
            "opportunities": _extract_opportunities(text),
            "stakeholders": _extract_stakeholders(text),
            "ai_opportunities": _count_ai_opportunities(text),
            "open_actions": _extract_actions(text),
            "documents": _count_documents(v, name),
        })
    return clients


def _score_health(text):
    t = text.lower()
    score = 0.75
    if any(w in t for w in ["risk", "concern", "issue", "delay", "at risk"]):
        score -= 0.15
    if any(w in t for w in ["expansion", "growth", "opportunity", "upsell", "renewal"]):
        score += 0.1
    if any(w in t for w in ["strong", "excellent", "healthy", "committed"]):
        score += 0.1
    return max(0.2, min(0.98, round(score, 2)))


def _extract_revenue(text):
    m = re.search(r"(?:revenue|contract|value|budget)[^\d]*?([\d.,]+\s*[kKmM]?)", text, re.IGNORECASE)
    return m.group(1) if m else "—"


def _extract_projects(v, name):
    if v is None:
        return []
    projects = []
    for nid, node in v.nodes.items():
        if node["type"] == "projects" and name.lower() in node["text"].lower():
            projects.append(node["title"])
    return projects


def _extract_risks(text):
    risks = []
    for line in text.splitlines():
        if re.search(r"risk|concern|issue|delay|at-risk", line, re.IGNORECASE):
            risks.append(line.strip().lstrip("- ").strip())
    return risks[:3]


def _extract_opportunities(text):
    opps = []
    for line in text.splitlines():
        if re.search(r"opportunity|upsell|expansion|growth|automation", line, re.IGNORECASE):
            clean = line.strip().lstrip("- ").strip()
            # Skip pure wikilink lines (e.g. "[[Hinjewadi Expansion]]")
            if clean.startswith("[[") and clean.endswith("]]"):
                continue
            # Strip "Opportunity: " / "Opportunity - " prefixes
            clean = re.sub(r"^opportunity\s*[:—-]\s*", "", clean, flags=re.IGNORECASE)
            opps.append(clean)
    return opps[:3]


def _extract_stakeholders(text):
    st = []
    for line in text.splitlines():
        if re.search(r"@|CEO|CTO|CIO|Director|Head|VP|Manager", line, re.IGNORECASE):
            st.append(line.strip().lstrip("- ").strip())
    return st[:4]


def _count_ai_opportunities(text):
    t = text.lower()
    count = 0
    for kw in ["automation", "ai opportunity", "agent", "workflow", "process"]:
        count += t.count(kw)
    return min(count, 8)


def _extract_actions(text):
    actions = []
    for line in text.splitlines():
        if re.search(r"action|follow up|next step|todo|pending", line, re.IGNORECASE):
            actions.append(line.strip().lstrip("- ").strip())
    return actions[:3]


def _count_documents(v, name):
    if v is None:
        return 0
    count = 0
    for node in v.nodes.values():
        if name.lower() in node["text"].lower():
            count += 1
    return count


# ---------------------------------------------------------------------------
# Project intelligence
# ---------------------------------------------------------------------------

def _project_intel(business_id=None):
    v = get_vault(business_id)
    if v is None:
        return []
    projects = []
    for nid, node in v.nodes.items():
        if node["type"] != "projects":
            continue
        text = node["text"]
        projects.append({
            "id": node["id"],
            "name": node["title"],
            "health": _score_health(text),
            "progress": _extract_progress(text),
            "budget": _extract_revenue(text),
            "margin": _extract_margin(text),
            "milestones": _extract_milestones(text),
            "risks": _extract_risks(text),
            "next_actions": _extract_actions(text),
            "client": _extract_client(text),
        })
    return projects


def _extract_progress(text):
    m = re.search(r"(\d{1,3})\s*%", text)
    return int(m.group(1)) if m else 0


def _extract_margin(text):
    m = re.search(r"margin[^\d]*?(\d{1,3})\s*%", text, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _extract_milestones(text):
    ms = []
    for line in text.splitlines():
        if re.search(r"milestone|phase|sprint|deliverable", line, re.IGNORECASE):
            ms.append(line.strip().lstrip("- ").strip())
    return ms[:4]


def _extract_client(text):
    v = get_vault()
    if v is None:
        return "—"
    for nid, node in v.nodes.items():
        if node["type"] == "clients" and node["title"].lower() in text.lower():
            return node["title"]
    return "—"


# ---------------------------------------------------------------------------
# Business intelligence
# ---------------------------------------------------------------------------

def _finance_file(business_id=None):
    """Locate the business's finance.md (or finance.txt) file."""
    root = data.data_root(business_id)
    if not root:
        return None
    for fname in ("finance.md", "finance.txt"):
        path = os.path.join(root, fname)
        if os.path.isfile(path):
            return path
    return None


def _parse_finance(business_id=None):
    """Parse key: value pairs from the business's finance file."""
    path = _finance_file(business_id)
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return {}
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        result[key.strip().lower().replace(" ", "_")] = value.strip()
    return result


def _business_intel(business_id=None):
    """Business KPIs derived from finance.md, falling back to defaults."""
    fin = _parse_finance(business_id)
    b = business.get_business(business_id) if business_id else business.current_business()
    name = b["name"] if b else "Business"

    defaults = {
        "revenue": "₹4.2M",
        "pipeline": "₹8.7M",
        "mrr": "₹3.5L",
        "arr": "₹42L",
        "gross_margin": "68%",
        "client_acquisition": "+2 this quarter",
        "conversion": "38%",
        "project_profitability": "72%",
        "utilization": "84%",
        "delivery_performance": "94%",
        "automation_savings": "₹18L / year",
        "ai_roi": "3.4×",
        "trends": {
            "revenue": "+12%",
            "pipeline": "+8%",
            "margin": "-2%",
            "utilization": "+5%",
        },
    }

    # Map finance.md keys to the payload shape
    key_map = {
        "revenue": "revenue",
        "pipeline": "pipeline",
        "mrr": "mrr",
        "arr": "arr",
        "gross_margin": "gross_margin",
        "client_acquisition": "client_acquisition",
        "conversion": "conversion",
        "project_profitability": "project_profitability",
        "utilization": "utilization",
        "delivery_performance": "delivery_performance",
        "automation_savings": "automation_savings",
        "ai_roi": "ai_roi",
    }
    payload = {}
    for fin_key, out_key in key_map.items():
        payload[out_key] = fin.get(fin_key, defaults[out_key])

    # Trends: optional "trend_revenue", "trend_pipeline", etc.
    trends = {}
    for trend_key, label in [("trend_revenue", "revenue"), ("trend_pipeline", "pipeline"),
                             ("trend_margin", "margin"), ("trend_utilization", "utilization")]:
        trends[label] = fin.get(trend_key, defaults["trends"][label])
    payload["trends"] = trends
    payload["business_name"] = name
    return payload


# ---------------------------------------------------------------------------
# Automation map
# ---------------------------------------------------------------------------

AUTOMATIONS = [
    {
        "id": "auto_1",
        "name": "Proposal Generation",
        "trigger": "New client engagement detected",
        "agent": "Sales Agent",
        "skill": "Proposal Generation v1.8",
        "tool": "proposal_engine",
        "action": "Draft proposal from client context",
        "validation": "QA Agent validates pricing",
        "outcome": "Client-ready proposal",
        "status": "active",
        "autonomy": "ASSIST",
    },
    {
        "id": "auto_2",
        "name": "Client Health Monitoring",
        "trigger": "Weekly health check",
        "agent": "Client Success Agent",
        "skill": "Client Health Assessment v1.2",
        "tool": "health_scoring",
        "action": "Score account health",
        "validation": "Flag risks for review",
        "outcome": "Health report with risk flags",
        "status": "active",
        "autonomy": "EXECUTE",
    },
    {
        "id": "auto_3",
        "name": "Market Intelligence Scan",
        "trigger": "Weekly market scan",
        "agent": "Research Agent",
        "skill": "Market Scan v3.0",
        "tool": "market_research",
        "action": "Scan market for trends",
        "validation": "Source credibility check",
        "outcome": "Market intelligence brief",
        "status": "active",
        "autonomy": "EXECUTE",
    },
    {
        "id": "auto_4",
        "name": "Margin Monitoring",
        "trigger": "Project financial update",
        "agent": "Financial Intelligence Agent",
        "skill": "Margin Analysis v1.0",
        "tool": "margin_analyzer",
        "action": "Compute project margin",
        "validation": "Flag margin erosion",
        "outcome": "Margin alert",
        "status": "active",
        "autonomy": "RECOMMEND",
    },
]


# ---------------------------------------------------------------------------
# CEO briefing
# ---------------------------------------------------------------------------

def _briefing(business_id=None):
    now = _dt.datetime.now()
    hour = now.hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    b = business.get_business(business_id) if business_id else business.current_business()
    name = b["name"] if b else "Business"
    owner = b.get("owner", "Pankaj") if b else "Pankaj"

    clients = _client_intel(business_id)
    projects = _project_intel(business_id)
    fin = _business_intel(business_id)
    opps = _derive_opportunities(business_id)

    client_names = ", ".join(c["name"] for c in clients[:3]) or "no active clients"
    project_names = ", ".join(p["name"] for p in projects[:3]) or "no active projects"
    client_count = len(clients)
    project_count = len(projects)

    return {
        "greeting": f"{greeting}, {owner}.",
        "subtitle": f"HEER has analyzed {name} — {client_count} clients, {project_count} projects.",
        "today": [
            f"{client_count} client accounts active — {client_names}.",
            f"{project_count} projects in flight — {project_names}.",
            "Review the latest intelligence for decisions requiring attention.",
        ],
        "this_week": [
            f"{len(opps)} opportunities identified that could grow {name}.",
            "Client health reviews due for all active accounts.",
            "Skill library is ready for validation.",
        ],
        "decisions": [
            {
                "title": f"Review top opportunity for {name}",
                "impact": fin.get("pipeline", "—") + " potential pipeline",
                "confidence": 0.9,
                "due": "Today",
            },
            {
                "title": "Approve project timeline adjustments",
                "impact": "Protects client relationships and margins",
                "confidence": 0.85,
                "due": "Tomorrow",
            },
            {
                "title": "Validate new skills for the library",
                "impact": "Improves automation coverage",
                "confidence": 0.88,
                "due": "This week",
            },
        ],
        "risks": [
            {
                "title": "Delivery timeline pressure",
                "severity": "medium",
                "detail": "Monitor active project milestones for slippage.",
            },
            {
                "title": "Pricing consistency",
                "severity": "medium",
                "detail": "Ensure proposals align with pricing principles.",
            },
            {
                "title": "Client health watch",
                "severity": "low",
                "detail": "Flagged accounts need proactive outreach.",
            },
        ],
        "opportunities": [
            {
                "title": "Top-scored opportunity",
                "value": "High",
                "detail": opps[0]["summary"] if opps else "None",
            },
            {
                "title": "Expansion potential",
                "value": "Medium",
                "detail": "Upsell and cross-sell across the active portfolio.",
            },
            {
                "title": "Automation savings",
                "value": "Medium",
                "detail": fin.get("automation_savings", "—") + " in annual savings.",
            },
        ],
        "performance": {
            "revenue": fin.get("revenue", "—"),
            "pipeline": fin.get("pipeline", "—"),
            "gross_margin": fin.get("gross_margin", "—"),
            "utilization": fin.get("utilization", "—"),
            "delivery": fin.get("delivery_performance", "—"),
        },
        "ai": [
            "OpenAI released a new governance framework — relevant to AI-GOS.",
            "Open-source model quality improved — worth re-evaluating model routing.",
            "RAG optimization reduced inference cost by 18%.",
        ],
        "recommendation": {
            "title": "Review the top-scored opportunity",
            "reason": f"Highest-scored opportunity with {fin.get('pipeline', '—')} potential pipeline.",
            "action": "One-click approval available.",
        },
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def agents_payload():
    return {
        "agents": AGENTS,
        "autonomy_levels": AUTONOMY_LEVELS,
        "active_count": sum(1 for a in AGENTS if a["status"] == "active"),
        "total": len(AGENTS),
    }


def skills_payload():
    skills = []
    for s in SKILLS:
        item = dict(s)
        item["autonomy"] = autonomy_name(item.get("autonomy", 0))
        skills.append(item)
    jarvis_count = len(_JARVIS_SKILLS)
    return {
        "skills": skills,
        "total": len(skills),
        "avg_success": round(sum(s["success_rate"] for s in skills) / len(skills), 2),
        "total_executions": sum(s["executions"] for s in skills),
        "jarvis_skills": jarvis_count,
        "jarvis_categories": sorted({s.get("category", "Other") for s in _JARVIS_SKILLS}),
    }


def learning_payload():
    """Flatten the learning center into the item stream the UI renders."""
    items = []
    for item in LEARNING.get("recent_learnings", []):
        items.append({
            "type": "growth",
            "text": item.get("title", ""),
            "meta": item.get("source", "") + " · " + str(round(item.get("confidence", 0) * 100)) + "% confidence",
        })
    for item in LEARNING.get("new_skills", []):
        items.append({
            "type": "skill",
            "text": "New skill: " + item.get("name", "") + " v" + str(item.get("version", "1.0")),
            "meta": item.get("discovered", "") + " · " + item.get("autonomy", "ASSIST"),
        })
    for item in LEARNING.get("skill_improvements", []):
        items.append({
            "type": "improvement",
            "text": item.get("skill", "") + " improved " + item.get("from", "") + " → " + item.get("to", ""),
            "meta": item.get("improvement", "") + " · " + item.get("when", ""),
        })
    for item in LEARNING.get("knowledge_gaps", []):
        items.append({
            "type": "gap",
            "text": "Knowledge gap: " + item.get("area", ""),
            "meta": item.get("why", "") + " · " + item.get("action", ""),
        })
    for item in LEARNING.get("conflicts", []):
        items.append({
            "type": "conflict",
            "text": "Conflict: " + item.get("topic", ""),
            "meta": item.get("conflict", "") + " · " + item.get("action", ""),
        })
    for item in LEARNING.get("outdated", []):
        items.append({
            "type": "outdated",
            "text": "Outdated: " + item.get("topic", ""),
            "meta": item.get("age", "") + " old · " + item.get("action", ""),
        })
    return {
        "items": items,
        "knowledge_growth": LEARNING.get("knowledge_growth", {}),
        "learning_confidence": LEARNING.get("learning_confidence", 0),
    }


def briefing_payload(business_id=None):
    return _briefing(business_id)


def _derive_opportunities(business_id=None):
    """Derive opportunities from the business's client intel (Opportunity: lines)."""
    opps = []
    for c in _client_intel(business_id):
        for i, opp_text in enumerate(c.get("opportunities", [])):
            impact = 0.7
            feasibility = 0.75
            urgency = 0.6
            strategic_value = 0.7
            t = opp_text.lower()
            if any(w in t for w in ["expansion", "cross-sell", "upsell", "renewal"]):
                strategic_value += 0.15
            if any(w in t for w in ["annual", "partnership", "contract"]):
                impact += 0.1
            if any(w in t for w in ["friday", "evening", "event", "corporate"]):
                urgency += 0.1
            if c.get("health", 0.75) > 0.8:
                feasibility += 0.1
            score = round((impact + feasibility + urgency + strategic_value) / 4, 2)
            opps.append({
                "id": f"opp_{c['id']}_{i}",
                "title": f"{c['name']} — {opp_text[:60]}",
                "category": "Client Opportunity",
                "impact": round(impact, 2),
                "feasibility": round(feasibility, 2),
                "urgency": round(urgency, 2),
                "strategic_value": round(strategic_value, 2),
                "score": score,
                "client": c["name"],
                "summary": opp_text,
                "action": f"Schedule follow-up with {c['name']}.",
            })
    return sorted(opps, key=lambda o: -o["score"])


def opportunities_payload(business_id=None):
    opps = _derive_opportunities(business_id)
    return {
        "opportunities": opps,
        "radar": {
            "labels": ["Impact", "Feasibility", "Urgency", "Strategic Value"],
            "top": opps[0] if opps else None,
        },
    }

def activity_payload():
    return {"items": [{"time": a.get("time", ""), "text": a.get("agent", "") + " — " + a.get("action", "")} for a in ACTIVITY]}


def clients_payload(business_id=None):
    return {"clients": _client_intel(business_id)}


def projects_payload(business_id=None):
    return {"projects": _project_intel(business_id)}


def business_payload(business_id=None):
    return _business_intel(business_id)


def automations_payload():
    return {"automations": AUTOMATIONS}


def network_payload(business_id=None):
    """HEER AI network — core connected to agents, skills, knowledge, tools, clients, projects."""
    nodes = [{"id": "heer", "label": "HEER", "type": "core", "size": 28}]
    links = []
    for a in AGENTS:
        nodes.append({"id": "agent_" + a["id"], "label": a["name"], "type": "agent", "size": 10})
        links.append({"source": "heer", "target": "agent_" + a["id"]})
    for s in SKILLS:
        nodes.append({"id": "skill_" + s["id"], "label": s["name"], "type": "skill", "size": 7})
        links.append({"source": "heer", "target": "skill_" + s["id"]})
    for c in _client_intel(business_id):
        nodes.append({"id": "client_" + c["id"], "label": c["name"], "type": "client", "size": 8})
        links.append({"source": "heer", "target": "client_" + c["id"]})
    for p in _project_intel(business_id):
        nodes.append({"id": "project_" + p["id"], "label": p["name"], "type": "project", "size": 8})
        links.append({"source": "heer", "target": "project_" + p["id"]})
    for a in AUTOMATIONS:
        nodes.append({"id": "auto_" + a["id"], "label": a["name"], "type": "automation", "size": 6})
        links.append({"source": "heer", "target": "auto_" + a["id"]})
    return {"nodes": nodes, "links": links}


def status_payload():
    return {
        "demo": data.demo_mode(),
        "agents_active": sum(1 for a in AGENTS if a["status"] == "active"),
        "agents_total": len(AGENTS),
        "skills": len(SKILLS),
        "learning": LEARNING["learning_confidence"],
        "autonomy": "ADAPTIVE",
        "model": "multi-model",
        "tts": "elevenlabs",
        "asr": "configured",
    }


def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "switch":
        b = business.switch_business(sys.argv[2])
        print(json.dumps(b, indent=2, ensure_ascii=False) if b else "Business not found.")
        return
    print(json.dumps({
        "business": business.current_business(),
        "agents": len(AGENTS),
        "skills": len(SKILLS),
        "opportunities": len(OPPORTUNITIES),
        "clients": len(_client_intel()),
        "projects": len(_project_intel()),
        "automations": len(AUTOMATIONS),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()