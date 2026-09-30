from framework.schemas.agent_status import AgentStatus
from src.nodes.exception_compile_node import ExceptionCompileNode


class TestExceptionCompileNode:
    def setup_method(self):
        self.node = ExceptionCompileNode()

    def test_builds_evidence_matrix_with_provenance(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK", "true")
        state = {
            "coverage_gaps": [{"part_number": "PN-1002", "gap_type": "missing_declaration"}],
            "substance_matches": [{"part_number": "PN-1001", "substance": "Lead"}],
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        matrix = result["evidence_matrix"]
        assert matrix["exceptions"] == state["coverage_gaps"]
        assert "provenance" in matrix
