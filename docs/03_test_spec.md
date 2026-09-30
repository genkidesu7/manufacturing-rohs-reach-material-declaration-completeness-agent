# Test Specification

**Status:** Completed

## Test Strategy
- Coverage target: 80%
- Test types: Unit / Integration / E2E (via ASGI transport)
- `.claude/rules/test_rule.md` read in full before implementing any test (mandatory per
  development-cycle/07_test_stage.md Step 0) — its 4 rules are covered explicitly below.

## Framework Compliance Tests (Mandatory)

| TC-ID | Test | Expected Result | Result |
|-------|------|----------------|--------|
| TC-01 | State contract: flat TypedDict | Type check pass, no Pydantic/dataclass | `tests/proof_of_boundary/test_state_safety.py` — PASS |
| TC-02 | SecurityViolationError fires on invalid input | Error raised | `tests/unit/test_pre_process_node.py::test_extra_security_gate_input_rejects_oversized_payload`, `test_post_process_node.py::test_extra_security_gate_output_blocks_approval_language`, `test_output_validate_node.py::test_extra_security_gate_output_requires_disclaimer` — PASS |
| TC-03 | No JWT/Credential in State | CI `gate-credential-scan`: 0 violations (S-5 enforcement moved to CI) | `tests/proof_of_boundary/test_state_safety.py` — PASS |
| TC-04 | InvocationContext via configurable only | Direct access raises error | N/A — no node stores `InvocationContext` in `State`; verified by `test_state_safety.py` prohibited-type scan |
| TC-05 | S-4: no duplicate lifecycle events in `execute()` | `node_start` / `node_complete` / `node_error` absent from `execute()` body | `tests/proof_of_boundary/test_pb_invoke_order.py` — PASS |
| TC-06 | S-2: `_security_gate_input()` not overridden (`FunctionNode` subclass) | `TypeError` raised at class definition if overridden (`@final` enforced by framework) | `tests/unit/test_framework_compliance_tc06_tc07.py::test_tc06...` — PASS |
| TC-07 | S-3: `_security_gate_output()` not overridden (`FunctionNode` subclass) | `TypeError` raised at class definition if overridden (`@final` enforced by framework) | `tests/unit/test_framework_compliance_tc06_tc07.py::test_tc07...` — PASS |
| TC-08 | `required_trust_level` enforced | Insufficient trust → refused | `tests/integration/test_graph.py::test_invoke_denies_anonymous_caller` — PASS |
| TC-09 | S-2: `_extra_security_gate_input()` non-trivial when domain checks needed | Domain-specific input checks execute correctly (e.g. PII scan on additional fields, consent validation, business rules) | `PreProcessNode._extra_security_gate_input` (payload size limit) — `tests/unit/test_pre_process_node.py` — PASS |
| TC-10 | S-3: `_extra_security_gate_output()` non-trivial when domain checks needed | Domain-specific output checks execute correctly (e.g. nested credential scan, PII re-check, content filtering, preservation verification) | `PostProcessNode`/`OutputValidateNode._extra_security_gate_output` (approval-language block + disclaimer requirement) — PASS |
| TC-11 | S-4: at least one domain `emit_trace_event()` inside each `execute()` | Domain event emitted on every invocation path | Verified statically by `bash .claude/common-scripts/check-security.sh` (`check_emit_trace_event`) — PASS |

## Proof-of-Boundary Tests (Mandatory)

