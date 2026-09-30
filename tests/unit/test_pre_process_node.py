from framework.schemas.agent_status import AgentStatus
from src.nodes.pre_process_node import PreProcessNode


class TestPreProcessNode:
    def setup_method(self):
        self.node = PreProcessNode()

    def test_success_path(self):
        state = {"user_input": "  bom-ref-001  ", "node_history": [], "error_log": []}
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        assert result["validated_input"] == "bom-ref-001"

    def test_empty_input_returns_error(self):
        state = {"user_input": "", "node_history": [], "error_log": []}
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.ERROR.value

    def test_extra_security_gate_input_rejects_oversized_payload(self):
        state = {"user_input": "x" * 50_001}
        import pytest
        from framework.errors import SecurityViolationError

        with pytest.raises(SecurityViolationError):
            self.node._extra_security_gate_input(state)

    def test_extra_security_gate_input_returns_state_when_within_limit(self):
        state = {"user_input": "bom-ref-001"}
        result = self.node._extra_security_gate_input(state)
        assert result is state
