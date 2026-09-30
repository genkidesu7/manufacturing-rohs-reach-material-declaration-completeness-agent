"""Includes the Rule 2 regression test from .claude/rules/test_rule.md — see
tests/unit/test_substance_match_node.py for the full rationale."""

from framework.schemas.agent_status import AgentStatus
from src.nodes.brief_draft_node import BriefDraftNode


def _base_state(**overrides) -> dict:
    state = {
        "evidence_matrix": {"provenance": "mock_evidence_matrix_v1"},
        "coverage_gaps": [{"part_number": "PN-1002"}],
        "correlation_id": "test-correlation",
        "session_id": "test-session",
        "thread_id": "test-thread",
        "trace_id": "test-trace",
        "node_history": [],
        "error_log": [],
    }
    state.update(overrides)
    return state


class TestBriefDraftNode:
    def setup_method(self):
        self.node = BriefDraftNode()

    def test_succeeds_in_mock_mode_with_no_secret_provider_bound(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = self.node.execute(_base_state())

        assert result["status"] == AgentStatus.SUCCESS.value
        assert isinstance(result["remediation_brief"], str)
        assert result["remediation_brief"]
