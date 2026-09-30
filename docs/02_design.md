# Template Design Specification

## Position in AgentCore Architecture

- **Agent Class**: `MaterialDeclarationCompletenessGraph`
- **L1 Base**: **AgentBaseGraph** (outer) / AutonomousBaseGraph
- **Three-Layer Separation**:
  - State: flat TypedDict composition (no Pydantic — msgpack incompatible)
  - Node: L1 inheritance (Template Method: `execute(self, state: dict) -> dict` override only)
  - Graph: composition (`register_nodes()` for node substitution)

## Architecture Overview

This is a **Cat 2** template: a fixed multi-step workflow for one specific job-to-be-done
(BOM-to-declaration compliance reconciliation), with no autonomous reasoning loop. It uses the
standard Cat 2 two-layer composition:

- **Outer graph** (`src/graph/graph.py`) — `MaterialDeclarationCompletenessGraph(AgentBaseGraph)`.
  Fixed 5-node backbone identical to Cat 1 (`initialize → pre_process → main → post_process →
  finalize`). All domain complexity is hidden inside the `main` slot via a `GraphNode` subclass,
  `MaterialDeclarationWorkflowGraphNode`. `add_edges()` is **not** overridden on the outer graph.
- **Inner graph** (`src/graph/domain_workflow_graph.py`) —
  `MaterialDeclarationWorkflowGraph(BaseGraph)`. Fully custom 7-node linear topology implementing
  the domain pipeline from `docs/01_proposal.md` §Agent Workflow: BOM Parse → Declaration Ingest
  → Substance Match → Coverage Check → Exception Compile → Brief Draft → Output Validate.
  Inherits `BaseGraph` directly (not `AgentBaseGraph`) because none of the 7 domain steps map to
  the pre_process/main/post_process slots — it is a fully custom topology.

### Node Configuration (Outer Graph)

| Node | Responsibility | Input State | Output State | Inherits/Overrides |
|------|---------------|-------------|--------------|-------------------|
| initialize | Framework default — assigns `trace_id`, `correlation_id`, initial `node_history` | (framework-managed) | (framework-managed) | InitializeNode (default) |
| pre_process | Validates/normalizes the incoming request: confirms `bom_ref`, `declarations_ref`, and `substance_index_ref` are present and well-formed; sets `validated_input` | `user_input` | `validated_input`, `status`, `error` (on invalid input) | `PreProcessNode` (`src/nodes/pre_process_node.py`) |
| main | `MaterialDeclarationWorkflowGraphNode` (`GraphNode`) — invokes the inner 7-node domain workflow and merges its result back into outer state | `validated_input` | `evidence_matrix`, `coverage_gaps`, `remediation_brief`, `result`, `status` | `GraphNode` subclass |
| post_process | Formats the final response: attaches the mandatory human-review disclaimer, assembles `result` into the final reviewer-facing shape | `evidence_matrix`, `coverage_gaps`, `remediation_brief` | `result` (final formatted shape) | `PostProcessNode` (`src/nodes/post_process_node.py`) |
| finalize | Framework default — appends final `node_history` entry, closes trace | (framework-managed) | (framework-managed) | FinalizeNode (default) |

### Node Configuration (Inner Graph — `MaterialDeclarationWorkflowGraph`)

| Node | Responsibility | Input State | Output State | Service Used |
|------|---------------|-------------|--------------|---------------|
| bom_parse | Extract part numbers, revisions, and supplier IDs from the product BOM | `validated_input` (BOM reference) | `bom_data` | `MaterialDeclarationService.parse_bom` |
| declaration_ingest | Parse supplier material declarations: part reference, substance list, declaration version/date | `bom_data` | `declaration_data` | `MaterialDeclarationService.ingest_declarations` |
| substance_match | RAG retrieval matching declared substances against the RoHS/REACH substance and exemption index | `declaration_data` | `substance_matches` | `MaterialDeclarationService.match_substances` |
| coverage_check | Join BOM parts to declarations; flag missing declarations, stale versions, contradictory substance records | `bom_data`, `declaration_data`, `substance_matches` | `coverage_gaps` | `MaterialDeclarationService.check_coverage` |
| exception_compile | Build a traceable evidence matrix and exception list with source-document provenance references | `coverage_gaps`, `substance_matches` | `evidence_matrix` | `MaterialDeclarationService.compile_exceptions` |
| brief_draft | Generate a structured, reviewer-ready remediation/decision brief from the evidence matrix | `evidence_matrix`, `coverage_gaps` | `remediation_brief` | `MaterialDeclarationService.draft_brief` |
| output_validate | S-3: block instruction-injection content from being read as an approval; append mandatory human-review disclaimer | `remediation_brief` | `remediation_brief` (validated), `status` | `MaterialDeclarationService.validate_output` |

