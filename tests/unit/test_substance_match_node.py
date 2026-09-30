"""Includes the Rule 2 regression test from .claude/rules/test_rule.md:
mock mode must not depend on a secret being resolvable — a fresh CI checkout
has no env/ secret tree at all, so this must succeed with zero secrets bound.
"""

from framework.schemas.agent_status import AgentStatus
from src.nodes.substance_match_node import SubstanceMatchNode


def _base_state(**overrides) -> dict:
    state = {
        "declaration_data": [{"part_number": "PN-1001", "substances": ["Lead"]}],
        "correlation_id": "test-correlation",
        "session_id": "test-session",
        "thread_id": "test-thread",
        "trace_id": "test-trace",
        "node_history": [],
        "error_log": [],
    }
    state.update(overrides)
    return state


class TestSubstanceMatchNode:
    def setup_method(self):
        self.node = SubstanceMatchNode()

    def test_succeeds_in_mock_mode_with_no_secret_provider_bound(self, monkeypatch):
        """Regression test (test_rule.md Rule 2): a fresh CI checkout has no env/
        secret files at all. Mock mode must not depend on a secret being resolvable.
        Run WITHOUT any bound_secrets() context — current_secrets() falls back to
        NullProvider, matching the actual deploy-stg condition."""
        monkeypatch.setenv("USE_MOCK", "true")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("SUBSTANCE_INDEX_API_KEY", raising=False)

        result = self.node.execute(_base_state())

        assert result["status"] == AgentStatus.SUCCESS.value
        assert isinstance(result["substance_matches"], list)

    def test_missing_declaration_data_returns_error(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        result = self.node.execute(_base_state(declaration_data=[]))
        assert result["status"] == AgentStatus.ERROR.value
