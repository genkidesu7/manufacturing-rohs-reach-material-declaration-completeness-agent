"""AgentCore Platform v1.0"""

import asyncio
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.service import MaterialDeclarationService


class DeclarationIngestNode(FunctionNode):
    """Parse supplier material declarations: part reference, substance list, version/date."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        bom_data = state.get("bom_data") or {}
        if not bom_data:
            return {
                "status": AgentStatus.ERROR.value,
                "error": "DeclarationIngestNode: bom_data is empty or missing",
                "error_log": ["DeclarationIngestNode: bom_data is empty or missing"],
            }

        service = MaterialDeclarationService()
        try:
            declaration_data = asyncio.run(service.ingest_declarations(bom_data))
        except Exception as exc:
            return {
                "status": AgentStatus.ERROR.value,
                "error": str(exc),
                "error_log": [f"DeclarationIngestNode: {exc}"],
            }

        emit_trace_event("declarations_ingested", {"declaration_count": len(declaration_data)}, state)
        return {"declaration_data": declaration_data, "status": AgentStatus.SUCCESS.value}