### Data Flow

**Outer graph (fixed backbone):**

```
START → initialize → pre_process → main → {route} → post_process → finalize → END
                                            ↓ (retry, max_retry=3)
                                          pre_process
```

**Inner graph (`main` slot, linear domain pipeline):**

```
START → bom_parse → declaration_ingest → substance_match → coverage_check
      → exception_compile → brief_draft → output_validate → END
```

No conditional branching inside the inner graph — every declaration/coverage exception is
recorded as data (in `coverage_gaps` / `evidence_matrix`), not as a routing decision, so the
pipeline always runs the full 7 steps and lets `output_validate` be the single gate before
returning to the outer graph.

### State Definition

| Field | Type | Purpose | Required |
|-------|------|---------|----------|
| `validated_input` | `str` | Normalized request payload (BOM/declarations/index references) set by outer `pre_process` | Yes (after pre_process) |
| `bom_data` | `dict` | Parsed BOM: part numbers, revisions, supplier IDs | No (set by `bom_parse`) |
| `declaration_data` | `list[dict]` | Parsed supplier declarations: part ref, substance list, version/date | No (set by `declaration_ingest`) |
| `substance_matches` | `list[dict]` | Declared substances matched against the RoHS/REACH substance/exemption index | No (set by `substance_match`) |
| `coverage_gaps` | `list[dict]` | Missing declarations, stale versions, contradictory records | No (set by `coverage_check`) |
| `evidence_matrix` | `dict` | Traceable evidence matrix with source provenance | No (set by `exception_compile`) |
| `remediation_brief` | `str` | Reviewer-ready remediation/decision brief text, disclaimer-appended | No (set by `brief_draft` / finalized by `output_validate`) |
| `result` | `dict` | Final formatted output returned to the caller | No (set by `post_process`) |
| `error` | `str` | Error message on failure | No |

`bom_data`, `declaration_data`, `substance_matches`, `coverage_gaps` are replaced wholesale on
each write (not append-only) — each inner node produces the complete artifact for that step, not
an incremental delta, so `Annotated[list[T], operator.add]` is deliberately **not** used for
`declaration_data`/`substance_matches`/`coverage_gaps`.

**State Constraints (mandatory):**
- Flat TypedDict only (primitives + JSON-serializable types)
- No JWT, API keys, credentials in State (checkpoint DB leakage)
- InvocationContext via `config["configurable"]` only (not in State)
- No Pydantic models, dataclass, arbitrary Python objects (msgpack incompatible)

## Framework Utilization

### Shared Components Used
- [x] InvocationContext (correlation_id, session_id, permissions, credential handle) — used by `substance_match` (vector DB) and `brief_draft` (LLM) via `context.credential_handle`
- [x] ConnectionPolicy (retry/timeout strategy) — outer graph `max_retry: 3`, `timeout_seconds: 30` per `config/agent.yaml`
- [ ] SecurityViolationError
- [x] S-2: `_extra_security_gate_input()` — domain-specific input check hook
      Validates that `bom_ref`/`declarations_ref` in the incoming payload do not exceed a
      configured size limit and are present, on top of the default PII scan on `user_input` /
      `validated_input`.
- [x] S-3: `_extra_security_gate_output()` — domain-specific output check hook
      `output_validate` (inner) and outer `post_process`'s `_extra_security_gate_output()` scan
      `remediation_brief` for approval-like language (e.g. "approved", "cleared for release",
      "compliant — ship") and raise/strip it — this is the direct implementation of the proposal's
      §11 risk #1 mitigation ("S-3 gate blocking any approval-like language in the output").
