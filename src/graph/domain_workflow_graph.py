"""AgentCore Platform v1.0"""

from typing import Any

# src/graph/domain_workflow_graph.py — inner graph for the Cat 2 `main` slot.
# Instantiated by MaterialDeclarationWorkflowGraphNode.get_subgraph() in src/graph/graph.py.
# Implements docs/02_design.md's 7-node linear domain pipeline.

from langgraph.graph import END, START

from framework.graph.base_graph import BaseGraph
from framework.schemas.agent_status import AgentStatus
from src.nodes.bom_parse_node import BomParseNode
from src.nodes.brief_draft_node import BriefDraftNode
from src.nodes.coverage_check_node import CoverageCheckNode
from src.nodes.declaration_ingest_node import DeclarationIngestNode
from src.nodes.exception_compile_node import ExceptionCompileNode
from src.nodes.output_validate_node import OutputValidateNode
from src.nodes.substance_match_node import SubstanceMatchNode
from src.schemas.state import State


class MaterialDeclarationWorkflowGraph(BaseGraph):
    """Inner graph implementing the BOM-to-declaration reconciliation pipeline.

    Pipeline (linear, docs/02_design.md):
        START → bom_parse → declaration_ingest → substance_match → coverage_check
              → exception_compile → brief_draft → output_validate → END
    """

    # ── Identity ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "material_declaration_workflow"

    @property
    def state_schema(self) -> type:
        return State

    # ── Config validation ─────────────────────────────────────────────────────

    def _validate_config(self) -> None:
        """No mandatory config for this inner graph."""
        pass

    # ── Node registration ─────────────────────────────────────────────────────

    def register_nodes(self) -> None:
        """No super() call — BaseGraph.register_nodes() is abstract.

        Do NOT register initialize/finalize here; those are outer backbone concerns
        handled by AgentBaseGraph in src/graph/graph.py.
        """
        self._nodes["bom_parse"] = BomParseNode()
        self._nodes["declaration_ingest"] = DeclarationIngestNode()
        self._nodes["substance_match"] = SubstanceMatchNode()
        self._nodes["coverage_check"] = CoverageCheckNode()
        self._nodes["exception_compile"] = ExceptionCompileNode()
        self._nodes["brief_draft"] = BriefDraftNode()
        self._nodes["output_validate"] = OutputValidateNode()

    # ── Edge wiring ───────────────────────────────────────────────────────────

    def add_edges(self) -> None:
        """Linear topology — every domain step always runs; exceptions are data,
        not routing decisions (docs/02_design.md Data Flow)."""
        self._sg.add_edge(START, "bom_parse")
        self._sg.add_edge("bom_parse", "declaration_ingest")
        self._sg.add_edge("declaration_ingest", "substance_match")
        self._sg.add_edge("substance_match", "coverage_check")
        self._sg.add_edge("coverage_check", "exception_compile")
        self._sg.add_edge("exception_compile", "brief_draft")
        self._sg.add_edge("brief_draft", "output_validate")
        self._sg.add_edge("output_validate", END)

    # ── Routing ───────────────────────────────────────────────────────────────

    def route(self, state: State) -> str:
        """Required by BaseGraph ABC; never called (no conditional edges)."""
        return END if state.get("status") == AgentStatus.ERROR.value else "output_validate"

    # ── Output shape ──────────────────────────────────────────────────────────

    def get_output(self, state: State) -> dict[str, Any]:
        """Shape the sub_result dict consumed by MaterialDeclarationWorkflowGraphNode.merge_output()."""
        return {
            "evidence_matrix": state.get("evidence_matrix", {}),
            "coverage_gaps": state.get("coverage_gaps", []),
            "remediation_brief": state.get("remediation_brief", ""),
            "status": state.get("status"),
            "trace_id": state.get("trace_id"),
            "correlation_id": state.get("correlation_id"),
            "node_history": state.get("node_history", []),
            "error_log": state.get("error_log", []),
        }
