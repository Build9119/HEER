# HEER Architecture

> **HEER — AI Agency Operating Partner**
> Intelligence That Executes.

This document records the current architecture, the target architecture, the gap map between them, and the implementation plan.

---

## 1. Conceptual Target Architecture

```
                    ┌──────────────────────┐
                    │       HEER UI        │
                    │ Chat / Voice / Dash  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   HEER ORCHESTRATOR  │
                    │ Intent + Planning    │
                    │ Agent Routing         │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
   AI AGENCY               BUSINESS              EXECUTION
   AGENTS                  INTELLIGENCE           AGENTS
        │                      │                      │
        ├── Strategy           ├── Research          ├── Developer
        ├── Sales              ├── Market Intel      ├── Automation
        ├── Consulting         ├── Lead Intel        ├── GitHub
        ├── Architecture       ├── Competitor        ├── DevOps
        ├── Delivery           └── Opportunity       └── Testing
        └── Finance
                               │
                    ┌──────────▼───────────┐
                    │       TOOL LAYER     │
                    │ APIs / Web / GitHub  │
                    │ n8n / DB / Cloud     │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ MEMORY + KNOWLEDGE   │
                    │ Client / Agency / AI │
                    │ Projects / Decisions │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ SECURITY & GOVERNANCE│
                    │ RBAC / Audit / Human │
                    │ Approval / Policies   │
                    └──────────────────────┘
```

---

## 2. Current Implementation (Actual, as-built)

### 2.1 Technology Stack

| Layer | Technology | Files |
|---|---|---|
| Backend | Python 3, stdlib-only HTTP server | `agent/chat.py`, `agent/main.py` |
| Intelligence | Regex/heuristic extraction from markdown vault | `agent/heer.py` |
| Frontend | Vanilla HTML/CSS/JS SPA, 11 views | `ui/index.html`, `ui/app.js`, `ui/style.css` |
| Memory | Markdown-file vault graph + JSON business registry | `agent/vault.py`, `agent/data.py`, `agent/business.py`, `businesses.json` |
| Learning | SQLite: `skills`, `executions`, `learnings`, `knowledge_gaps`, `skill_proposals` | `agent/skills.py` |
| Tools | 7 stdlib-only vault tools | `agent/tools.py` |
| Agents | 15 declarative fixture agents (data, not executable) | `agent/heer.py` `AGENTS` |
| Voice | ElevenLabs TTS, macOS Apple Speech ASR | `agent/voice.py`, `agent/asr_swift.swift` |
| Config | `.env` (ELEVENLABS_API_KEY, HEER_DEMO, INDEX_PATHS, OPENAI optional) | `.env` |
| Demo | 2 businesses (AI Agency, Sip & Slice) | `data/demo/`, `data/demo_businesses/` |
| Skills | 3 sources merged: heer.py fixtures + skills.py MASTER_SKILLS + JARVIS marketplace | `agent/heer.py`, `agent/skills.py`, `agent/jarvis_skills.py` |

### 2.2 Module Map

```
jarvis/
├── agent/
│   ├── main.py          # CLI entry, business switching
│   ├── chat.py          # HTTP server, chat endpoint, voice endpoints
│   ├── heer.py          # Intelligence layer: AGENTS, SKILLS, briefing, radar, client/project intel
│   ├── skills.py        # SkillEngine: SQLite learning engine, MASTER_SKILLS, auto_learn
│   ├── tools.py         # Tool registry: echo, clock, search, look, remind, hubs, stats
│   ├── vault.py         # Markdown vault graph (notes, clients, projects, reports)
│   ├── data.py          # Data root resolution, demo mode
│   ├── business.py      # Business registry + current business state
│   ├── jarvis_skills.py # JARVIS SKILL.md frontmatter loader
│   ├── voice.py         # ElevenLabs TTS
│   └── asr_swift.*      # macOS offline ASR helper
├── ui/
│   ├── index.html       # 11-view SPA
│   ├── app.js           # Rendering, API calls, chat, graph viz
│   └── style.css        # Dark premium theme
├── data/
│   ├── demo/            # AI Agency fixtures (clients, projects, notes, reports)
│   └── demo_businesses/ # Sip & Slice fixtures
├── scripts/             # Skill download / verify
├── businesses.json      # Business registry
└── skills-lock.json     # Marketplace lockfile
```

### 2.3 Data Flow (Current)

```
User message
  → agent/chat.py /api/chat
  → (prompt + vault context) → LLM
  → LLM may call agent/tools.py call_tool()
  → text response to UI
```

There is **no** orchestrator: no intent classification, no agent routing, no approval gating, no execution auditing.

### 2.4 Memory System (Current)

Vault graph (`agent/vault.py`):

- **Nodes**: `id`, `title`, `type` (note/clients/projects/reports), `text` (markdown body), `rel` (links)
- **Links**: `source_id`, `target_id`
- **Search**: ranking by query terms over node text
- **Hubs**: node degree counting
- **Per-business**: each business has its own vault under its `data_root`

### 2.5 Learning Engine (Current)

SQLite (`agent/skills.py`):

| Table | Purpose |
|---|---|
| `skills` | Skill defs: id, name, category, purpose, version, success_rate, executions, autonomy, status, risk_score, workflow, decision_logic, output, validation, dependencies, permissions, prerequisites, learning_path |
| `executions` | skill_id, success, duration_ms, context, created_at |
| `learnings` | title, type, detail (json: source/confidence/detail), created_at |
| `knowledge_gaps` | area, why, impact, action, status, created_at, closed_at |
| `skill_proposals` | name, reason, pattern, status, created_at |

