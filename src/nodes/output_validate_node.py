"""AgentCore Platform v1.0"""

import asyncio
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.service import MaterialDeclarationService


class OutputValidateNode(FunctionNode):
    """S-3: block instruction-injection/approval-like content; append the disclaimer."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def _extra_security_gate_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Defense-in-depth backstop on top of MaterialDeclarationService.validate_output."""
        brief = result.get("remediation_brief", "")
        if brief and "DISCLAIMER:" not in brief:
            from framework.errors import SecurityViolationError

            raise SecurityViolationError(
                "OutputValidateNode: mandatory human-review disclaimer missing from " "remediation brief."
            )
        return result

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        remediation_brief = state.get("remediation_brief", "")
        if not remediation_brief:
            return {
                "status": AgentStatus.ERROR.value,
                "error": "OutputValidateNode: remediation_brief is empty or missing",
                "error_log": ["OutputValidateNode: remediation_brief is empty or missing"],
            }

        service = MaterialDeclarationService()
        try:
            validated_brief = asyncio.run(service.validate_output(remediation_brief))
        except Exception as exc:
            return {
                "status": AgentStatus.ERROR.value,
                "error": str(exc),
                "error_log": [f"OutputValidateNode: {exc}"],
            }

        emit_trace_event("output_validated", {"brief_length": len(validated_brief)}, state)
        return {"remediation_brief": validated_brief, "status": AgentStatus.SUCCESS.value}
