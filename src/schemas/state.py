"""AgentCore Platform v1.0"""

from typing import Any

# ADR-005: State must be a flat TypedDict (see ADR-005 for the prohibited
# alternatives). LangGraph checkpoints use msgpack serialization, so only
# plain serializable fields are allowed. Do NOT add credentials or secrets.

from framework.schemas.agent_state import AgentState


class State(AgentState):
    """Agent state.

    All shared fields (user_input, status, session_id, node_history,
    error_log, hitl_*, etc.) are inherited from AgentState.

    Domain fields below are replaced wholesale on each write (not
    append-only) — each inner node produces the complete artifact for
    its step, not an incremental delta. See docs/02_design.md State
    Definition for the full field list.
    """

    bom_data: dict[str, Any]
    declaration_data: list[dict[str, Any]]
    substance_matches: list[dict[str, Any]]
    coverage_gaps: list[dict[str, Any]]
    evidence_matrix: dict[str, Any]
    remediation_brief: str
