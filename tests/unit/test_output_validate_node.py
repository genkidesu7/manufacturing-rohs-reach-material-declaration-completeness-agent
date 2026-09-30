from framework.schemas.agent_status import AgentStatus
from src.nodes.output_validate_node import OutputValidateNode


class TestOutputValidateNode:
    def setup_method(self):
        self.node = OutputValidateNode()

    def test_appends_disclaimer(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        state = {
            "remediation_brief": "1 coverage gap found.",
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        assert "DISCLAIMER:" in result["remediation_brief"]

    def test_blocks_approval_like_language(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        state = {
            "remediation_brief": "All parts approved for release.",
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.ERROR.value

    def test_missing_brief_returns_error(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        state = {"node_history": [], "error_log": []}
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.ERROR.value

    def test_extra_security_gate_output_requires_disclaimer(self):
        import pytest
        from framework.errors import SecurityViolationError

        with pytest.raises(SecurityViolationError):
            self.node._extra_security_gate_output({"remediation_brief": "No disclaimer here."})
