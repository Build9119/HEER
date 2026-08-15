# HEER Phase 3.8 Implementation Plan

## 1. Executive Summary

**Why Phase 3.8 Exists:**
Phase 3.8 delivers Remote Worker Transport capabilities for HEER, enabling HEER to communicate with remote worker processes beyond the in-process and subprocess capabilities of Phase 3.7. This is the first transport that enables **remote** worker execution, addressing the need for distributed worker management in production deployments.

**What Capability It Introduces:**
Remote Worker Transport (RWT) with the following capabilities:
- HTTP/JSON over TLS protocol for remote communication
- mTLS authentication with control-plane CA
- Bounded transport queue with EE pull model for backpressure
- Registry-authoritative worker epochs and SQLite persistence
- JSONL event emission over same channel
- EE-only governance boundary preservation
- No shared workers (tenant isolation at worker instance level)
- Worker registration/heartbeat/departure lifecycle

**What Remains Frozen:**
- Phase 3.7 SubprocessTransport remains unchanged and operational
- ExecutionEngine retains sole authority for execution_id, attempt lifecycle, leases, retries, task state, cancellation, governance, and final persistence
- Worker capabilities remain descriptive only (never authorization)
- No second execution engine or authorization authority
- tenant_scope remains hard isolation boundary
- All 330 existing tests remain green

**What Phase 3.8 Does NOT Change:**
- No modifications to Production code
- No modifications to existing tests
- No modifications to dependencies
- No modifications to Phase 3.7
- No modifications to architecture decision documents
- No modifications to decision register
- No RemoteWorkerTransport implementations in this phase (only planning)
- No implementation of Phase 3.8 infrastructure until approval

## 2. Current Baseline

**Phase 3.7 Frozen State:**
- SubprocessTransport (30 tests, all passing)
- WorkerRegistry (8 public methods, descriptive-only, no persistence)
- WorkerMatcher (deterministic-first-eligible, registry-only, no policy authority)
- HermesAdapter (pure mapping seam)
- ExecutionEngine (sole authority for execution/lease/retry/task/state/governance)
- WorkerFabric contracts (WorkerIdentity, WorkerCapabilities, WorkerLiveness)

**Test Suite Status:**
- Full suite: 330 passed / 0 failed / 1 warning (cosmetic cleanup noise only)
- Previously failing test (`test_worker_crash_recovery`) now passes
- All Phase 3.7 tests continue to pass

**D1-D10 Resolution Status:**
- All 10 architecture decisions explicitly resolved by Architecture Owner
- No blockers remaining on architectural decisions
- Ready for implementation planning

**Architecture Gate Approval:**
- Phase 3.8 architecture gate approved
- All frozen invariants preserved
- No implementation started

## 3. Architecture Boundary

### ExecutionEngine (Control Plane)
**Responsibilities:**
- execution_id generation and correlation
- attempt lifecycle management (create/claim/advance/complete/fail)
- lease management (owner, expiration, sweep)
- retry policy and exponential backoff
- task state transitions (PENDING/READY/RUNNING/COMPLETED/FAILED/BLOCKED/CANCELLED)
- cancellation policy and timeout enforcement
- tool governance and authorization (L0-L3 approvals, allowlists)
- final persistence (SQLite, audit, execution_events)
- DAG scheduling and task assignment
- Capacity limits and concurrency control
- All policy decisions and authorization

**Authority Surface:** Public APIs: `submit()`, `start()`, `cancel()`, `heartbeat()`, `status()`, `result()`, `terminate()`, `recover()`

### Worker Matching (Dispatch/Matching Seam)
**Responsibilities:**
- Consume registry entries via read-only `list()` and `status()`
- Apply DispatchConstraints (tenant_scope, liveness, isolation, tool classes, runtime features, architecture)
- Deterministic-first-eligible selection (worker_id ordering)
- Produce DispatchDecision and CapabilityMatch contracts
- No execution authority, no policy decisions

**Authority Surface:** Public APIs: `match()`, `evaluate()` only

### RuntimeTransport (HermesAdapter → HermesRuntime)
**Responsibilities:**
- Map RuntimeRequest → RuntimeResult over transport protocol
- Process capability validation and worker identity verification
- Handle transport-level errors and retries
- Manage connection lifecycle
- Emit events via event_sink

**Authority Surface:** Pure mapping seam, no policy

### RemoteWorkerTransport (NEW for Phase 3.8)
**Responsibilities:**
- Registration/heartbeat/departure over HTTP/JSON/TLS
- mTLS authentication with control-plane CA
- Worker lifecycle management (epoch, instance_id, tenant_scope)
- Request/result delivery over bounded queue
- JSONL event emission
- Connection lifecycle and recovery
- Capacity/backpressure via EE pull model

**Authority Surface:** Read-only registry operations, event emission only

### Worker (Execution Plane)
**Responsibilities:**
- Execute one authorized job via governed tool boundary
- Produce RuntimeResult
- Maintain worker liveness

**Authority Surface:** None (capability is descriptive only)

## 4. D1-D10 Implementation Matrix

