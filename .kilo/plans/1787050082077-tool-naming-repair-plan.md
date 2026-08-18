# HEER Tool Naming Mismatch Repair Plan

## Goal
Make the existing HEER tool architecture internally consistent: registry → planner → dispatcher → implementation.

## Status
DISCOVERED — DEFECT CONFIRMED

## Root Cause
`agent/registry.py` uses short tool names (`code_read`, `docker`, `terminal_exec`).
`agent/orchestrator.py` and `agent/tools.py` use prefixed names (`developer_code_read`, `deploy_docker`, `terminal_terminal_exec`).
`plan()` silently drops Phase 3 tools; `_dispatch()` would reject them even if planned.

## Decision
Make short names canonical. Module routing is metadata, not part of public tool identity.

## Tasks

### 1. Update `agent/orchestrator.py`
- Replace `_MODULE_TOOLS` prefixed set with canonical short names:
  `mission_create`, `mission_list`, `mission_get`,
  `developer_code_read`, `developer_code_write`, `developer_test_run`,
  `github_github_read`, `github_github_write`,
  `n8n_n8n`, `deploy_docker`, `terminal_terminal_exec`
  →
  `mission_create`, `mission_list`, `mission_get`,
  `code_read`, `code_write`, `test_run`,
  `github_read`, `github_write`,
  `n8n`, `docker`, `terminal_exec`
- Keep `_dispatch()` behavior unchanged; it already routes non-payload tools through `_call_tool()`.

### 2. Update `agent/tools.py`
- Change `_register()` so `_MODULE_TOOLS` keys use the short tool name from each module's dict instead of `f"{module_name}_{tname}"`.
- Preserve `"module": module_name` metadata in the tool spec for observability.
- This makes `TOOLS` and `call_tool()` resolve short names directly.

### 3. Add explicit unavailable-tool diagnostics
- In `orchestrator.plan()`, when a tool is not in `_PAYLOAD_TOOLS`, `_VAULT_TOOLS`, or `_MODULE_TOOLS`, append a diagnostic step:
  `{"tool": t, "status": "TOOL_UNAVAILABLE", "reason": "not_registered"}`
- In `call_tool()`, when `name not in TOOLS`, return:
  `{"tool": name, "ok": False, "error": "Tool unavailable: not registered", "code": "TOOL_UNAVAILABLE"}`

### 4. Add regression tests
- Create `tests/tool_routing_test.py`:
  - For each affected agent/tool pair, assert `plan()` includes the short tool name.
  - Assert `call_tool("code_read", {"path": "agent/main.py"})` returns `"ok": True` or a known demo/dry-run status, never `"Unknown tool"`.
  - Assert `call_tool("unknown_tool_xyz", {})` returns `"code": "TOOL_UNAVAILABLE"`.

### 5. Validate
- Run `python3 -m unittest discover -s tests -p '*_test.py'`
- Run `python3 -m agent.orchestrator --self-test`
- Run `python3 -m agent.developer --self-test`
- Run `python3 -m agent.github_agent --self-test`
- Run `python3 -m agent.n8n --self-test`
- Run `python3 -m agent.deploy --self-test`
- Run `python3 -m agent.terminal --self-test`

## Files Changed
- `agent/orchestrator.py`
- `agent/tools.py`
- `tests/tool_routing_test.py` (new)

## Security
No security impact. Short names preserve existing approval levels and execution gates.

## Tenancy
No tenancy impact. `business_id` propagation unchanged.

## Risks
- Any external caller using prefixed names will break. Search shows prefixed names appear only in `agent/orchestrator.py` and `agent/tools.py`, so risk is contained.
- `tools.py` module imports remain inside `try/except`, preserving current import-failure behavior.

## Next Step
Implementation agent to execute tasks 1–5 in order, then report test results.
