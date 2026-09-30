from framework.schemas.agent_status import AgentStatus
from src.nodes.coverage_check_node import CoverageCheckNode


class TestCoverageCheckNode:
    def setup_method(self):
        self.node = CoverageCheckNode()

    def test_flags_missing_declaration(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        state = {
            "bom_data": {"parts": [{"part_number": "PN-1001"}, {"part_number": "PN-1002"}]},
            "declaration_data": [{"part_number": "PN-1001"}],
            "substance_matches": [],
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        gaps = result["coverage_gaps"]
        assert any(g["part_number"] == "PN-1002" for g in gaps)
        assert not any(g["part_number"] == "PN-1001" for g in gaps)