| ID | Decision | Required Behavior | Planned Component | Tests | Acceptance Criteria |
|----|----------|-------------------|-------------------|-------|---------------------|
| **D1** | Worker Registration Persistence | Additive SQLite table for WorkerIdentity + WorkerLiveness | Registry persistence layer | Unit tests for schema/migrations | Registry persists across process restarts |
| **D2** | Remote Worker Attestation Depth | mTLS with control-plane CA | TLS/SSL configuration | Integration tests for cert validation | Worker certificates issued per instance+epoch |
| **D3** | Worker Epoch / Clock-Skew Semantics | Registry-authoritative epoch assignment | Epoch service layer | Tests for epoch conflict resolution | Registry controls epoch assignment |
| **D4** | business_id-Scoped Identity Boundary | Propagate business_id as tenant_id in RuntimeRequest.metadata + DispatchConstraints | Tenant propagation layer | Tests for cross-tenant filtering | tenant_scope hard isolation boundary |
| **D5** | Transport Security Model | mTLS with control-plane CA | Security layer | Tests for TLS handshake and auth | Mutual TLS authentication |
| **D6** | Remote Registration / Heartbeat / Departure Protocol | HTTP/JSON over TLS protocol | Protocol implementation | Integration tests for lifecycle API | RESTful registration/heartbeat/departure |
| **D7** | Cross-Tenant Network Isolation | No shared workers | Worker lifecycle management | Tests for tenant isolation | Each worker bound to single tenant_scope |
| **D8** | Capacity / Backpressure Semantics | Bounded transport queue + EE pull | Queue/backpressure manager | Tests for queue limits and flow control | Transport queue limits enforced |
| **D9** | Observability Correlation Protocol | JSONL over same channel | Event emission layer | Tests for event correlation | Same JSONL format as SubprocessTransport |
| **D10** | Network Governance-Check Boundary | EE-only governance | Governance boundary | Tests for authorization flow | Transport trusts EE validation only |

## 5. File-Level Change Matrix

### MUST CHANGE (No Evidence → Must Create New Files)

**agent/remoteworker_transport.py**
- **Reason:** New component required by D1-D10 decisions
- **Exact Responsibility:** Implements RemoteWorkerTransport for Phase 3.8
- **Relevant Symbols:** `RemoteWorkerTransport`, `RemoteWorkerConfig`, `RemoteWorkerConnection`
- **Affected Decision:** D2, D5, D6, D8, D9
- **Compatibility Impact:** Additive - coexists with Phase 3.7
- **Regression Risk:** Low - isolated new implementation
- **Required Tests:** Integration tests, contract tests, security tests

**tests/remoteworker_transport_test.py**
- **Reason:** New test suite for RemoteWorkerTransport
- **Exact Responsibility:** Comprehensive testing of remote transport
- **Relevant Symbols:** All transport lifecycle, protocol, security tests
- **Affected Decision:** D1-D10
- **Compatibility Impact:** Additive - independent of existing tests
- **Regression Risk:** Medium - new code path validation
- **Required Tests:** Unit, integration, security, failure injection

### MAY CHANGE (Optional Extension)

**agent/hermes_adapter.py**
- **Reason:** May need to support both local and remote transports
- **Exact Responsibility:** Extend to handle remote transport type
- **Relevant Symbols:** `RuntimeAdapter`, transport selection logic
- **Affected Decision:** D6, D8, D9
- **Compatibility Impact:** Backward compatible with existing code
- **Regression Risk:** Medium - adapter logic changes
- **Required Tests:** Integration tests for transport switching

**agent/execution_engine.py**
- **Reason:** May need configuration for remote transport selection
- **Exact Responsibility:** Add remote transport configuration
- **Relevant Symbols:** `ExecutionEngineConfig`, transport factory
- **Affected Decision:** D8, D10
- **Compatibility Impact:** Configuration-only change initially
- **Regression Risk:** Low - additive configuration
- **Required Tests:** Integration tests for configuration

### MUST NOT CHANGE

**agent/subprocess_transport.py** (Phase 3.7)
- **Reason:** Phase 3.7 is frozen and must remain operational
- **Exact Responsibility:** Subprocess-based worker transport
- **Relevant Symbols:** `SubprocessTransport`, all existing methods
- **Affected Decision:** None (Phase 3.7 remains unchanged)
- **Compatibility Impact:** Zero (must continue to work)
- **Regression Risk:** Zero (must preserve existing functionality)
- **Required Tests:** All 30 Phase 3.7 tests must continue passing

