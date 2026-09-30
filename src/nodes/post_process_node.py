"""AgentCore Platform v1.0"""

from typing import Any, ClassVar

from framework.errors import SecurityViolationError
from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

# docs/01_proposal.md §11 risk #1: a compliance reviewer must never see the brief
# treated as a de facto approval. This is a final backstop re-check on top of
# MaterialDeclarationService.validate_output (which output_validate_node already ran).
_APPROVAL_PHRASES = (
    "approved",
    "cleared for release",
    "compliant — ship",
    "compliant - ship",
    "certified compliant",
    "release approved",
)


class PostProcessNode(FunctionNode):
    """Assemble the final reviewer-facing result."""

    # docs/02_design.md Design Decision Record: caller is an internal PLM/BOM export
    # pipeline or an authenticated compliance reviewer, never anonymous.
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def _extra_security_gate_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """S-3 domain check: block approval-like language, require the disclaimer."""
        final = result.get("result") or {}
        brief = final.get("remediation_brief", "") if isinstance(final, dict) else ""
        lowered = brief.lower()
        for phrase in _APPROVAL_PHRASES:
            if phrase in lowered:
                raise SecurityViolationError(
                    f"PostProcessNode: approval-like language '{phrase}' detected in " "final output — blocked."
                )
        if brief and "DISCLAIMER:" not in brief:
            raise SecurityViolationError(
                "PostProcessNode: mandatory human-review disclaimer missing from " "remediation brief."
            )
        return result

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        result = {
            "evidence_matrix": state.get("evidence_matrix", {}),
            "coverage_gaps": state.get("coverage_gaps", []),
            "remediation_brief": state.get("remediation_brief", ""),
        }
        emit_trace_event("result_formatted", {"gap_count": len(result["coverage_gaps"])}, state)
        return {
            "result": result,
            "status": AgentStatus.SUCCESS.value,
        }
