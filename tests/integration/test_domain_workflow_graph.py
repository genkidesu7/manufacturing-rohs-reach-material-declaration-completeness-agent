"""Real .compile() + .invoke() integration test for the inner domain workflow graph."""

from framework.schemas.invocation_context import InvocationContext
from framework.schemas.trust_level import TrustLevel
from framework.secrets.context import bound_secrets
from shared.secrets.inmemory_provider import InMemoryProvider

from src.graph.domain_workflow_graph import MaterialDeclarationWorkflowGraph


def test_inner_graph_invoke_end_to_end_success(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "true")

    inner = MaterialDeclarationWorkflowGraph(config={"max_retry": 1})
    inner.compile()
    provider = InMemoryProvider(
        {"ANTHROPIC_API_KEY": "test-value", "SUBSTANCE_INDEX_API_KEY": "test-value"}
    )
    inner.provision_secrets(provider)
    ctx = InvocationContext(caller_trust_level=TrustLevel.VERIFIED_EXTERNAL)

    with bound_secrets(provider):
        result = inner.invoke("bom-ref-001", ctx=ctx)

    assert result["status"] == "success"
    assert result["node_history"] == [
        "BomParseNode",
        "DeclarationIngestNode",
        "SubstanceMatchNode",
        "CoverageCheckNode",
        "ExceptionCompileNode",
        "BriefDraftNode",
        "OutputValidateNode",
    ]
    assert "DISCLAIMER:" in result["remediation_brief"]
