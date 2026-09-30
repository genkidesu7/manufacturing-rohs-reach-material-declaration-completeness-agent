import pytest

from src.services.service import MaterialDeclarationService


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "true")
    return MaterialDeclarationService()


class TestMaterialDeclarationServiceMockMode:
    @pytest.mark.asyncio
    async def test_parse_bom(self, service):
        result = await service.parse_bom("bom-ref-001")
        assert "parts" in result

    @pytest.mark.asyncio
    async def test_ingest_declarations(self, service):
        bom_data = await service.parse_bom("bom-ref-001")
        result = await service.ingest_declarations(bom_data)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_match_substances_requires_credential_handle(self, service):
        with pytest.raises(ValueError):
            await service.match_substances([{"substances": ["Lead"]}], "")

    @pytest.mark.asyncio
    async def test_draft_brief_requires_credential_handle(self, service):
        with pytest.raises(ValueError):
            await service.draft_brief({}, [], "")


class TestMaterialDeclarationServiceValidateOutput:
    @pytest.mark.asyncio
    async def test_blocks_approval_language(self, service):
        with pytest.raises(ValueError):
            await service.validate_output("This declaration set is approved.")

    @pytest.mark.asyncio
    async def test_appends_disclaimer_once(self, service):
        result = await service.validate_output("Findings only.")
        assert result.count("DISCLAIMER:") == 1

    @pytest.mark.asyncio
    async def test_does_not_duplicate_existing_disclaimer(self, service):
        brief = "Findings.\n\nDISCLAIMER: already present."
        result = await service.validate_output(brief)
        assert result == brief


class TestMaterialDeclarationServiceRealModeNotWired:
    @pytest.mark.asyncio
    async def test_parse_bom_raises_without_mock_mode(self, monkeypatch):
        monkeypatch.delenv("USE_MOCK", raising=False)
        monkeypatch.delenv("STG_MOCK_MODE", raising=False)
        service = MaterialDeclarationService()
        with pytest.raises(NotImplementedError):
            await service.parse_bom("bom-ref-001")
