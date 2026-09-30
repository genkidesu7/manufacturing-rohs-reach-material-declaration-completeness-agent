from framework.schemas.agent_status import AgentStatus
from src.nodes.declaration_ingest_node import DeclarationIngestNode


class TestDeclarationIngestNode:
    def setup_method(self):
        self.node = DeclarationIngestNode()

    def test_success_path(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        state = {
            "bom_data": {"bom_ref": "bom-ref-001", "parts": [{"part_number": "PN-1001"}]},
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        assert isinstance(result["declaration_data"], list)

    def test_missing_bom_data_returns_error(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        state = {"node_history": [], "error_log": []}
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.ERROR.value
