"""AgentCore Platform v1.0"""

import asyncio
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.service import MaterialDeclarationService


class BomParseNode(FunctionNode):
    """Extract part numbers, revisions, and supplier IDs from the product BOM."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        # Inner-graph fresh-state rule: the outer pre_process's validated_input is not
        # copied into this inner graph's initial_state — fall back to user_input.
        bom_ref = state.get("validated_input", state.get("user_input", ""))
        if not bom_ref:
            return {
                "status": AgentStatus.ERROR.value,
                "error": "BomParseNode: bom_ref is empty or missing",
                "error_log": ["BomParseNode: bom_ref is empty or missing"],
            }

        service = MaterialDeclarationService()
        try:
            bom_data = asyncio.run(service.parse_bom(bom_ref))
        except Exception as exc:
            return {
                "status": AgentStatus.ERROR.value,
                "error": str(exc),
                "error_log": [f"BomParseNode: {exc}"],
            }

        emit_trace_event("bom_parsed", {"part_count": len(bom_data.get("parts", []))}, state)
        return {"bom_data": bom_data, "status": AgentStatus.SUCCESS.value}