`auto_learn()` scans vault for repeated patterns (proposal, report, plan…) and proposes new skills; detects knowledge gaps via markers ("unknown", "todo", "missing").

---

## 3. Target Architecture (Desired)

### 3.1 Component Specification

| Component | Status Now | Target | Owner |
|---|---|---|---|
| **Orchestrator** | ❌ Missing | Intent classification → agent routing → tool dispatch → approval gate → execute → verify → audit | `agent/orchestrator.py` |
| **Agent Registry** | ⚠️ Fixtures only | Executable agent definitions with permissions & approval levels | `agent/registry.py` |
| **Tool Registry** | ⚠️ 7 vault tools | Extensible registry: name, desc, I/O schema, permissions, risk, timeout, logging | `agent/tools.py` |
| **Memory** | ✅ Vault graph | Same + permission-aware access + client/agency/project/user categories | `agent/vault.py` |
| **Learning** | ✅ SQLite engine | Same + agent execution history table | `agent/skills.py` |
| **Approval System** | ⚠️ UI modal only | L0-L3 policy engine gating all state-changing actions | `agent/approvals.py` |
| **Audit/Observability** | ⚠️ Skill executions only | Full agent-execution trace: request→intent→agent→tools→outputs→approval→outcome | `agent/audit.py` |
| **CRM/Pipeline** | ❌ Missing (pipeline is a string KPI) | Leads → opportunities → proposals → won/lost stages with amounts | `agent/crm.py` |
| **Proposal/ROI** | ❌ Missing | Generator producing business-outcome-focused proposals + ROI models | `agent/proposal.py` |
| **Vertical Library** | ❌ Missing | Reusable industry templates (healthcare, manufacturing, …) | `data/verticals/` |
| **Finance Engine** | ❌ Missing | Revenue/cost/profit/margin/MRR/ARR per project | `agent/finance.py` |
| **Governance** | ❌ Missing | AI inventory, risk, controls, incidents, audit evidence | `agent/governance.py` |
| **Proactive Intel** | ❌ Missing | Scheduled scans → alerts ("7 prospects not contacted") | `agent/proactive.py` |
| **Auth/RBAC** | ❌ Missing | User roles, least-privilege, session security | — |
| **External Tools** | ❌ Missing | web_search, github, http, filesystem, docker, n8n, email, crm | — |

---

## 4. Gap Map

| Area | Current | Target | Gap | Priority |
|---|---|---|---|---|
| Orchestration | LLM direct call | Intent → route → tool plan | **HIGH** | P1 |
| Agent execution | 15 fixture dicts | Executable agents w/ permissions | **HIGH** | P1 |
| Approval enforcement | UI modal (no backend) | L0-L3 policy gate | **HIGH** | P1 |
| Audit trail | Skill execs only | Full agent-execution history | **HIGH** | P1 |
| Tool coverage | 7 vault tools | Registry + external tools | MEDIUM | P2 |
| Sales pipeline | string KPI | Structured lead→won CRM | MEDIUM | P2 |
| Proposals/ROI | skill fixture | Generator | MEDIUM | P2 |
| Finance | finance.md K:V parse | Revenue/cost/margin engine | MEDIUM | P3 |
| Verticals | — | 10 industry templates | LOW | P5 |
| Governance | empty tab | AI inventory/risk/controls | MEDIUM | P4 |
| Proactive | — | Scheduled alerts | LOW | P5 |
| Auth/RBAC | business switch only | Roles + secrets mgmt | MEDIUM | P4 |

---

## 5. Implementation Plan

### Phase 1 — Foundation (P1)
Add (no destructive changes):

1. `agent/orchestrator.py` — intent classification, agent routing, tool dispatch, verify
2. `agent/registry.py` — AGENT_REGISTRY (13 AI-Agency agents) + TOOL_REGISTRY (with risk/permissions)
3. `agent/approvals.py` — L0 read / L1 prepare / L2 execute / L3 critical policy engine
4. `agent/audit.py` — SQLite audit log: request→intent→agent→tools→outcome
5. `data/agency/` — seed AI-agency file model: leads/, opportunities/, proposals/, clients/, projects/, finance.md
6. Wire approval modal + activity feed in `ui/app.js`
7. Self-test: `python3 -m agent.orchestrator --self-test`

### Phase 2 — AI Agency Core (P2)
- Market research agent (web_search integration)
- Lead intelligence (company research, decision-maker id)
- AI discovery/consulting (process mapping, opportunity id, ROI)
- Solution architect (model selection, architecture)
- Proposal agent (SOW, pricing, ROI models)
- Project delivery agent (status, risk, forecast)

### Phase 3 — Execution (P3)
- Developer agent (code gen/modify/test)
- GitHub agent (repo, PR, CI/CD)
- Automation agent (n8n, webhooks, APIs)
- Deployment & testing agents

### Phase 4 — Governance & Scale (P4)
- AI inventory/risk management
- Approval workflows (already P1, extend)
- Audit dashboard
- Multi-tenant / auth

### Phase 5 — Scale (P5)
- Vertical solution library (10 industries)
- Productization engine
- Marketing & finance engines
- Client portal

---

## 6. Design Principles

1. **Business-first** — every technical recommendation answers: business problem → value → cost → risk → time → success metric
2. **Minimum agents** — never route to all agents; use the minimum required
3. **Modular** — agents, tools, skills, memory, orchestration are separate modules
4. **Backwards compatible** — existing fixtures stay; new modules augment
5. **Secure by design** — secrets in env, least privilege, tool permissions, audit logging
6. **No fabrication** — distinguish Known / Inferred / Estimated / Unknown
7. **Reusable** — every completed project is evaluated for reuse/template/productization

---

_Document version: 1.0 — 2026-09-08_