| PB-ID | Boundary | Test | Expected Result | Result |
|-------|----------|------|----------------|--------|
| PB-1 | BaseNode → EventEmitter | `emit_trace_event()` fires on every invocation path | No silent failures | `tests/proof_of_boundary/test_pb_invoke_order.py` (node_start/node_complete events) — PASS |
| PB-2 | State serialization | Post-invoke State is primitives only | No Pydantic/dataclass | `tests/proof_of_boundary/test_state_safety.py` — PASS |
| PB-3 | Level 2 → External service | Real external service connection | Data retrieved | N/A — all external integrations (BOM/declaration parsers, substance index, LLM) are deferred to a later sprint per docs/02_design.md; mock-mode stubs cover the current functioning path (see `tests/unit/test_service.py`) |
| PB-4 | Import isolation | No Level 0 imports | AST scan: 0 violations | `tests/proof_of_boundary/test_import_isolation.py` — PASS |
| PB-5 | Checkpoint safety | No JWT/Pydantic in checkpoint | Inspection pass | `tests/proof_of_boundary/test_state_safety.py` — PASS |
| PB-6 | Invoke execution order | `__call__()`: S-1 trust gate → S-4 `node_start` → S-2 `_security_gate_input` → `execute()` → S-3 `_security_gate_output` → S-4 `node_complete` | Order verified | `tests/proof_of_boundary/test_pb_invoke_order.py` — PASS (harness state extended with `session_id`/`thread_id`/`trace_id` so nodes calling `InvocationContext.from_state()` don't raise `KeyError`) |
| PB-7 | HITL interrupt propagation *(conditional)* | Required only when `config.yaml` sets `hitl.enabled: true`; otherwise record **Auto-waived — non-HITL** | `GraphInterrupt` propagates to the LangGraph engine; `status` is not set to `error` | **Auto-waived — non-HITL** (`config/agent.yaml` has no `hitl.enabled: true`; `docs/01_proposal.md` HITL Gate is N/A for MFG industry) — `tests/proof_of_boundary/test_pb7_hitl_interrupt_propagation.py` SKIPPED as designed |

> **Pre-CoE gate checklist:** PB-1 through PB-6 are mandatory. Evaluate PB-7 only for HITL-enabled templates. When neither HITL setting is true, mark PB-7 **Auto-waived — non-HITL**; its test is not required and must not block the gate.

## Regression Tests — `.claude/rules/test_rule.md` (deploy-stg `agent_status_success: false` class)

| Rule | Test | Expected Result | Result |
|------|------|----------------|--------|
| Rule 1 — mock-mode flag resolved under every alias | `tests/unit/test_mock_mode.py` (`USE_MOCK` alone, `STG_MOCK_MODE` alone, neither) | Activates under either alias individually; off when neither set | PASS |
| Rule 2 — mock mode skips `require()` with zero secrets bound | `tests/unit/test_substance_match_node.py::test_succeeds_in_mock_mode_with_no_secret_provider_bound`, `tests/unit/test_brief_draft_node.py::test_succeeds_in_mock_mode_with_no_secret_provider_bound` | `status: success` with no `bound_secrets()` context at all | PASS |
| Rule 3 — HTTP-level test for async route wrapping sync `agent.invoke()` | `tests/integration/test_api_invoke_http.py` (real `httpx.ASGITransport`) | 200 response, no swallowed `asyncio.run()` RuntimeError | PASS |
| Rule 4 — `stg_invoke_evidence.py` runnable as local pytest | `scripts/test_stg_invoke_evidence.py` (pre-existing scaffold test, stub HTTP server) | `overall == "PASS"` on a healthy stub agent | PASS (143/143 in `scripts/`) |

## Domain / Unit Tests

| Test file | Covers | Result |
|-----------|--------|--------|
| `tests/unit/test_pre_process_node.py` | Input validation, S-2 size-limit gate | PASS |
| `tests/unit/test_post_process_node.py` | Result assembly, S-3 approval-language + disclaimer gate | PASS |
| `tests/unit/test_bom_parse_node.py` | BOM parse, inner-graph `validated_input`/`user_input` fallback | PASS |
| `tests/unit/test_declaration_ingest_node.py` | Declaration parsing | PASS |
| `tests/unit/test_substance_match_node.py` | RAG substance match, Rule 2 regression | PASS |
| `tests/unit/test_coverage_check_node.py` | Missing-declaration gap detection | PASS |
| `tests/unit/test_exception_compile_node.py` | Evidence matrix + provenance | PASS |
| `tests/unit/test_brief_draft_node.py` | Brief drafting, Rule 2 regression | PASS |
| `tests/unit/test_output_validate_node.py` | Approval-language block, disclaimer append | PASS |
| `tests/unit/test_service.py` | `MaterialDeclarationService` mock-mode functions, `validate_output`, real-mode `NotImplementedError` | PASS |

## Integration Tests

| Test file | Covers | Result |
|-----------|--------|--------|
| `tests/integration/test_graph.py` | Outer graph real `.compile()` + `.invoke()`, success path and S-1 anonymous-denial path | PASS |
| `tests/integration/test_domain_workflow_graph.py` | Inner 7-node domain workflow graph real `.compile()` + `.invoke()` | PASS |
| `tests/integration/test_api_invoke_http.py` | `/invoke` and `/health` over real ASGI transport | PASS |

## Test Execution Summary
- Execution date: 2026-07-28
- Total tests: 45 in `tests/` (43 passed, 2 auto-waived/skipped — PB-7 non-HITL) + 143 in `scripts/` (all passed)
- Pass: 186 / Fail: 0 / Skip: 2 (PB-7, auto-waived — non-HITL)
- Coverage: 94% (`src/`, `pytest --cov=src`)
