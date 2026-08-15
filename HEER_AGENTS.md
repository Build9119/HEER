# HEER Agent Workforce

> Complete catalog of the 15 existing fixture agents and the 13 target AI-Agency operational agents.

---

## 1. What Exists Today

The current `agent/heer.py` defines **15 agent fixtures** — rich declarative dictionaries (mission, role, tools, skills, confidence, autonomy) that feed the dashboard's Agents view and the network map. **They are data, not executable code.** No orchestrator routes requests to them; no agent actually invokes tools.

### 1.1 Existing Fixture Agents

| ID | Name | Role | Autonomy | Mission |
|---|---|---|---|---|
| `strategy` | AI Strategy Agent | STRATEGY | ASSIST | Align AI initiatives with agency strategic objectives |
| `research` | Research & Intelligence Agent | RESEARCH | EXECUTE | Continuously gather, validate, synthesize market intelligence |
| `sales` | Business Development Agent | SALES | ASSIST | Identify and qualify new revenue opportunities |
| `client` | Client Success Agent | CLIENT | ASSIST | Protect and grow client relationships |
| `delivery` | AI Delivery Agent | DELIVERY | EXECUTE | Ensure flawless delivery of AI engagements |
| `product` | Product Strategy Agent | PRODUCT | ASSIST | Shape product roadmap from market/client signals |
| `automation` | Automation Architect | AUTOMATION | EXECUTE | Design and deploy automation across the agency |
| `engineering` | AI Engineering Agent | ENGINEERING | EXECUTE | Build and maintain the AI engineering stack |
| `security` | Cybersecurity Agent | SECURITY | AUTONOMOUS | Protect agency data, systems, client information |
| `governance` | AI Governance Agent | GOVERNANCE | AUTONOMOUS | Ensure every AI action is governed, auditable, compliant |
| `finance` | Financial Intelligence Agent | FINANCE | ASSIST | Monitor financial health of the agency |
| `marketing` | Marketing & GTM Agent | MARKETING | ASSIST | Drive go-to-market and brand growth |
| `project` | Project Management Agent | PROJECT | EXECUTE | Keep every project on track, on budget, on margin |
| `qa` | Quality & Validation Agent | QA | EXECUTE | Validate every skill, workflow and deliverable |
| `ceo` | Executive Chief-of-Staff Agent | CEO | ASSIST | Synthesize everything into executive decisions |

---

## 2. Target AI-Agency Agents (Master Prompt §3)

The target architecture defines 13 operational agents covering the full agency lifecycle. These will be implemented in the `agent/registry.py` module in Phase 1 as **declarative executable definitions** (each has a route-matching pattern, tool list, permission set, and approval level) so the orchestrator can actually dispatch to them.

| # | Target Agent | Lifecycle Stage | Role | Key Responsibilities |
|---|---|---|---|---|
| 1 | **CEO / Strategy Agent** | All | STRATEGY | Business strategy, agency priorities, growth planning, OKRs, executive briefing, decision support |
| 2 | **AI Agency Sales Agent** | Lead Gen → Acquisition | SALES | ICP creation, target accounts, lead research, qualification, outreach, pipeline, CRM prep |
| 3 | **AI Discovery / Consulting Agent** | Discovery | CONSULTING | Process discovery, current-state analysis, pain points, AI/automation opportunities, ROI estimate, roadmap |
| 4 | **AI Solution Architect** | Solution Architecture | ARCHITECT | Solution/AI-agent/workflow/integration/data/security architecture, RAG, model selection, cost optimization |
| 5 | **Proposal Agent** | Proposal | PROPOSAL | Discovery reports, executive summaries, SOWs, scope docs, pricing models, ROI models, presentations |
| 6 | **ROI / Business Case Agent** | Business Case | FINANCE-ROI | Operating cost, automation potential, savings, infra cost, payback, margin, recurring revenue |
| 7 | **Developer Agent** | Build | ENGINEERING | Write/modify/debug/refactor/test/review/document code, APIs, integrations, agents, UI, backend, DB |
| 8 | **Automation Agent** | Automation | AUTOMATION | n8n workflows, APIs, webhooks, schedules, data sync, CRM/email/document automation |
| 9 | **GitHub / Engineering Agent** | Code Ops | ENGINEERING-OPS | Repo analysis, issues, branches, PRs, reviews, CI/CD, tests, docs |
| 10 | **Project Delivery Agent** | Delivery | DELIVERY | Projects, tasks, milestones, dependencies, risks, deadlines, UAT, deployment, handover, status reports |
| 11 | **Finance Agent** | Finance | FINANCE | Revenue, pipeline, MRR, ARR, project revenue, cloud/AI/software cost, margins, CAC, LTV |
| 12 | **Marketing Agent** | Marketing | MARKETING | LinkedIn content, case studies, industry reports, campaigns, demo scripts, lead magnets |
| 13 | **AI Governance Agent** | Governance | GOVERNANCE | AI/agent/model inventory, risk assessment, policies, controls, prompt/data governance, audit logging, incidents |

---

