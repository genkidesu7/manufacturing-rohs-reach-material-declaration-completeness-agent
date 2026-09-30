"""Real .compile() + .invoke() integration test for the outer graph.

Per development-cycle/07_test_stage.md's Definition of Done: exercises the
compiled LangGraph runtime (schema projection included), not just stubbed
execute()/route() calls with a plain dict.
"""

from framework.schemas.invocation_context import InvocationContext
from framework.schemas.trust_level import TrustLevel
from framework.secrets.context import bound_secrets
from shared.secrets.inmemory_provider import InMemoryProvider

from src.graph.graph import MaterialDeclarationCompletenessGraph


def test_invoke_end_to_end_success(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "true")

    agent = MaterialDeclarationCompletenessGraph(config={"max_retry": 1})
    agent.compile()
    provider = InMemoryProvider(
        {"ANTHROPIC_API_KEY": "test-value", "SUBSTANCE_INDEX_API_KEY": "test-value"}
    )
    agent.provision_secrets(provider)
    ctx = InvocationContext(caller_trust_level=TrustLevel.VERIFIED_EXTERNAL)

    with bound_secrets(provider):
        result = agent.invoke("bom-ref-001", ctx=ctx)

    assert result["status"] == "success"
    output = result["output"]
    assert "remediation_brief" in output
    assert "DISCLAIMER:" in output["remediation_brief"]
    assert "coverage_gaps" in output
    assert "evidence_matrix" in output


def test_invoke_denies_anonymous_caller(monkeypatch):
    """S-1: nodes require VERIFIED_EXTERNAL; the default ANONYMOUS caller is denied."""
    monkeypatch.setenv("USE_MOCK", "true")

    agent = MaterialDeclarationCompletenessGraph(config={"max_retry": 1})
    agent.compile()
    provider = InMemoryProvider({})
    agent.provision_secrets(provider)

    with bound_secrets(provider):
        result = agent.invoke("bom-ref-001")

    assert result["status"] == "error"
