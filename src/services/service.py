"""AgentCore Platform v1.0"""

# Service layer: domain queries, external API wrappers, data aggregation.
# Must NOT contain business logic, routing, or credentials.
# Nodes call this; this calls shared/services/ for external integrations.
#
# Mock-mode gate uses the shared mock_mode_enabled() helper (src/services/mock_mode.py)
# — see .claude/rules/implementation_rule.md Rule 1: it must accept STG_MOCK_MODE
# (what deploy-stg actually sets), not only USE_MOCK.

from __future__ import annotations

from typing import Any

from src.services.mock_mode import mock_mode_enabled

_APPROVAL_PHRASES = (
    "approved",
    "cleared for release",
    "compliant — ship",
    "compliant - ship",
    "certified compliant",
    "release approved",
)


class MaterialDeclarationService:
    """Domain service for BOM-to-declaration RoHS/REACH reconciliation.

    Usage from a node::

        service = MaterialDeclarationService()
        bom_data = await service.parse_bom(bom_ref)
    """

    def __init__(self) -> None:
        self._mock_mode: bool = mock_mode_enabled()

    async def parse_bom(self, bom_ref: str) -> dict[str, Any]:
        """Extract part numbers, revisions, and supplier IDs from the product BOM."""
        if self._mock_mode:
            from src.services.mock_data import stub_parse_bom

            return await stub_parse_bom(bom_ref)
        raise NotImplementedError(
            "MaterialDeclarationService.parse_bom: not yet wired. "
            "Wire shared/services/bom_parser in the next sprint."
        )

    async def ingest_declarations(self, bom_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse supplier declarations: part reference, substance list, version/date."""
        if self._mock_mode:
            from src.services.mock_data import stub_ingest_declarations

            return await stub_ingest_declarations(bom_data)
        raise NotImplementedError(
            "MaterialDeclarationService.ingest_declarations: not yet wired. "
            "Wire shared/services/declaration_parser in the next sprint."
        )

    async def match_substances(
        self, declaration_data: list[dict[str, Any]], credential_handle: str
    ) -> list[dict[str, Any]]:
        """RAG-match declared substances against the RoHS/REACH substance/exemption index."""
        if not credential_handle:
            raise ValueError(
                "MaterialDeclarationService.match_substances: credential_handle is empty — "
                "check InvocationContext configuration"
            )
        if self._mock_mode:
            from src.services.mock_data import stub_match_substances

            return await stub_match_substances(declaration_data, credential_handle)
        raise NotImplementedError(
            "MaterialDeclarationService.match_substances: not yet wired. "
            "Wire shared/services/vector_db in the next sprint."
        )

    async def check_coverage(
        self,
        bom_data: dict[str, Any],
        declaration_data: list[dict[str, Any]],
        substance_matches: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Join BOM parts to declarations; flag missing/stale/contradictory records."""
        if self._mock_mode:
            from src.services.mock_data import stub_check_coverage

            return await stub_check_coverage(bom_data, declaration_data, substance_matches)
        raise NotImplementedError(
            "MaterialDeclarationService.check_coverage: not yet wired. "
            "Wire real declaration-validity rule set in the next sprint."
        )

    async def compile_exceptions(
        self,
        coverage_gaps: list[dict[str, Any]],
        substance_matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build a traceable evidence matrix and exception list with provenance."""
        if self._mock_mode:
            from src.services.mock_data import stub_compile_exceptions

            return await stub_compile_exceptions(coverage_gaps, substance_matches)
        raise NotImplementedError(
            "MaterialDeclarationService.compile_exceptions: not yet wired. "
            "Wire real evidence-matrix builder in the next sprint."
        )

    async def draft_brief(
        self,
        evidence_matrix: dict[str, Any],
        coverage_gaps: list[dict[str, Any]],
        credential_handle: str,
    ) -> str:
        """Generate a structured, reviewer-ready remediation/decision brief."""
        if not credential_handle:
            raise ValueError(
                "MaterialDeclarationService.draft_brief: credential_handle is empty — "
                "check InvocationContext configuration"
            )
        if self._mock_mode:
            from src.services.mock_data import stub_draft_brief

            return await stub_draft_brief(evidence_matrix, coverage_gaps, credential_handle)
        raise NotImplementedError(
            "MaterialDeclarationService.draft_brief: not yet wired. " "Wire shared/services/llm in the next sprint."
        )

    async def validate_output(self, remediation_brief: str) -> str:
        """Block approval-like language; append the mandatory human-review disclaimer.

        Pure domain check (no external call), so it runs identically in mock and real
        mode — deliberately has no mock/real branch, unlike the other methods above.
        """
        lowered = remediation_brief.lower()
        for phrase in _APPROVAL_PHRASES:
            if phrase in lowered:
                raise ValueError(
                    f"MaterialDeclarationService.validate_output: approval-like language "
                    f"'{phrase}' detected in remediation brief — output blocked."
                )
        disclaimer = (
            "\n\nDISCLAIMER: This brief presents evidence and exception findings only. "
            "It is not an approval, certification, or release decision. "
            "Mandatory human compliance-reviewer sign-off is required before release."
        )
        if "DISCLAIMER:" in remediation_brief:
            return remediation_brief
        return remediation_brief + disclaimer
