import pytest
from framework.errors import SecurityViolationError
from framework.schemas.agent_status import AgentStatus
from src.nodes.post_process_node import PostProcessNode


class TestPostProcessNode:
    def setup_method(self):
        self.node = PostProcessNode()

    def test_success_path_assembles_result(self):
        state = {
            "evidence_matrix": {"provenance": "x"},
            "coverage_gaps": [{"part_number": "PN-1"}],
            "remediation_brief": "Brief text.\n\nDISCLAIMER: not an approval.",
            "node_history": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        assert result["result"]["coverage_gaps"] == [{"part_number": "PN-1"}]

    def test_extra_security_gate_output_blocks_approval_language(self):
        result = {"result": {"remediation_brief": "This part is approved for release."}}
        with pytest.raises(SecurityViolationError):
            self.node._extra_security_gate_output(result)

    def test_extra_security_gate_output_requires_disclaimer(self):
        result = {"result": {"remediation_brief": "Just findings, no disclaimer text."}}
        with pytest.raises(SecurityViolationError):
            self.node._extra_security_gate_output(result)

    def test_extra_security_gate_output_passes_with_disclaimer(self):
        result = {"result": {"remediation_brief": "Findings.\n\nDISCLAIMER: not an approval."}}
        returned = self.node._extra_security_gate_output(result)
        assert returned is result
