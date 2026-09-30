"""AgentCore Platform v1.0"""

import asyncio
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.service import MaterialDeclarationService


class ExceptionCompileNode(FunctionNode):
    """Build a traceable evidence matrix and exception list with provenance."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        coverage_gaps = state.get("coverage_gaps") or []
        substance_matches = state.get("substance_matches") or []

        service = MaterialDeclarationService()
        try:
            evidence_matrix = asyncio.run(service.compile_exceptions(coverage_gaps, substance_matches))
        except Exception as exc:
            return {
                "status": AgentStatus.ERROR.value,
                "error": str(exc),
                "error_log": [f"ExceptionCompileNode: {exc}"],
            }

        emit_trace_event(
            "exceptions_compiled",
            {"exception_count": len(evidence_matrix.get("exceptions", []))},
            state,
        )
        return {"evidence_matrix": evidence_matrix, "status": AgentStatus.SUCCESS.value}
