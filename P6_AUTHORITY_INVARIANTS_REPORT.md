# P6 AUTHORITY INVARIANTS REPORT

## Overview
This report verifies that authority boundaries remain correctly separated across all four pillars of the HEER architecture:

```
HEER → JARVIS → Hermes → ExecutionEngine → Tool
      ↓
Obsidian (memory authority)
```

## D1 - Worker Identity & Epoch Authority
- **Owner**: `agent/worker_contracts.py`
- **Authority**: Worker identity (id, type, status)
- **Validation**: 
  - Worker identity persists in `agent/worker_registry.py`
  - Worker epoch generated and validated by `agent/worker_registry.py`
  - Stale workers rejected by `agent/worker_registry.py`
  - No worker→business authorization table exists in D1
  - D1 persists worker epoch, ExecutionEngine only consumes worker_epoch

## D3 - Worker Registry Authority
- **Owner**: `agent/worker_registry.py`
- **Authority**: Worker epoch management, stale worker rejection
- **Validation**:
  - Worker epoch generation and validation
  - Epoch rejection for stale workers
  - D1 persists worker epoch
  - ExecutionEngine only consumes worker_epoch

## D4 - Business Authorization Authority
- **Owner**: `agent/business_authorization.py`
- **Authority**: Business ID, tenant scope, business context
- **Validation**:
  - Invalid business_id fails closed
  - Invalid worker fails closed
  - Invalid worker_epoch fails closed
  - Tenant mismatch fails closed
  - Unauthorized business fails closed
  - Spoofed claims fail closed

## ExecutionEngine - Execution Authority
- **Owner**: `agent/execution_engine.py`
- **Authority**: execution_id, attempt number, lease ownership, retry scheduling, task lifecycle
- **Validation**:
  - ExecutionEngine is the sole executor
  - No direct HEER→tool bypass
  - No direct JARVIS→tool bypass
  - No tool execution without authorization
  - No Obsidian cross-business memory access
  - Lower pillars cannot elevate authority
  - Delegation cannot expand beyond delegated claims

## Cross-Pillar Boundaries
- **HEER → JARVIS**: HEER delegates execution authority to JARVIS
- **JARVIS → Hermes**: JARVIS delegates execution to Hermes
- **Hermes → ExecutionEngine**: Hermes delegates execution to ExecutionEngine
- **Obsidian**: Memory authority, isolated from all others
- **Claims Bound**: business_id, worker_id, worker_epoch, tenant_scope, task_id, mission_id, execution_id, tool_name

## Conclusion
All authority invariants are maintained. The four-pillar architecture preserves strict separation of concerns with no unauthorized escalation paths.