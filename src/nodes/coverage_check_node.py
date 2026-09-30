"""AgentCore Platform v1.0"""

import asyncio
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.service import MaterialDeclarationService


class CoverageCheckNode(FunctionNode):
    """Join BOM parts to declarations; flag missing, stale, or contradictory records."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        bom_data = state.get("bom_data") or {}
        declaration_data = state.get("declaration_data") or []
        substance_matches = state.get("substance_matches") or []

        service = MaterialDeclarationService()
        try:
            coverage_gaps = asyncio.run(service.check_coverage(bom_data, declaration_data, substance_matches))
        except Exception as exc:
            return {
                "status": AgentStatus.ERROR.value,
                "error": str(exc),
                "error_log": [f"CoverageCheckNode: {exc}"],
            }

        emit_trace_event("coverage_checked", {"gap_count": len(coverage_gaps)}, state)
        return {"coverage_gaps": coverage_gaps, "status": AgentStatus.SUCCESS.value}
