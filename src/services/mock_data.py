"""AgentCore Platform v1.0"""

# Mock stub implementations for MaterialDeclarationService.
# One stub_* function per domain step (src/services/service.py).
# These are the only functioning path today — real integrations (BOM/declaration
# parsers, RoHS/REACH vector index, LLM brief drafting) are wired in a later sprint.

from typing import Any


async def stub_parse_bom(bom_ref: str) -> dict[str, Any]:
    return {
        "bom_ref": bom_ref,
        "parts": [
            {"part_number": "PN-1001", "revision": "A", "supplier_id": "SUP-01"},
            {"part_number": "PN-1002", "revision": "B", "supplier_id": "SUP-02"},
        ],
    }


async def stub_ingest_declarations(bom_data: dict[str, Any]) -> list[dict[str, Any]]:  # noqa: ARG001
    return [
        {
            "part_number": "PN-1001",
            "supplier_id": "SUP-01",
            "substances": ["Lead", "Cadmium"],
            "version": "2026-01-15",
        }
    ]


async def stub_match_substances(
    declaration_data: list[dict[str, Any]],
    credential_handle: str,  # noqa: ARG001
) -> list[dict[str, Any]]:
    return [
        {
            "part_number": decl["part_number"],
            "substance": substance,
            "exemption_code": None,
            "index_source": "rohs_reach_index_v2026.1",
        }
        for decl in declaration_data
        for substance in decl.get("substances", [])
    ]


async def stub_check_coverage(
    bom_data: dict[str, Any],
    declaration_data: list[dict[str, Any]],
    substance_matches: list[dict[str, Any]],  # noqa: ARG001
) -> list[dict[str, Any]]:
    declared_parts = {decl["part_number"] for decl in declaration_data}
    return [
        {
            "part_number": part["part_number"],
            "gap_type": "missing_declaration",
            "detail": f"No declaration on file for part {part['part_number']}",
        }
        for part in bom_data.get("parts", [])
        if part["part_number"] not in declared_parts
    ]


async def stub_compile_exceptions(
    coverage_gaps: list[dict[str, Any]], substance_matches: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "matched_substances": substance_matches,
        "exceptions": coverage_gaps,
        "provenance": "mock_evidence_matrix_v1",
    }


async def stub_draft_brief(
    evidence_matrix: dict[str, Any],
    coverage_gaps: list[dict[str, Any]],
    credential_handle: str,  # noqa: ARG001
) -> str:
    gap_count = len(coverage_gaps)
    return (
        f"Remediation Brief: {gap_count} coverage gap(s) found. "
        f"Evidence provenance: {evidence_matrix.get('provenance', 'unknown')}. "
        "This brief presents evidence findings only."
    )
