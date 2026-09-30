from framework.schemas.agent_status import AgentStatus
from src.nodes.bom_parse_node import BomParseNode


class TestBomParseNode:
    def setup_method(self, monkeypatch=None):
        self.node = BomParseNode()

    def test_success_path_uses_validated_input(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        state = {"validated_input": "bom-ref-001", "node_history": [], "error_log": []}
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        assert "parts" in result["bom_data"]

    def test_falls_back_to_user_input_when_validated_input_absent(self, monkeypatch):
        """Inner-graph fresh-state rule: outer validated_input is not copied into
        the inner graph's initial_state — only user_input is present."""
        monkeypatch.setenv("USE_MOCK", "true")
        state = {"user_input": "bom-ref-001", "node_history": [], "error_log": []}
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value

    def test_missing_input_returns_error(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        state = {"node_history": [], "error_log": []}
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.ERROR.value
