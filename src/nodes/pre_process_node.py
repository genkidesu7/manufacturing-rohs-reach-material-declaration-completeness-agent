"""AgentCore Platform v1.0"""

# Node contract (agents_layer_design.md §1):
#  - Extend FunctionNode; implement execute(state) -> dict
#  - Return ONLY the fields this node changes (never full state)
#  - Return AgentStatus.<X>.value strings for status assignments [A1]
#  - Never import from mediator/, api/, or other agents

from typing import Any, ClassVar

from framework.errors import SecurityViolationError
from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

_MAX_INPUT_CHARS = 50_000


class PreProcessNode(FunctionNode):
    """Validate the incoming BOM/declarations/substance-index request."""

    # docs/02_design.md Design Decision Record: caller is an internal PLM/BOM export
    # pipeline or an authenticated compliance reviewer, never anonymous.
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def _extra_security_gate_input(self, state: dict[str, Any]) -> dict[str, Any]:
        """S-2 domain check: reject an oversized request payload."""
        user_input = state.get("user_input", "")
        if isinstance(user_input, str) and len(user_input) > _MAX_INPUT_CHARS:
            raise SecurityViolationError(
                f"PreProcessNode: user_input exceeds max size of {_MAX_INPUT_CHARS} characters"
            )
        return state

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        user_input = state.get("user_input", "")

        if not user_input or not user_input.strip():
            return {
                "status": AgentStatus.ERROR.value,
                "error": "PreProcessNode: user_input is empty or missing",
                "error_log": ["PreProcessNode: user_input is empty or missing"],
            }

        validated_input = user_input.strip()
        emit_trace_event("request_validated", {"input_length": len(validated_input)}, state)
        return {
            "validated_input": validated_input,
            "status": AgentStatus.SUCCESS.value,
        }
