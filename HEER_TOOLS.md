# HEER Tool System

> Complete catalog of the current tool registry and the target modular tool registry with permissions, risk levels, and timeout/error metadata.

---

## 1. Current Tool Registry (`agent/tools.py` — 7 tools)

All current tools are **stdlib-only, vault-centric, and read-safe** with one write (remind). They accept `(name, args, business_id)` and return a JSON-serializable dict with `tool` and `ok` flags.

| Tool | Description | Params | Risk | Access |
|---|---|---|---|---|
| `echo` | Echo text back (testing) | `text: string` | None | read |
| `clock` | Current date and time | — | None | read |
| `search` | Search vault; returns matching nodes + snippet | `query: string`, `limit: int` (default 5) | Low | read |
| `look` | Read full node by exact title | `title: string` | Low | read |
| `remind` | Save a reminder/note into vault | `text: string`, `when: string` (opt), `title: string` (opt) | Low | write |
| `hubs` | Top connected vault nodes ("what's most important?") | `limit: int` (default 5) | Low | read |
| `stats` | Vault node/link/type counts | — | Low | read |

### Call pattern

```python
from agent.tools import call_tool, tool_descriptions

result = call_tool("search", {"query": "healthcare ai"}, business_id="ai_agency")
# => {"tool": "search", "ok": True, "results": [...]}

# failure is never fatal:
# => {"tool": name, "ok": False, "error": "..."}
```

---

## 2. Target Tool Registry Schema

Expansion per the master prompt §7: every tool must be declared with full metadata so the orchestrator, approval engine, and audit log can gate it safely.

```python
{
    "name": str,                    # unique tool id
    "description": str,             # LLM-facing description
    "category": str,                # vault | web | github | filesystem | terminal | http | database | email | calendar | crm | slack | telegram | whatsapp | n8n | cloud | docker | monitoring | document | voice | home
    "input_schema": {field: type},  # params + types
    "output_schema": str,           # JSON shape description
    "permissions_required": [str],  # e.g. ["read:clients"], ["write:proposals"]
    "risk_level": str,              # none | low | medium | high | critical
    "approval_level": int,          # 0=Read, 1=Prepare, 2=Execute, 3=Critical
    "timeout_ms": int,
    "logging": bool,                # whether tool I/O is persisted to audit
    "error_handling": str,          # policy: "return-ok-false" | "raise" | "retry"
    "enabled": bool,
    "source": str,                  # "builtin" | "jarvis" | "custom"
}
```

---

## 3. Tool Roadmap (Priority Order)

### Phase 1 — Foundation (wire existing tools + metadata)

| Tool | Status | Approval | Notes |
|---|---|---|---|
| `echo` | ✅ exists | L0 | Keep |
| `clock` | ✅ exists | L0 | Keep |
| `search` | ✅ exists | L0 | Keep |
| `look` | ✅ exists | L0 | Keep |
| `remind` | ✅ exists | L1 (write) | Keep |
| `hubs` | ✅ exists | L0 | Keep |
| `stats` | ✅ exists | L0 | Keep |
| `vault_write` | ➕ (alias of remind, generalized) | L1 | prepare notes/docs |
| `vault_archive` | ➕ | L2 | move node to archive dir |

**Add metadata** to all existing tools: risk_level, approval_level, permissions, logging, timeout.

### Phase 2 — AI Agency Core (external intelligence)

| Tool | Approval | Risk | Purpose |
|---|---|---|---|
| `web_search` | L0 | Low | Web research (DuckDuckGo) |
| `http_get` | L0 | Medium | Fetch public documents/APIs (SSRF-protected) |
| `lead_research` | L0 | Low | Company research → decision-makers, firmographics |
| `opportunity_score` | L0 | Low | Score leads by ICP fit |
| `proposal_draft` | L1 | Clean | Generate proposals (requires approval to send) |
| `roi_calc` | L0 | Low | Business case / ROI models (assumptions flagged) |
| `crm_read` | L0 | Low | Read pipeline/leads from memory |
| `crm_write` | L2 | Medium | Create/update lead, opportunity, customer records |

### Phase 3 — Execution

| Tool | Approval | Risk | Purpose |
|---|---|---|---|
| `code_write` | L1 | High | Write/modify code files |
| `code_review` | L0 | Low | Analyze code |
| `github_read` | L0 | Low | Repos, issues, PRs (read) |
| `github_write` | L2 | High | Create PR, push branch, merge |
| `ci_cd_run` | L2 | High | Trigger pipelines |
| `docker_run` | L2 | High | Build/run containers |
| `n8n_deploy` | L2 | Medium | Deploy workflow to n8n |
| `terminal_exec` | L2 | Critical | Arbitrary shell (sandboxed, allowlist) |

### Phase 4 — Governance & Communications

| Tool | Approval | Risk | Purpose |
|---|---|---|---|
| `email_send` | L2 | Medium | Send email |
| `calendar_write` | L2 | Medium | Schedule meetings |
| `slack_send` | L2 | Medium | Post to channels |
| `telegram_send` | L2 | Medium | Message |
| `whatsapp_send` | L2 | Medium | Message |
| `audit_read` | L0 | Low | Read audit trail |
| `policy_write` | L3 | Critical | Modify governance policies |

### Phase 5 — Scale

| Tool | Approval | Risk | Purpose |
|---|---|---|---|
| `vertical_load` | L0 | Low | Load vertical template |
| `case_study_gen` | L1 | Low | Generate case study |
| `productize_score` | L0 | Low | Evaluate project → product potential |
| `finance_write` | L2 | Medium | Record revenue/cost |
| `client_portal_sync` | L2 | Medium | Sync portal data |

---

## 4. Approval Level Definitions (Reused)

| Level | Name | Rule | Example |
|---|---|---|---|
| **0** | Read | No approval | Search, analyze, summarize |
| **1** | Prepare | Approval before external action | Draft email, draft proposal, draft code change |
| **2** | Execute | Approval required | Send email, deploy, modify production, create customer record |
| **3** | Critical | Explicit confirmation | Financial transactions, destructive actions, production DB changes, credential changes |

---

## 5. Tool Security Requirements (All Tools)

1. **Secrets never exposed to the model** — held by server env/secret manager
2. **Least privilege** — tool only gets tokens scoped to its function
3. **SSRF protection** — `http_get`/`web_search` block private IP ranges
4. **Input validation** — every param validated before use
5. **Output validation** — schema checks on responses
6. **Rate limiting** — per-tool and per-user caps
7. **Audit logging** — every tool I/O persisted (unless logging=False for secrets)
8. **Error handling** — `ok:false` + error string, never crashes conversation
9. **Timeout** — every external call bounded
10. **Command execution controls** — `terminal_exec` allowlist + sandbox dir

---

_Document version: 1.0 — 2026-09-08_