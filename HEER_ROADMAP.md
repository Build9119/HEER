# HEER Roadmap

> Phased implementation plan transforming the existing HEER platform into the AI Agency Operating Partner.

---

## 0. Backlog Summary

| Phase | Name | Focus | Status |
|---|---|---|---|
| **P1** | Foundation | Orchestrator, agent registry, approval engine, audit log, agency seed data | 🔜 Implemented in this build |
| **P2** | AI Agency Core | Market research, lead intelligence, discovery, architecture, proposals, ROI | Planned |
| **P3** | Execution | Developer, GitHub, automation, deployment, testing agents | Planned |
| **P4** | Governance | AI inventory, risk management, approval workflows, audit dashboard | Planned |
| **P5** | Scale | Vertical library, productization, marketing, finance, client portal, multi-tenant | Planned |

---

## Phase 1 — Foundation (The "Operating System")

> Objective: establish the state machine that every future AI-Agency capability runs on. Nothing here is a business vertical; it's the plumbing.

### Scope

| Area | Deliverable | Module |
|---|---|---|
| **Orchestration** | Intent classification → agent selection → tool dispatch → verification → response | `agent/orchestrator.py` |
| **Agent Registry** | 13 AI-Agency agents with routing metadata (intents, tools, skills, permissions, approval) | `agent/registry.py` |
| **Approval Engine** | L0-L3 human-approval gating for every state-changing action | `agent/approvals.py` |
| **Audit Log** | SQLite `agent_executions` — full request→intent→agent→tools→approval→outcome trace | `agent/audit.py` |
| **Agency Data** | `data/agency/` file model: leads, opportunities, proposals, clients, projects, finance | `data/agency/` |
| **API Wiring** | POST `/api/execute`, GET `/api/executions`, GET `/api/approvals/pending`, POST `/api/approvals/respond` | `agent/main.py` |
| **UI Wiring** | Approval modal → real endpoint; executions feed in activity view; agency data in clients/projects views | `ui/app.js` |

### Implementation Details

#### 1. `agent/registry.py`
- `AGENT_REGISTRY`: 13 agents (ceo, sales, discovery, architect, proposal, roi, developer, automation, github, delivery, finance, marketing, governance), each:
  - `id`, `name`, `role`, `mission`
  - `intents`: keyword lists used by orchestrator router
  - `tools`: tool registry ids (reuse `agent/tools.py`)
  - `skills`: skill library ids
  - `permissions`: e.g. `["read:clients"]`, `["write:proposals"]`
  - `approval_level`: default L0-L3
  - `autonomy`: 0-5 (reuse existing model)
  - `status`: active

#### 2. `agent/orchestrator.py`
- `route(request)` → classify intent against registry agent intents (keyword scoring)
- `plan(request, agent)` → pick minimal tools needed (rule-based, no extra agents)
- `execute(plan, business_id)` → for each tool: check approval → record audit → call tool → verify result
- `handle(request, business_id)` → full pipeline: route → plan → execute → return structured response
- `--self-test` CLI: runs 3 canned scenarios through the pipeline

#### 3. `agent/approvals.py`
- `APPROVAL_LEVELS`: L0=Read, L1=Prepare, L2=Execute, L3=Critical
- `requires_approval(level)` → bool
- `check(level, action)` → `{"approved": bool, "reason": str}` (L0 auto-pass; L1+ pending)
- SQLite `approvals` table: id, request_id, level, action, status(pending/approved/denied), created_at, responded_at
- `pending_approvals()`, `respond(approval_id, decision)`

#### 4. `agent/audit.py`
- SQLite `agent_executions`: id, request, intent, agent_id, tools (json), inputs (json), outputs (json), approval (json), success, lat_ms, created_at
- `record()`, `recent()`, `metrics()` (success rate, failure rate, avg latency, tool failures, approvals pending, total)

#### 5. `data/agency/` seed
- `leads/` — 3 sample leads with firmographic fields
- `opportunities/` — 3 staged opportunities (qualification, proposal, negotiation)
- `proposals/` — 1 sample proposal outline
- `clients/` — reuse existing demo clients (or link)
- `projects/` — reuse existing demo projects
- `finance.md` — K:V finance (already parsed by heer.py)
- All readable by the existing vault scanner (`get_vault`).

### Acceptance Criteria (P1)