- [x] S-4: `emit_trace_event()` — at least one domain-specific event inside each `execute()`
      Each inner node emits one domain event: `bom_parsed`, `declarations_ingested`,
      `substances_matched`, `coverage_checked`, `exceptions_compiled`, `brief_drafted`,
      `output_validated`. (**mandatory**; do NOT emit `node_start` / `node_complete` /
      `node_error` — `BaseNode.__call__()` emits these automatically; duplicates corrupt audit
      trail)

> **S-2/S-3 gate behaviour by node type (ADR-017):**
> - `FunctionNode` subclass → framework `@final` gate always runs automatically;
>   extend via `_extra_security_gate_input()` / `_extra_security_gate_output()` only
> - `GraphNode` / `RemoteAgentNode` → deliberate no-op (upstream or remote node's gate already applied)
> - Custom `BaseNode` subclass → must implement `_security_gate_input()` and
>   `_security_gate_output()` directly (`@abstractmethod` — omission raises `TypeError` at instantiation)

All 7 inner nodes and the outer `pre_process`/`post_process` are `FunctionNode` subclasses (the
framework `@final` gate applies automatically); the outer `main` slot is a `GraphNode` (deliberate
no-op — the inner graph's own nodes already ran their gates).

### Composition Pattern

- **Pattern**: GraphNode (subgraph)
- **Composition target**: `MaterialDeclarationWorkflowGraph` (`src/graph/domain_workflow_graph.py`), a `BaseGraph`-derived 7-node linear domain pipeline
- **Error propagation strategy**: `propagate` — a reconciliation error (e.g. an unparseable BOM or a substance-index lookup failure) must fail the whole invocation as `SubgraphError` rather than degrade gracefully, because a compliance evidence gap silently omitted from the brief is exactly the failure mode the agent exists to prevent (see `docs/01_proposal.md` §11 risk #1). `propagate_hitl` is `False` — no HITL is declared (industry is MFG, not HCR/INS/FIN/GOV; see `docs/01_proposal.md` HITL Gate section), and human sign-off happens procedurally after the agent returns, not via a framework `interrupt()`.

## Import Isolation Confirmation
- [x] Template does not import agenticstar-platform SDK (Level 0)
- [x] Import targets: framework/ and shared/ only (no agents/base/ required)

## Design Decision Record

| Decision | Option A | Option B | Chosen | Rationale |
|----------|----------|----------|--------|-----------|
| L1 base type | AgentBaseGraph | AutonomousBaseGraph | **AgentBaseGraph** | Fixed, bounded 7-step reconciliation pipeline with no self-directed loop or termination decision — matches `docs/01_proposal.md` Cat Self-Assessment (Cat 2, L2/L3 ruled out) |
| Composition pattern | Standalone (flat outer graph) | GraphNode (outer + inner) | **GraphNode (outer + inner)** | 7 distinct domain steps do not map onto the 3 outer slots (pre_process/main/post_process) 1:1; isolating them in an inner `BaseGraph` keeps the outer graph as the standard 5-node backbone and keeps domain logic independently testable |
| Inner graph parent | `BaseGraph` (custom topology) | `AgentBaseGraph` (5-node pipeline) | **BaseGraph** | The 7 domain steps are a fully custom linear topology with no natural pre_process/main/post_process split |
| `error_strategy` | `propagate` | `handle` | **propagate** | A reconciliation failure must surface as a hard error, not a degraded/partial brief — see Composition Pattern rationale above |
| `propagate_hitl` | `True` | `False` | **False** | Industry is MFG, not HCR/INS/FIN/GOV; `docs/01_proposal.md` HITL Gate is N/A; human sign-off is enforced procedurally outside the agent |
| `required_trust_level` | `ANONYMOUS` | `VERIFIED_EXTERNAL` | **VERIFIED_EXTERNAL** | Matches `config/agent.yaml`; caller is an internal PLM/BOM export pipeline or an authenticated compliance reviewer, never anonymous |

---

**Status**: completed
**Date**: 2026-07-28
**Reviewer**: [TBD]
