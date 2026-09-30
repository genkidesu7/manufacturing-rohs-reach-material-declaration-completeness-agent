"""AgentCore Platform v1.0"""

import asyncio
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.invocation_context import InvocationContext
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.mock_mode import mock_mode_enabled
from src.services.service import MaterialDeclarationService


class SubstanceMatchNode(FunctionNode):
    """RAG-match declared substances against the RoHS/REACH substance/exemption index."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        declaration_data = state.get("declaration_data") or []
        if not declaration_data:
            return {
                "status": AgentStatus.ERROR.value,
                "error": "SubstanceMatchNode: declaration_data is empty or missing",
                "error_log": ["SubstanceMatchNode: declaration_data is empty or missing"],
            }

        # .claude/rules/implementation_rule.md Rule 2: mock mode must short-circuit
        # before any credential is required — a fresh CI checkout has no provisioned
        # secrets, so this must not call ctx.secrets.require() when mocked.
        ctx = InvocationContext.from_state(state)
        credential_handle = "mock" if mock_mode_enabled() else ctx.secrets.require("SUBSTANCE_INDEX_API_KEY")

        service = MaterialDeclarationService()
        try:
            substance_matches = asyncio.run(service.match_substances(declaration_data, credential_handle))
        except Exception as exc:
            return {
                "status": AgentStatus.ERROR.value,
                "error": str(exc),
                "error_log": [f"SubstanceMatchNode: {exc}"],
            }

        emit_trace_event("substances_matched", {"match_count": len(substance_matches)}, state)
        return {"substance_matches": substance_matches, "status": AgentStatus.SUCCESS.value}
