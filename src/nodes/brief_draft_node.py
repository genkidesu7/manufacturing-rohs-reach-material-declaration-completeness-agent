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


class BriefDraftNode(FunctionNode):
    """Generate a structured, reviewer-ready remediation/decision brief."""

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        evidence_matrix = state.get("evidence_matrix") or {}
        coverage_gaps = state.get("coverage_gaps") or []

        # .claude/rules/implementation_rule.md Rule 2: mock mode must short-circuit
        # before any credential is required.
        ctx = InvocationContext.from_state(state)
        credential_handle = "mock" if mock_mode_enabled() else ctx.secrets.require("ANTHROPIC_API_KEY")

        service = MaterialDeclarationService()
        try:
            remediation_brief = asyncio.run(service.draft_brief(evidence_matrix, coverage_gaps, credential_handle))
        except Exception as exc:
            return {
                "status": AgentStatus.ERROR.value,
                "error": str(exc),
                "error_log": [f"BriefDraftNode: {exc}"],
            }

        emit_trace_event("brief_drafted", {"brief_length": len(remediation_brief)}, state)
        return {"remediation_brief": remediation_brief, "status": AgentStatus.SUCCESS.value}