- [ ] `python3 -m agent.orchestrator --self-test` passes (3 scenarios: read, prepare-approval, execute-approval)
- [ ] `GET /api/executions` returns audit rows with intent/agent/tools/outcome
- [ ] `GET /api/approvals/pending` returns any L1+ actions awaiting approval
- [ ] UI approval modal shows real pending approvals and can approve/deny
- [ ] No existing endpoint broken (chat/status/graph/briefing remain working)

---

## Phase 2 — AI Agency Core

> Objective: move from "knows the agency exists" to "runs the business development loop."

| Capability | What HEER can now do |
|---|---|
| Market Research Agent | `web_search` → scan vertical → competitive landscape → opportunity brief |
| Lead Intelligence | target-account lists → firmographics → decision-makers → qualification score |
| AI Discovery Agent | process discovery → current-state → pain points → AI/automation opportunity map |
| AI Solution Architect | model selection, architecture patterns (RAG, agents, workflows), cost model |
| Proposal Agent | discovery report → executive summary → SOW → pricing model → ROI section |
| ROI / Business Case | operating cost → automation potential → savings → payback → margin |
| Project Delivery Agent | status updates, milestone risk, delivery forecast |
| Finance (read) | revenue/pipeline/margin dashboard from finance.md + project intel |

**New modules**: `agent/research.py`, `agent/crm.py`, `agent/discovery.py`, `agent/proposal.py`, `agent/roi.py`
**New tools**: `web_search`, `http_get`, `lead_research`, `opportunity_score`, `proposal_draft`, `roi_calc`, `crm_read`
**API**: `/api/discover`, `/api/proposal/generate`, `/api/opportunities`

---

## Phase 3 — Execution

> Objective: HEER builds and ships, not just advises.

| Agent | Capability |
|---|---|
| Developer | write/modify/debug/test code in workspace |
| GitHub | repo analysis, issues, branches, PRs, CI/CD read |
| Automation | design n8n workflows (trigger/inputs/processing/outputs/error/retry/logging) |
| Deployment | docker build/run, env-staged deploys |
| Testing | API tests, workflow validation, QA gates |

**New tools**: `code_write` (L1), `github_read` (L0), `github_write` (L2), `docker` (L2), `n8n` (L2), `terminal_exec` (L3, allowlisted)
**New modules**: `agent/developer.py`, `agent/github_agent.py`, `agent/n8n.py`

---

## Phase 4 — Governance

> Objective: make HEER a compliant AI platform, not just an automator.

| Area | Deliverable |
|---|---|
| AI Inventory | registry of every AI system/agent/model HEER knows about |
| Risk Assessment | per-inventory-item risk scoring (technical, data, operational, regulatory) |
| Policies & Controls | governance policy docs + control assertions |
| Approval Workflows | extend P1 approvals → policy-driven routing |
| Audit Dashboard | full traceability view: who approved what, when, why |
| Incidents | AI incident register with status/resolution |

**New modules**: `agent/governance.py`, `agent/policies.py`
**New tables**: `ai_inventory`, `ai_risks`, `ai_controls`, `ai_incidents`

---

## Phase 5 — Scale

> Objective: turn the agency into a repeatable, productized, multi-tenant machine.

| Area | Deliverable |
|---|---|
| Vertical Library | 10 industry templates (healthcare, manufacturing, retail, financial, professional services, real estate, hospitality, cybersecurity, IT services, education) — each with profile, pains, opportunities, integrations, ROI, risks, governance, proposal |
| Productization | per-project scoring → reusable solutions, templates, agents, automations, SaaS |
| Marketing Engine | case studies, LinkedIn content, industry reports from real project data |
| Finance Engine | revenue/cost/profit per project, MRR/ARR, CAC/LTV |
| Client Portal | client-facing view of their project, status, reports |
| Multi-Tenant | per-client data isolation, roles, audit |

**New modules**: `agent/verticals.py`, `agent/productize.py`, `agent/finance_engine.py`, `agent/portal.py`

---

## Guiding Principles (Re-stated)

1. **Smallest safe change** — never break the running system.
2. **Backwards compatible** — existing endpoints/views keep working; new modules augment.
3. **Business-first** — every feature answers: problem → value → cost → risk → time → metric.
4. **No fabrication** — Known/Inferred/Estimated/Unknown labels on all intelligence.
5. **Human in the loop** — L0 auto, L1+ approval, L3 explicit.
6. **Observable** — every execution traceable from request to result.
7. **Productizable** — each completed project is candidate for reuse.

---

_Document version: 1.0 — 2026-09-08_