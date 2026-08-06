"""K4 - Provider Activation (unit tests, no network).

Membuktikan seluruh provider baseline yang SUDAH TERSEDIA diaktifkan, dan
provider yang BELUM LENGKAP didokumentasikan (bukan error, bukan konsep baru):
- 5 provider LLM dengan LLMAdapter (openai/anthropic/gemini/deepseek/ollama)
  -> status 'active'.
- provider non-LLM (openclaw/filesystem/shell/sqlite/docker) -> status
  'missing' + didokumentasikan sebagai deferred; provider lain tetap lanjut.
- `available()` per provider tetap gate kredensial (no call saat tak ada env).
- Setiap provider active terdaftar di registry dengan link connector contract.
"""
from sam.api.llm_wiring import (
    LLM_CONNECTOR_CONTRACT_ID,
    llm_provider_layer,
    provider_readiness,
)
from sam.providers.execution.provider_executor import PROVIDER_ENV


ACTIVE_PP = {"openai", "anthropic", "gemini", "deepseek", "ollama"}
NON_LLM = {"openclaw", "filesystem", "shell", "sqlite", "docker"}


class TestProviderActivation:
    """Seluruh provider baseline dinilai & didokumentasikan."""

    def test_readiness_meliputi_semua_baseline(self) -> None:
        report = provider_readiness()
        # Semua provider baseline dari ProviderExecutor tercakup.
        baseline = set(PROVIDER_ENV.keys())
        report_ids = {r["provider_id"] for r in report["providers"]}
        assert baseline == report_ids

    def test_provider_llm_adapter_aktif(self) -> None:
        report = provider_readiness()
        by_id = {r["provider_id"]: r for r in report["providers"]}
        for pid in ACTIVE_PP:
            assert by_id[pid]["adapter"] is True
            assert by_id[pid]["status"] == "active"

    def test_provider_nonllm_didokumentasikan_missing(self) -> None:
        report = provider_readiness()
        by_id = {r["provider_id"]: r for r in report["providers"]}
        for pid in NON_LLM:
            assert by_id[pid]["adapter"] is False
            assert by_id[pid]["status"] == "missing"

    def test_tidak_ada_konsep_provider_baru(self) -> None:
        report = provider_readiness()
        # 10 provider baseline persis (5 LLM + 5 non-LLM), bukan tambahan baru.
        assert report["total"] == 10
        assert report["active"] == 5
        assert report["missing_documented"] == 5

    def test_contract_dipakai_seragam(self) -> None:
        assert provider_readiness()["contract"] == LLM_CONNECTOR_CONTRACT_ID


class TestProviderCredentialGating:
    """available() tetap gate kredensial; tanpa env -> unavailable, no call."""

    def test_openai_unavailable_tanpa_env(self) -> None:
        import os
        os.environ.pop("OPENAI_API_KEY", None)
        assert llm_provider_layer.available("openai") is False
