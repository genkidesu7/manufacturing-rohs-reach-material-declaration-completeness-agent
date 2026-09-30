"""AgentCore Platform v1.0"""

# Cat 2 — Manufacturing RoHS/REACH Material Declaration Completeness Agent.
# Outer graph: fixed 5-node backbone (AgentBaseGraph). Domain complexity lives in
# the inner graph (src/graph/domain_workflow_graph.py), wrapped by
# MaterialDeclarationWorkflowGraphNode in the `main` slot. See docs/02_design.md.

from typing import Any, ClassVar

from framework.graph.agent_base_graph import AgentBaseGraph
from framework.nodes.graph_node import GraphNode
from framework.schemas.agent_state import AgentState
from src.nodes.post_process_node import PostProcessNode
from src.nodes.pre_process_node import PreProcessNode
from src.schemas.state import State


class MaterialDeclarationWorkflowGraphNode(GraphNode):
    """Wraps the inner MaterialDeclarationWorkflowGraph; assigned to the `main` slot."""

    # docs/02_design.md Design Decision Record: propagate — a reconciliation error
    # must fail the whole invocation, not degrade to a partial/silent brief.
    error_strategy: ClassVar[str] = "propagate"

    # docs/01_proposal.md HITL Gate: N/A (industry is MFG, not HCR/INS/FIN/GOV).
    propagate_hitl: ClassVar[bool] = False

    def get_subgraph(self) -> Any:
        from src.graph.domain_workflow_graph import MaterialDeclarationWorkflowGraph

        return MaterialDeclarationWorkflowGraph(config=self._parent_config())

    def extract_input(self, state: AgentState) -> str:
        return str(state.get("validated_input", state.get("user_input", "")))

    def merge_output(self, state: AgentState, sub_result: dict[str, Any]) -> dict[str, Any]:
        return {
            "evidence_matrix": sub_result.get("evidence_matrix", {}),
            "coverage_gaps": sub_result.get("coverage_gaps", []),
            "remediation_brief": sub_result.get("remediation_brief", ""),
            "status": sub_result.get("status"),
        }

    def _parent_config(self) -> dict[str, Any]:
        return {}


class MaterialDeclarationCompletenessGraph(AgentBaseGraph):
    """Manufacturing RoHS/REACH Material Declaration Completeness Agent.

    Backbone: initialize → pre_process → main → post_process → finalize (fixed).
    Domain logic is encapsulated in MaterialDeclarationWorkflowGraphNode (`main` slot).
    """

    @property
    def name(self) -> str:
        return "mfg-c2-143"

    @property
    def state_schema(self) -> type:
        return State

    def register_nodes(self) -> None:
        super().register_nodes()  # injects InitializeNode + FinalizeNode

        self._nodes["pre_process"] = PreProcessNode()
        self._nodes["main"] = MaterialDeclarationWorkflowGraphNode()
        self._nodes["post_process"] = PostProcessNode()

    # add_edges() is NOT overridden — backbone wiring belongs to the framework.