## 3. Mapping: Existing Fixtures → Target Agents

| Target Agent | Existing Fixture(s) | Status |
|---|---|---|
| CEO / Strategy Agent | `strategy`, `ceo` | 🔄 Merge into one target agent |
| AI Agency Sales Agent | `sales` | 🔄 Extend with ICP/lead research/target accounts |
| AI Discovery / Consulting Agent | — (gap) | ➕ New |
| AI Solution Architect | `engineering`, `product` | 🔄 Repurpose |
| Proposal Agent | (part of `sales` tools) | ➕ New dedicated agent |
| ROI / Business Case Agent | `finance` | 🔄 Extend |
| Developer Agent | — (gap) | ➕ New |
| Automation Agent | `automation` | 🔄 Extend |
| GitHub / Engineering Agent | `engineering` | 🔄 Extend |
| Project Delivery Agent | `delivery`, `project` | 🔄 Merge |
| Finance Agent | `finance` | 🔄 Extend |
| Marketing Agent | `marketing` | 🔄 Extend |
| AI Governance Agent | `governance`, `security` | 🔄 Merge |

Additional fixtures that map to **supporting roles** (kept as-is for dashboard continuity):

| Existing Fixture | Role |
|---|---|
| `client` | Client Success (supports Delivery) |
| `research` | Research & Intelligence (supports Sales/Strategy) |
| `qa` | Quality & Validation (supports Delivery) |

---

## 4. Agent Definition Schema (Target — Phase 1 `agent/registry.py`)

Each registry agent is an executable definition with routing metadata:

```python
{
    "id": str,                    # unique agent id
    "name": str,
    "role": str,                  # STRATEGY | SALES | CONSULTING | ARCHITECT | ...
    "mission": str,
    "intents": [str],             # keyword/phrase patterns routed to this agent
    "tools": [str],               # tool registry ids (agent/tools.py + registry)
    "skills": [str],              # skill library ids
    "permissions": [str],         # read:clients, write:proposals, execute:deploy...
    "approval_level": int,        # 0=Read, 1=Prepare, 2=Execute, 3=Critical
    "autonomy": int,              # 0-5
    "status": str,                # active | idle | watch
    "description": str,
}
```

---

## 5. Approval Levels per Agent (proposed)

| Agent | Default Approval Level | Examples Requiring Human Approval |
|---|---|---|
| CEO / Strategy | 0 | None (read/analyze only) |
| Sales | 1 | Draft outreach → L1; Send email → L2 |
| Discovery | 0 | Read-only discovery |
| Architect | 0 | Read-only design |
| Proposal | 1 | Draft proposal → L1; Send proposal → L2 |
| ROI | 0 | Read/calc only (assumptions flagged) |
| Developer | 1 | Code change → L1; push/deploy → L2 |
| Automation | 1 | Workflow draft → L1; activate n8n → L2 |
| GitHub | 2 | Create PR → L2; merge/deploy → L2 |
| Delivery | 1 | Status report → L1; scope change → L2 |
| Finance | 0 | Read/monitor only |
| Marketing | 1 | Draft content → L1; publish campaign → L2 |
| Governance | 3 | Policy changes, credential changes, audit evidence |

---

## 6. Phase 1 Registry: 13 Agents (draft definitions)

```
AGENT_REGISTRY = {
  "ceo":            {mission: strategy, okrs, executive decisions},
  "sales":          {mission: icp, target accounts, quality leads, pipeline},
  "discovery":      {mission: process discovery, pain points, AI opportunities, ROI},
  "architect":      {mission: solution architecture, integrations, model selection},
  "proposal":       {mission: discovery reports, proposals, SOWs, pricing},
  "roi":            {mission: business case, savings, payback, margin},
  "developer":      {mission: write, modify, debug, refactor, test code},
  "automation":     {mission: n8n workflows, webhooks, integrations},
  "github":         {mission: repo analysis, issues, PRs, CI/CD},
  "delivery":       {mission: projects, milestones, risks, UAT, handover},
  "finance":        {mission: revenue, costs, margins, MRR, ARR},
  "marketing":      {mission: case studies, LinkedIn, campaigns},
  "governance":     {mission: AI inventory, risks, policies, audits, incidents},
}
```

---

## 7. Autonomy Model (Existing — Reused)

HEER already defines 6 autonomy levels in `agent/heer.py`:

| Level | Name | Description |
|---|---|---|
| 0 | OBSERVE | Only monitor |
| 1 | RECOMMEND | Analyze and recommend |
| 2 | ASSIST | Prepare actions but require approval |
| 3 | EXECUTE | Execute approved workflows |
| 4 | AUTONOMOUS | Execute within predefined boundaries |
| 5 | ADAPTIVE | Learn, optimize, improve within governance boundaries |

The target agents will map onto this existing model: **default ASSIST (2)** for most agents, EXECUTE (3) for research/delivery, AUTONOMOUS (4) for security/governance, with **approval_level** layered on top for L0-L3 human-approval gating.

---

_Document version: 1.0 — 2026-09-08_