**agent/worker_registry.py**
- **Reason:** WorkerRegistry is frozen (Phase 3.5) and must remain unchanged
- **Exact Responsibility:** In-memory worker presence registry
- **Relevant Symbols:** `WorkerRegistry`, all 8 public methods
- **Affected Decision:** D1 (adds persistence, but doesn't change API)
- **Compatibility Impact:** Zero (registry API unchanged)
- **Regression Risk:** Zero (must preserve existing functionality)
- **Required Tests:** All existing registry tests must continue passing

**agent/worker_matcher.py**
- **Reason:** WorkerMatcher is frozen (Phase 3.6) and must remain unchanged
- **Exact Responsibility:** Deterministic worker capability matching
- **Relevant Symbols:** `WorkerMatcher`, `match()`, `evaluate()`
- **Affected Decision:** D4 (tenant_scope used in constraints)
- **Compatibility Impact:** Zero (matcher API unchanged)
- **Regression Risk:** Zero (must preserve existing functionality)
- **Required Tests:** All 41 Phase 3.6 tests must continue passing

**agent/worker_contracts.py**
- **Reason:** WorkerFabric contracts are frozen (Phase 3.5)
- **Exact Responsibility:** WorkerIdentity, WorkerCapabilities, WorkerLiveness
- **Relevant Symbols:** All contract classes
- **Affected Decision:** D1 (schema mirrored but contracts unchanged)
- **Compatibility Impact:** Zero (contracts are immutable)
- **Regression Risk:** Zero (cannot modify frozen contracts)
- **Required Tests:** All contract tests must continue passing

**agent/dispatch_contracts.py**
- **Reason:** Dispatch contracts are frozen (Phase 3.6)
- **Exact Responsibility:** WorkerCandidate, CapabilityMatch, DispatchDecision
- **Relevant Symbols:** All dispatch contract classes
- **Affected Decision:** D4 (tenant_scope used in constraints)
- **Compatibility Impact:** Zero (contracts are immutable)
- **Regression Risk:** Zero (cannot modify frozen contracts)
- **Required Tests:** All dispatch contract tests must continue passing

**agent/hermes_runtime.py**
- **Reason:** HermesRuntime is frozen (Phase 3.4)
- **Exact Responsibility:** Runtime execution environment
- **Relevant Symbols:** `RuntimeCapabilities`, transport enum
- **Affected Decision:** D2 (mTLS added but transport kind enum unchanged)
- **Compatibility Impact:** Zero (runtime contracts unchanged)
- **Regression Risk:** Zero (must preserve existing functionality)
- **Required Tests:** All runtime tests must continue passing

**tests/execution_engine_test.py**
- **Reason:** ExecutionEngine tests must all continue to pass
- **Exact Responsibility:** All EE lifecycle and governance tests
- **Relevant Symbols:** All test cases
- **Affected Decision:** D10 (EE-only governance preserved)
- **Compatibility Impact:** Zero (must continue to test existing behavior)
- **Regression Risk:** Zero (no test modifications allowed)
- **Required Tests:** All 292 existing tests must continue passing

**tests/subprocess_transport_test.py**
- **Reason:** Phase 3.7 transport tests must all continue to pass
- **Exact Responsibility:** All SubprocessTransport tests
- **Relevant Symbols:** All 30 test cases
- **Affected Decision:** None (Phase 3.7 unchanged)
- **Compatibility Impact:** Zero (must continue to test existing behavior)
- **Regression Risk:** Zero (no test modifications allowed)
- **Required Tests:** All 30 Phase 3.7 tests must continue passing

**tests/worker_registry_test.py**
- **Reason:** WorkerRegistry tests must all continue to pass
- **Exact Responsibility:** All registry lifecycle tests
- **Relevant Symbols:** All 24 test cases
- **Affected Decision:** D1 (adds persistence but doesn't change API)
- **Compatibility Impact:** Zero (registry API unchanged)
- **Regression Risk:** Zero (no test modifications allowed)
- **Required Tests:** All 24 registry tests must continue passing

**tests/worker_matcher_test.py**
- **Reason:** WorkerMatcher tests must all continue to pass
- **Exact Responsibility:** All matcher selection tests
- **Relevant Symbols:** All 41 test cases
- **Affected Decision:** D4 (tenant_scope used in constraints)
- **Compatibility Impact:** Zero (matcher API unchanged)
- **Regression Risk:** Zero (no test modifications allowed)
- **Required Tests:** All 41 matcher tests must continue passing

**tests/dispatch_contracts_test.py**
- **Reason:** Dispatch contract tests must all continue to pass
- **Exact Responsibility:** All contract validation tests
- **Relevant Symbols:** All 43 test cases
- **Affected Decision:** D4 (tenant_scope used in constraints)
- **Compatibility Impact:** Zero (contracts unchanged)
- **Regression Risk:** Zero (no test modifications allowed)
- **Required Tests:** All 43 contract tests must continue passing

**tests/worker_contracts_test.py**
- **Reason:** Worker contract tests must all continue to pass
- **Exact Responsibility:** All worker contract validation tests
- **Relevant Symbols:** All test cases
- **Affected Decision:** D1 (schema mirrored but contracts unchanged)
- **Compatibility Impact:** Zero (contracts are immutable)
- **Regression Risk:** Zero (cannot modify frozen contracts)
- **Required Tests:** All worker contract tests must continue passing

## 6. Remote Worker Transport Design

### Registration Lifecycle
- **Registration:** HTTP POST `/workers/register` with worker identity
- **Attestation:** mTLS client certificate verification
- **Epoch Assignment:** Registry assigns worker_epoch on registration
- **Tenant Binding:** worker_instance_id + epoch + tenant_scope bound
- **Duplicate Handling:** Same instance+epoch → idempotent; newer epoch → supersedes

### Heartbeat/Departure
- **Heartbeat:** HTTP POST `/workers/heartbeat` with heartbeat_seq
- **Liveness Validation:** Registry validates instance/epoch, state transitions
- **Departure:** HTTP POST `/workers/depart` for terminal DEPARTED transition
- **Stale Detection:** Registry marks STALE based on heartbeat_seq, reported_at

### Request/Result Delivery
- **Request Queue:** Bounded queue (default 100 per worker) with EE pull model
- **Protocol:** HTTP POST `/jobs` for request submission, HTTP GET `/jobs/{handle_id}` for polling
- **Correlation:** execution_id correlates all messages (request/result/event)
- **Backpressure:** Queue full → transport returns CAPACITY_LIMIT error

### Connection Lifecycle
- **Establishment:** TLS handshake with mTLS client cert
- **Keepalive:** HTTP/2-style persistent connections when idle
- **Recovery:** Automatic reconnection with exponential backoff
- **Cleanup:** Graceful shutdown on transport termination

### Event Emission
- **Format:** JSONL events over same channel
- **Types:** REGISTRATION, HEARTBEAT, DEPARTURE, REQUEST_DELIVERY, RESULT_DELIVERY
- **Correlation:** All events include execution_id for traceability
- **Rate Limiting:** Transport controls event emission rate

### Security
- **Authentication:** mTLS with control-plane CA
- **Authorization:** EE-only governance boundary
- **Encryption:** TLS for all communications
- **Certificate Rotation:** New epoch = new certificate

### Observability
- **Correlation:** All components carry execution_id
- **Telemetry:** Structured JSONL events
- **Error Reporting:** Standardized error types and codes
- **Audit Trail:** All events logged for compliance

## 7. D1 — SQLite Registry Persistence

### Persistence Purpose
- **Goal:** Worker registry survives process restarts
- **Scope:** WorkerIdentity + WorkerLiveness fields only
- **Strategy:** Additive SQLite table (Phase 3.5 in-memory registry remains)

### Registry State
- **Schema:** Mirrors `worker_contracts.py` WorkerIdentity + WorkerLiveness
- **Single-Writer:** Registry holds exclusive write access
- **WAL Mode:** Write-ahead logging for performance
- **Migration:** Empty database on restart → workers re-register fresh

### Restart Recovery
- **Cold Start:** Registry empty, workers register fresh (new instance+epoch)
- **Warm Start:** Registry loads persisted state, workers may continue
- **Stale Handling:** Workers with old epochs ignored (new epoch required)
- **Departed Workers:** DEPARTED state preserved across restarts

### Lifecycle Integration
- **Registration:** On worker registration, insert/update registry table
- **Heartbeat:** Update reported_at and heartbeat_seq
- **Mark Stale:** Update state to STALE
- **Depart:** Update state to DEPARTED
- **Tenant Isolation:** tenant_scope indexed for fast queries

## 8. D2 + D5 — mTLS Security

### Control-Plane CA
- **Authority:** Central Certificate Authority controls all worker certificates
- **Issuance:** Certificates issued per worker_instance_id + epoch
- **Rotation:** New epoch triggers new certificate
- **Revocation:** Certificate revocation supported via CRL/OCSP

### Worker Identity
- **Binding:** Certificate contains worker_id, worker_instance_id, worker_epoch
- **Validation:** Transport validates certificate against control-plane CA
- **Attestation:** Client certificate required for all connections

### Authentication Flow
1. **TLS Handshake:** Establish TLS connection
2. **Certificate Exchange:** Client presents mTLS certificate
3. **Validation:** Control-plane validates certificate chain
4. **Registration:** Worker sends registration request with certificate info
5. **Authorization:** Control-plane validates certificate before processing

### Certificate Rotation
- **Trigger:** Worker epoch change or re-registration
- **Process:** New certificate issued, old certificate revoked
- **Transition:** Old connections closed, new connections with new cert
- **Cleanup:** Old certificates purged from registry after grace period

## 9. D3 — Registry-Authoritative Epoch

### Epoch Assignment
- **Authority:** Registry assigns worker_epoch on registration
- **Increment:** New epoch = current max epoch + 1 for same worker_id
- **Binding:** worker_instance_id + epoch creates unique worker identity
- **Validation:** Workers cannot self-assign epochs

### Epoch Semantics
- **Immutable:** Epoch immutable after registration (tied to certificate)
- **State:** Higher epoch always supersedes lower epoch
- **Stale Handling:** Lower epoch workers cannot overwrite newer epoch
- **Cross-Instance:** New instance requires new epoch regardless of instance_id

### Re-registration
- **Same Instance+Epoch:** Idempotent registration, capabilities updated
- **New Instance+Same Epoch:** Rejected (gate-model violation)
- **New Instance+New Epoch:** Fresh registration (supersedes old entry)
- **New Epoch+Same Instance:** Rejected (instance cannot change epoch)

### Worker Lifecycle
- **Registration:** Registry assigns epoch, issues certificate
- **Heartbeat:** Worker includes epoch in heartbeat, validated by registry
- **Stale Detection:** Epoch mismatch detected as stale heartbeat
- **Departure:** Worker sends depart request with current epoch

## 10. D4 + D7 — Tenant Isolation

### business_id → tenant_id Propagation
- **Metadata:** business_id propagated as tenant_id in RuntimeRequest.metadata
- **Constraints:** tenant_scope used in DispatchConstraints for filtering
- **Worker Binding:** Each worker instance bound to single tenant_scope
- **No Sharing:** Workers cannot serve multiple tenants

### Tenant Isolation Enforcement
- **Registry:** list(tenant_scope=...) restricts visibility
- **Matcher:** tenant_scope filter in eligibility checks
- **Transport:** worker bound to tenant_scope via certificate
- **Selection:** cross-tenant selection structurally impossible

### Worker Instance Binding
- **Single Tenant:** Each worker_instance_id bound to one tenant_scope
- **Immutable:** tenant_scope immutable after worker registration
- **Lifecycle:** Worker cannot change tenant_scope without re-registration
- **Validation:** transport validates worker-tenant binding on each request

### No Shared Workers
- **Design:** Eliminate cross-tenant worker sharing
- **Benefit:** Simplifies security model and reduces complexity
- **Impact:** Each tenant gets dedicated worker instances
- **Scaling:** Linear scaling with number of tenants

## 11. D6 — Remote Registration/Heartbeat/Departure Protocol

### HTTP/JSON over TLS Protocol
- **Base:** HTTP/1.1 over TLS with JSON payloads
- **Framing:** JSON lines (JSONL) for event streams
- **Content-Type:** application/json
- **Authentication:** mTLS client certificates

### Registration API
- **Endpoint:** POST /workers/register
- **Request:** WorkerIdentity + certificate info
- **Response:** registration confirmation with worker_epoch
- **Validation:** registry validates and assigns epoch

### Heartbeat API
- **Endpoint:** POST /workers/heartbeat
- **Request:** worker_id, worker_instance_id, worker_epoch, heartbeat_seq, reported_at
- **Response:** heartbeat confirmation or error
- **Validation:** registry validates epoch and liveness state

### Departure API
- **Endpoint:** POST /workers/depart
- **Request:** worker_id, worker_instance_id, worker_epoch
- **Response:** departure confirmation
- **Effect:** Registry sets worker state to DEPARTED

### Lifecycle Operations
- **Startup:** Worker registers, gets epoch and certificate
- **Heartbeat:** Worker periodically heartbeats, registry updates liveness
- **Departure:** Worker sends depart, registry marks as departed
- **Stale Detection:** Registry marks stale based on heartbeat timeout
- **Recovery:** Departed workers can re-register with new epoch

## 12. D8 — Capacity / Backpressure

### Bounded Transport Queue
- **Size:** Configurable queue depth (default 100 per worker)
- **Per-Worker:** Separate queue for each worker instance
- **Message Limit:** Maximum queued requests per worker
- **Full State:** Queue reports full when at capacity limit

### EE Pull Model
- **Polling:** EE actively polls for available work
- **Slot Allocation:** EE allocates execution slots per worker
- **Backoff:** EE respects queue capacity when assigning work
- **Flow Control:** Transport signals capacity limits to EE

### Capacity Limit Handling
- **Signal:** CAPACITY_LIMIT error returned to EE
- **Backoff:** EE backs off from overloading transport
- **Retry:** EE can retry after delay or try different worker
- **Logging:** Capacity events logged for observability

### Queue Management
- **Prioritization:** FIFO ordering for fairness
- **Eviction:** Oldest requests evicted when queue full
- **Monitoring:** Queue depth metrics exposed
- **Recovery:** Queue automatically drains as EE processes work

## 13. D9 — Observability Correlation Protocol

### JSONL Event Format
- **Structure:** Each event is a JSON object
- **Newline Delimited:** Events separated by newline characters
- **Fields:** execution_id, event_type, timestamp, worker_id, correlation_id
- **Ordering:** Events ordered by transmission sequence

### Event Types
- **REGISTRATION:** Worker registration event
- **HEARTBEAT:** Worker heartbeat event
- **DEPARTURE:** Worker departure event
- **REQUEST_DELIVERY:** Request delivered to worker
- **RESULT_DELIVERY:** Result returned from worker
- **ERROR:** Error event
- **CAPACITY_LIMIT:** Queue capacity limit event

### Correlation Chain
- **execution_id:** Primary correlation identifier
- **worker_id:** Worker identifier
- **correlation_id:** Additional correlation context
- **event_id:** Unique event identifier
- **timestamp:** Event generation timestamp

### Event Propagation
- **Transport:** Transport forwards worker events to EE
- **Event Sink:** Events stored in event_sink for audit
- **Real-time:** Events processed in near real-time
- **Persistence:** Events persisted for replay and debugging

## 14. D10 — Governance Boundary

### EE-Only Governance
- **Trust Model:** Transport assumes EE validated all work
- **No Re-check:** Transport does not re-validate governance
- **Fail-Closed:** Transport fails closed on errors
- **Authorization:** EE remains sole authorizer

### Governance Flow
1. **EE Authorization:** EE validates tool allowlist, approvals, quotas
2. **Transport Submission:** EE submits request to transport
3. **Transport Delivery:** Transport delivers to worker
4. **Worker Execution:** Worker executes job
5. **Result Return:** Worker returns result to transport
6. **EE Finalization:** EE validates result and stores

### Security Assumptions
- **EE Trust:** EE is trusted to perform all authorization
- **Transport Security:** Transport only secures transport layer
- **Worker Isolation:** Workers operate in sandboxed environments
- **Event Integrity:** Events are tamper-evident and traceable

## 15. Failure Matrix

| Failure | Detection | Authority | Action | Retry Authority | State Impact |
|---------|-----------|-----------|--------|----------------|--------------|
| Registration failure | TLS handshake failure | Transport | Return AUTH_DENIED | EE | Worker cannot register |
| TLS failure | Connection failure | Transport | Return TRANSPORT error | EE | Worker disconnected |
| Certificate failure | Cert validation failure | Transport | Return AUTH_DENIED | EE | Worker rejected |
| Worker unavailable | Connection timeout | Transport | Return TRANSPORT error | EE | Request queued/failed |
| Heartbeat timeout | No heartbeat within timeout | Registry | Mark STALE | EE | Worker marked stale |
| Stale epoch | Epoch mismatch | Registry | Reject heartbeat | EE | Worker cannot heartbeat |
| Tenant mismatch | tenant_scope validation | Registry/Matcher | Return TENANT_REJECTED | EE | Request rejected |
| Queue full | Capacity limit reached | Transport | Return CAPACITY_LIMIT | EE | EE backs off |
| Malformed message | Protocol violation | Transport | Return INVALID_RESULT | EE | Request rejected |
| Oversized message | Message size exceeded | Transport | Return INVALID_RESULT | EE | Request rejected |
| Duplicate request | Duplicate execution_id | Transport | Return DUPLICATE_REQUEST | EE | Request rejected |
| Replay attack | Duplicate request | Transport | Return DUPLICATE_REQUEST | EE | Request rejected |
| Worker crash | Process termination | Transport | Return CRASH error | EE | Job failed |
| Connection loss | Network failure | Transport | Return TRANSPORT error | EE | Retry with backoff |
| Cancellation | EE cancel request | Transport | Send cancellation to worker | EE | Job cancelled |
| Timeout | Execution timeout | EE | Cancel job, return TIMEOUT | EE | Job timed out |
| Result correlation | execution_id mismatch | Transport | Return INVALID_RESULT | EE | Result rejected |
| Cross-tenant access | tenant_scope violation | Registry/Matcher | Return TENANT_REJECTED | EE | Request rejected |

## 16. Security Threat Model

### Worker Impersonation
- **Risk:** Attacker presents stolen/missing certificate
- **Mitigation:** mTLS certificate validation, certificate revocation
- **Detection:** Failed certificate validation logged
- **Response:** Worker rejected, alert generated

### Certificate Compromise
- **Risk:** Stolen certificate used for unauthorized access
- **Mitigation:** Certificate rotation on epoch change, revocation checking
- **Detection:** Unusual connection patterns
- **Response:** Certificate revoked, workers re-registered

### MITM Attacks
- **Risk:** Attacker intercepts/modifies communications
- **Mitigation:** TLS with mTLS, certificate pinning
- **Detection:** TLS handshake failures
- **Response:** Connection terminated, alert generated

### Replay Attacks
- **Risk:** Attacker replays captured messages
- **Mitigation:** Unique execution_id for each request, nonce usage
- **Detection:** Duplicate execution_id detection
- **Response:** Request rejected, alert generated

### Cross-Tenant Access
- **Risk:** Worker serves requests from unauthorized tenants
- **Mitigation:** Worker bound to single tenant_scope, transport validation
- **Detection:** tenant_scope validation failures
- **Response:** Request rejected, worker quarantine

### Stale Identity
- **Risk:** Attacker uses old worker identity after departure
- **Mitigation:** Epoch-based identity, registry-authoritative epochs
- **Detection:** Stale heartbeat/epoch detection
- **Response:** Worker rejected, old identity invalidated

### Protocol Vulnerabilities
- **Risk:** Protocol implementation flaws
- **Mitigation:** Protocol validation, input sanitization
- **Detection:** Protocol violation detection
- **Response:** Request rejected, protocol bug fix

### Capacity Exhaustion
- **Risk:** Attacker exhausts transport capacity
- **Mitigation:** Bounded queues, rate limiting
- **Detection:** Queue full alerts
- **Response:** Capacity_LIMIT response, attacker blocked

## 17. Test Strategy

### D1 SQLite Persistence
- **Unit Tests:** Schema validation, migration testing
- **Integration Tests:** Registry persistence across restarts
- **Load Tests:** Concurrent registration/heartbeat operations
- **Recovery Tests:** Failed worker re-registration

### D2 mTLS
- **Unit Tests:** Certificate validation, chain verification
- **Integration Tests:** mTLS handshake, certificate rotation
- **Security Tests:** Certificate revocation, compromised cert handling
- **Performance Tests:** TLS handshake performance

### D3 Epoch
- **Unit Tests:** Epoch assignment, validation logic
- **Integration Tests:** Epoch conflict resolution, stale epoch handling
- **Concurrency Tests:** Concurrent epoch assignment
- **Recovery Tests:** Epoch continuity across restarts

### D4 Tenant Propagation
- **Unit Tests:** tenant_scope propagation, filtering logic
- **Integration Tests:** Cross-tenant access prevention
- **Load Tests:** Multi-tenant worker allocation
- **Security Tests:** tenant isolation bypass attempts

### D5 TLS
- **Unit Tests:** TLS configuration, cipher suite validation
- **Integration Tests:** Secure connection establishment
- **Security Tests:** TLS vulnerability testing
- **Performance Tests:** TLS performance under load

### D6 Lifecycle Protocol
- **Unit Tests:** API endpoint validation, request/response parsing
- **Integration Tests:** Registration/heartbeat/departure flows
- **Failure Tests:** Network partition, protocol failure handling
- **Recovery Tests:** Protocol recovery after failures

### D7 Tenant Isolation
- **Unit Tests:** tenant isolation rules, validation logic
- **Integration Tests:** Multi-tenant worker lifecycle
- **Security Tests:** Cross-tenant access attempts
- **Compliance Tests:** tenant_scope adherence verification

### D8 Queue/Backpressure
- **Unit Tests:** Queue implementation, capacity limits
- **Integration Tests:** Backpressure flow control, EE interaction
- **Load Tests:** Queue behavior under stress
- **Recovery Tests:** Queue recovery after failures

### D9 Correlation Protocol
- **Unit Tests:** JSONL parsing, event structure validation
- **Integration Tests:** Event correlation, traceability
- **Performance Tests:** Event throughput and latency
- **Recovery Tests:** Event replay and reconstruction

### D10 Governance Boundary
- **Unit Tests:** Governance boundary enforcement
- **Integration Tests:** EE authorization flow preservation
- **Security Tests:** Authorization bypass attempts
- **Compliance Tests:** Governance boundary verification

### Phase 3.7 Regression Protection
- **Regression Tests:** All 330 existing tests continue to pass
- **Integration Tests:** SubprocessTransport and EE interaction
- **Compatibility Tests:** Protocol interoperability
- **Performance Tests:** No performance regression

## 18. Phase 3.7 Regression Protection

### ExecutionEngine Compatibility
- **API Surface:** No changes to ExecutionEngine public APIs
- **Behavioral Compatibility:** All existing execution patterns preserved
- **State Management:** No changes to execution state management
- **Error Handling:** No changes to error handling semantics

### SubprocessTransport Compatibility
- **Protocol Compatibility:** HTTP/JSON over TLS preserves existing patterns
- **Lifecycle Compatibility:** Registration/heartbeat/departure similar to existing
- **Security Compatibility:** mTLS provides similar security to existing
- **Performance Compatibility:** No performance requirements changes

### Worker Compatibility
- **Contract Compatibility:** Worker contracts unchanged
- **Capability Compatibility:** Capability model unchanged (descriptive only)
- **Governance Compatibility:** Governance boundary preserved
- **Isolation Compatibility:** tenant_scope boundary preserved

### Test Compatibility
- **Test Suite Compatibility:** All 330 existing tests must pass
- **Protocol Compatibility:** Interoperability with existing protocols
- **Performance Compatibility:** No performance regression requirements
- **Security Compatibility:** No security degradation requirements

## 19. Implementation Sequence

### Phase 3.8A — Contract Preparation
**Objective:** Prepare contracts for Remote Worker Transport
**Files:** agent/remoteworker_transport.py, tests/remoteworker_transport_test.py
**Dependencies:** agent/worker_contracts.py, agent/runtime_contracts.py
**Tests:** Contract validation tests
**Acceptance Criteria:** Contracts compile and pass validation
**Rollback Point:** Before contract changes

### Phase 3.8B — Identity and Tenant Boundary
**Objective:** Implement worker identity, tenant isolation, epoch management
**Files:** agent/remoteworker_transport.py, agent/worker_registry.py (add persistence)
**Dependencies:** D1, D2, D3, D4, D5
**Tests:** Identity validation, tenant isolation, epoch management
**Acceptance Criteria:** Identity and tenant boundaries enforced
**Rollback Point:** Before persistence layer changes

### Phase 3.8C — Registry Persistence
**Objective:** Implement SQLite persistence for worker registry
**Files:** agent/worker_registry.py (persistence layer)
**Dependencies:** D1, D3
**Tests:** Persistence tests, recovery tests
**Acceptance Criteria:** Registry persists across restarts
**Rollback Point:** Before persistence implementation

### Phase 3.8D — mTLS Foundation
**Objective:** Implement mTLS with control-plane CA
**Files:** agent/remoteworker_transport.py (security layer)
**Dependencies:** D2, D5
**Tests:** Certificate validation, TLS handshake tests
**Acceptance Criteria:** mTLS authentication working
**Rollback Point:** Before security layer changes

### Phase 3.8E — HTTP/JSON Lifecycle
**Objective:** Implement HTTP/JSON over TLS protocol
**Files:** agent/remoteworker_transport.py (protocol layer)
**Dependencies:** D6
**Tests:** Registration/heartbeat/departure tests
**Acceptance Criteria:** Lifecycle protocol functional
**Rollback Point:** Before protocol implementation

### Phase 3.8F — Request/Result Delivery
**Objective:** Implement request/result delivery over transport
**Files:** agent/remoteworker_transport.py (delivery layer)
**Dependencies:** D8
**Tests:** Request delivery, result handling tests
**Acceptance Criteria:** Request/result delivery working
**Rollback Point:** Before delivery implementation

### Phase 3.8G — Queue/Backpressure
**Objective:** Implement bounded queue with EE pull model
**Files:** agent/remoteworker_transport.py (queue/backpressure)
**Dependencies:** D8
**Tests:** Queue behavior, backpressure tests
**Acceptance Criteria:** Backpressure working correctly
**Rollback Point:** Before queue implementation

### Phase 3.8H — Observability
**Objective:** Implement JSONL event emission
**Files:** agent/remoteworker_transport.py (event layer)
**Dependencies:** D9
**Tests:** Event correlation, emission tests
**Acceptance Criteria:** Event emission working
**Rollback Point:** Before event implementation

### Phase 3.8I — Failure/Recovery
**Objective:** Implement failure detection and recovery
**Files:** agent/remoteworker_transport.py (failure handling)
**Dependencies:** All D1-D10
**Tests:** Failure injection, recovery tests
**Acceptance Criteria:** Failure/recovery robust
**Rollback Point:** Before failure handling

### Phase 3.8J — Integration
**Objective:** Integrate with ExecutionEngine and existing components
**Files:** agent/execution_engine.py (configuration), agent/hermes_adapter.py (extension)
**Dependencies:** All components
**Tests:** Integration tests, end-to-end tests
**Acceptance Criteria:** Full integration working
**Rollback Point:** Before integration

### Phase 3.8K — Verification
**Objective:** Comprehensive testing and validation
**Files:** All test files
**Dependencies:** All implementations
**Tests:** Full test suite, security tests, performance tests
**Acceptance Criteria:** All tests pass, performance requirements met
**Rollback Point:** Before final verification

### Phase 3.8L — Gate Closure
**Objective:** Final approval and production readiness
**Files:** Documentation, configuration
**Dependencies:** All completed phases
**Tests:** Final regression test suite
**Acceptance Criteria:** Gate acceptance criteria met
**Rollback Point:** Before gate closure

## 20. Rollback Strategy

### Phase-by-Phase Rollback
- **Early Phases (A-D):** Revert changes to code and configuration files
- **Mid Phases (E-H):** Revert protocol and integration changes
- **Late Phases (I-L):** Revert advanced features and integration

### Data Recovery
- **Registry Persistence:** No data loss (SQLite preserves data)
- **Worker State:** Workers can re-register fresh (new epoch)
- **Event Logs:** Events stored in event_sink for replay
- **Configuration:** Configuration files preserved for recovery

### Service Continuity
- **Phase 3.7 Preservation:** SubprocessTransport remains operational
- **Graceful Degradation:** If new transport fails, fallback to existing
- **Load Balancing:** Multiple worker instances for redundancy
- **Monitoring:** All components monitored for health

### Testing Rollback
- **Regression Suite:** All 330 existing tests continue to pass
- **Test Isolation:** New tests isolated from existing tests
- **Test Cleanup:** Remove new test files if rollback occurs
- **Validation:** Verify rollback complete before proceeding

## 21. Explicit Non-Goals

- **No second execution engine:** RemoteWorkerTransport does not become execution engine
- **No second authorization engine:** EE remains sole authorizer
- **No shared workers:** Each worker instance bound to single tenant
- **No capability authorization:** Capabilities remain descriptive only
- **No Phase 3.7 rewrite:** Phase 3.7 SubprocessTransport unchanged
- **No unbounded queues:** Transport queue has configurable limits
- **No replacement of ExecutionEngine:** EE remains central authority
- **No speculative service mesh:** Simple HTTP/JSON over TLS only
- **No SPIFFE/SPIRE:** Uses mTLS with control-plane CA
- **No gRPC:** Uses HTTP/JSON over TLS
- **No alternate transport protocol:** Uses HTTP/JSON over TLS
- **No asynchronous governance:** EE synchronously authorizes before execution
- **No worker-side governance:** Workers cannot authorize tools
- **No capability enforcement:** Worker capabilities descriptive only
- **No capacity enforcement:** Capacity never hard gate at worker level
- **No scheduling authority:** EE remains sole scheduler

## 22. Implementation Acceptance Gate

### Checklist
- [ ] D1 implemented and tested (SQLite persistence)
- [ ] D2 implemented and tested (mTLS with control-plane CA)
- [ ] D3 implemented and tested (Registry-authoritative epoch)
- [ ] D4 implemented and tested (business_id as tenant_id propagation)
- [ ] D5 implemented and tested (Transport security model)
- [ ] D6 implemented and tested (HTTP/JSON over TLS protocol)
- [ ] D7 implemented and tested (No shared workers)
- [ ] D8 implemented and tested (Bounded queue + EE pull)
- [ ] D9 implemented and tested (JSONL over same channel)
- [ ] D10 implemented and tested (EE-only governance)

- [ ] ExecutionEngine authority preserved
- [ ] Phase 3.7 preserved
- [ ] tenant isolation verified
- [ ] security verified
- [ ] failure recovery verified
- [ ] regression suite green (330 tests)
- [ ] documentation updated
- [ ] final gate review completed

## 23. FINAL OUTPUT

After creating ONLY the plan file, report:

**PHASE 3.8 ACTION 12 — COMPLETE**

**Plan:** HEER_PHASE38_IMPLEMENTATION_PLAN.md

**Architecture:** APPROVED

**D1-D10:** RESOLVED

**Implementation:** NOT STARTED

**Production code:** UNCHANGED

**Tests:** UNCHANGED

**Dependencies:** UNCHANGED

**Phase 3.7:** FROZEN

**Frozen invariants:** PRESERVED

**Architecture blockers:** NONE

**Implementation readiness:** READY

Any architectural ambiguity discovered: None - all D1-D10 decisions explicitly resolved by Architecture Owner with clear implementation paths.

The plan provides comprehensive implementation roadmap for Phase 3.8 Remote Worker Transport while preserving all existing architecture and maintaining backward compatibility with Phase 3.7 SubprocessTransport.