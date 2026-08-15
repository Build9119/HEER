# HEER Skills Library

> Complete catalog of all skills available to HEER across all three sources, plus the gap analysis for AI-Agency lifecycle coverage.

---

## 1. Skill Sources

HEER merges skills from three sources:

| Source | Location | Loader |
|---|---|---|
| **Core HEER Skills** (hard-coded) | `agent/heer.py` `SKILLS[]` | module import |
| **Master Skill Set** (SQLite persisted) | `agent/skills.py` `MASTER_SKILLS[]` | `SkillEngine._seed()` |
| **JARVIS Marketplace** | `.agents/skills/*/SKILL.md` | `agent/jarvis_skills.py` |

All three are merged into the runtime skill library used by the learning engine, governance, and dashboard.

---

## 2. Core HEER Skills (`agent/heer.py`)

| ID | Name | Version | Success | Execs | Autonomy | Owner |
|---|---|---|---|---|---|---|
| `enterprise_ai_assessment` | Enterprise AI Assessment | 2.4 | 96% | 48 | ASSIST | Delivery Agent |
| `proposal_generation` | Proposal Generation | 1.8 | 92% | 31 | ASSIST | Sales Agent |
| `market_scan` | Market Scan | 3.1 | 94% | 22 | EXECUTE | Research Agent |
| `client_health` | Client Health Assessment | 1.2 | 90% | 15 | ASSIST | Client Success Agent |
| `margin_analysis` | Margin Analysis | 1.0 | 88% | 9 | ASSIST | Financial Agent |
| `ceo_briefing` | CEO Briefing | 2.1 | 95% | 40 | ASSIST | Chief-of-Staff Agent |

---

## 3. Master Skill Set (`agent/skills.py` — 41 skills)

### 3.1 Strategy & Leadership (6)

| ID | Name | Purpose |
|---|---|---|
| `enterprise_ai_assessment` | Enterprise AI Assessment | Assess client AI readiness and produce structured assessment report |
| `ceo_briefing` | CEO Briefing | Synthesize agency state into daily executive briefing |
| `business_health` | Business Health Score | Score overall business health across dimensions |
| `revenue_forecast` | Revenue Forecasting | Project future revenue from pipeline and history |
| `pricing_strategy` | Pricing Strategy | Recommend pricing models for engagements |
| `product_strategy` | Product Strategy | Shape product roadmap from market/client signals |

### 3.2 Sales & Growth (7)

| ID | Name | Purpose |
|---|---|---|
| `proposal_generation` | Proposal Generation | Generate client proposal from context + pricing |
| `opportunity_scoring` | Opportunity Scoring | Score opportunities by Impact × Feasibility × Urgency × Strategic Value |
| `lead_nurturing` | Lead Nurturing | Maintain lead engagement cadence |
| `pitch_deck` | Pitch Deck Generation | Build client-facing pitch decks |
| `contract_review` | Contract Review | Flag risky clauses in contracts |
| `renewal_management` | Renewal Management | Manage client renewals |
| `client_health` | Client Health Assessment | Score account health across delivery/sentiment/revenue |

### 3.3 Research & Intelligence (4)

| ID | Name | Purpose |
|---|---|---|
| `market_scan` | Market Scan | Scan market for competitors, trends, opportunities |
| `competitor_analysis` | Competitor Analysis | Deep-dive competitor capabilities and positioning |
| `trend_detection` | Trend Detection | Detect emerging trends from intelligence |
| `sentiment_analysis` | Sentiment Analysis | Assess sentiment from client/feedback data |

### 3.4 Delivery & Operations (6)

| ID | Name | Purpose |
|---|---|---|
| `delivery_management` | Delivery Management | Track project delivery and quality gates |
| `risk_mitigation` | Risk Mitigation | Identify and mitigate delivery risks |
| `resource_planning` | Resource Planning | Allocate people/time across projects |
| `automation_design` | Automation Design | Design automation workflows |
| `milestone_tracking` | Milestone Tracking | Track project milestones |
| `margin_analysis` | Margin Analysis | Analyze project profitability |

### 3.5 Finance (3)

| ID | Name | Purpose |
|---|---|---|
| `cashflow_analysis` | Cashflow Analysis | Monitor cashflow position |
| `invoice_management` | Invoice Management | Manage invoicing cycle |
| `margin_analysis` | Margin Analysis | Project margin tracking |

### 3.6 Marketing & Content (3)

| ID | Name | Purpose |
|---|---|---|
| `content_generation` | Content Generation | Generate marketing content |
| `social_media_planning` | Social Media Planning | Plan social media cadence |
| `meeting_briefing` | Meeting Briefing | Prepare briefing for meetings |

### 3.7 Engineering (4)

| ID | Name | Purpose |
|---|---|---|
| `model_routing` | Model Routing | Route LLM calls to optimal model |
| `rag_optimization` | RAG Optimization | Improve retrieval quality/cost |
| `code_review` | Code Review | Review code changes for quality |
| `report_generation` | Report Generation | Generate structured reports |

### 3.8 Security & Governance (4)

| ID | Name | Purpose |
|---|---|---|
| `threat_detection` | Threat Detection | Detect security anomalies |
| `policy_enforcement` | Policy Enforcement | Enforce governance policies |
| `governance_audit` | Governance Audit | Audit autonomous actions for compliance |
| `risk_assessment` | Risk Assessment | Assess AI implementation risks |

### 3.9 Learning & Growth (4)

| ID | Name | Purpose |
|---|---|---|
| `skill_discovery` | Skill Discovery | Discover new skill opportunities |
| `knowledge_gap_detection` | Knowledge Gap Detection | Find knowledge gaps in vault |
| `pattern_recognition` | Pattern Recognition | Detect repeated workflows |
| `self_improvement` | Self-Improvement | Improve own skill definitions |

---

## 4. JARVIS Marketplace Skills (30 — from `.agents/skills/`)

| Skill | Category (derived) | Typical Use |
|---|---|---|
| `api-test` | Development | API endpoint testing |
| `code-generator` | Development | Multi-language code generation |
| `code-review` | Development | Systematic code review |
| `content-generator` | Content | Shopping/recommendation copy writing |
| `contract-review` | Research | Legal contract CUAD analysis |
| `database-admin` | Operations | Database administration |
| `docker-cli` | Operations | Docker container management |
| `document-parser` | Productivity | Document parsing |
| `email-sender` | Communication | Email sending |
| `file-manager` | Productivity | Batch file ops / cleanup |
| `github` | Development | GitHub via gh CLI |
| `healthcheck` | Productivity | Track water & sleep |
| `image-generate` | Content | Image generation via script |
| `k8s` | Operations | Kubernetes management |
| `keyword-research` | Research | SEO keyword research |
| `meeting-summary` | Productivity | Meeting recordings → minutes |
| `monitoring` | Operations | System monitoring |
| `note-taker` | Productivity | Note-taking (Cornell/Zettelkasten) |
| `pdf-processor` | Productivity | PDF text/translation/overview |
| `project-manager` | Productivity | Project management tasks |
| `report-generator` | Productivity | Structured HTML reports |
| `security-audit` | Operations | Security scanning & fixes |
| `session-logs` | Communication | Search own session logs |
| `social-media` | Communication | Social media management |
| `speech-to-text` | Content | Whisper transcription |
| `text-to-speech` | Content | TTS voice synthesis |
| `translate-agent` | Productivity | Translation/summarization |
| `video-processor` | Content | Video processing |
| `weather` | Research | Weather forecasts |
| `web-search` | Research | Web search via DuckDuckGo |

---

## 5. AI-Agency Lifecycle Gap Analysis

### Lifecycle: Market Intel → Leads → Discovery → Proposal → Delivery → Repeat

| Lifecycle Stage | Covered by Existing Skill? | Gap |
|---|---|---|
| Market Intelligence | ✅ `market_scan`, `competitor_analysis`, `trend_detection` | — |
| Target Account ID | ⚠️ Partially (`opportunity_scoring`) | No formal ICP/account-firmographic scoring |
| Lead Generation | ⚠️ `lead_nurturing` | No list-building / enrichment skill |
| Prospect Research | ⚠️ `keyword-research`, `web-search` (marketplace) | No company-decision-maker research skill |
| AI Opportunity Discovery | ✅ `enterprise_ai_assessment` | Could be strengthened with process-mapping step |
| AI Consulting / Discovery | ⚠️ | No current-state/pain-point/future-state template skill |
| Solution Architecture | ❌ | No architecture-design, model-selection, integration-design skill |
| Proposal / ROI | ⚠️ `proposal_generation`, `pricing_strategy` | No ROI-model builder (cost savings, payback, margin) |
| Client Acquisition | ✅ `pitch_deck`, `contract_review`, `opportunity_scoring` | — |
| Solution Build | ⚠️ `code-generator`, `code-review`, `github` | No end-to-end build-then-deploy skill |
| Automation | ⚠️ `automation_design` | No n8n/Make/PowerAutomate specific builder |
| Testing | ⚠️ `api-test` | No QA harness for AI agent/workflow testing |
| Deployment | ⚠️ `docker-cli`, `k8s`, `monitoring` | No CI/CD pipeline skill |
| Client Delivery | ✅ `delivery_management`, `milestone_tracking`, `client_health` | — |
| Monitoring | ⚠️ `monitoring` | No AI-specific cost/latency/success monitoring |
| Support | ⚠️ `meeting_briefing` | No support-ticket triage skill |
| Case Study | ❌ | No case-study generator from project data |
| Repeat/Productize | ❌ | No productization-reuse evaluator |
| Scale | ❌ | No vertical-solution template library |

### Priority-Ordered Missing Skills (for Phase 2+)

1. **ROI / Business Case Builder** — current cost → automation potential → savings → payback
2. **AI Discovery Report Generator** — current state → pain points → opportunities → roadmap
3. **Solution Architecture Designer** — model selection, RAG, integration, security, cost
4. **Lead Intelligence Researcher** — company research, decision-makers, qualification score
5. **Prospect Outreach Generator** — email/message sequence per ICP
6. **Case Study Generator** — from project data → client-ready story
7. **Productization Evaluator** — reuse/template/SaaS scoring per completed project
8. **n8n Workflow Builder** — agentic trigger→actions→error-handling→logging automation

---

## 6. Skill Schema (All Skills)

```python
{
    "id": str,
    "name": str,
    "category": str,          # Strategy/Sales/Research/Delivery/Finance/...
    "purpose": str,
    "version": str,
    "success_rate": float,
    "executions": int,
    "autonomy": int,          # 0=OBSERVE ... 5=ADAPTIVE
    "status": str,            # learning | validated
    "inputs": [str],
    "tools": [str],
    "workflow": [str],
    "decision_logic": str,
    "output": str,
    "validation": str,
    "dependencies": [str],
    "permissions": [str],     # e.g. read:clients, write:reports
    "risk": str,              # low | medium | high
    "owner": str,
    "last_validated": str,
    "learning_path": [str] (optional),
    "prerequisites": [str] (optional),
}
```

---

_Document version: 1.0 — 2026-09-08_