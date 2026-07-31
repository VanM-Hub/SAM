"""Test Sprint 238 — Provider Certification 7 dimensi (Program A).
Semua adapter LLM disertifikasi terhadap 7 dimensi: structure, integrity,
consistency, completeness, determinism, immutability, preview_only.
"""
import pytest

from sam.providers.certification_program.program_certifier import (
    ProgramCertifier,
    CertificationCriterion,
    CertificationResult,
    ProgramScore,
)
from sam.providers.integration.runtime_integration import ProviderIntegration
from sam.providers.openai import OpenAIAdapter
from sam.providers.anthropic import AnthropicAdapter
from sam.providers.gemini import GeminiAdapter
from sam.providers.deepseek import DeepSeekAdapter
from sam.providers.ollama import OllamaAdapter

FROZEN_DTOS = [
    CertificationCriterion,
    CertificationResult,
    ProgramScore,
]


def build_full_integration():
    it = ProviderIntegration()
    it.register(OpenAIAdapter())
    it.register(AnthropicAdapter())
    it.register(GeminiAdapter())
    it.register(DeepSeekAdapter())
    it.register(OllamaAdapter())
    return it


class TestProgramCertifier:
    def test_7_dimensions_all_certified(self):
        it = build_full_integration()
        cert = ProgramCertifier(it)
        results = cert.certify_all()
        assert len(results) == 5
        for r in results:
            assert r.certified is True
            assert r.total == 7
            assert r.passed_count == 7

    def test_certified_ids_all(self):
        it = build_full_integration()
        cert = ProgramCertifier(it)
        assert cert.certified_ids() == it.list_providers()

    def test_each_dimension_present(self):
        it = build_full_integration()
        cert = ProgramCertifier(it)
        r = cert.certify("openai")
        names = {c.name for c in r.criteria}
        assert names == {
            "structure", "integrity", "consistency", "completeness",
            "determinism", "immutability", "preview_only",
        }

    def test_unknown_provider_not_certified(self):
        it = build_full_integration()
        cert = ProgramCertifier(it)
        r = cert.certify("nope")
        assert r.certified is False
        assert r.total == 7
        assert r.passed_count == 0

    def test_score_fully_certified(self):
        it = build_full_integration()
        cert = ProgramCertifier(it)
        score = cert.score()
        assert score.provider_count == 5
        assert score.certified_count == 5
        assert score.fully_certified is True
        assert score.average_score == 100.0

    def test_score_empty(self):
        cert = ProgramCertifier(ProviderIntegration())
        score = cert.score()
        assert score.provider_count == 0
        assert score.certified_count == 0
        assert score.fully_certified is False
        assert score.average_score == 0.0

    def test_immutability_dimension_checks_frozen(self):
        it = build_full_integration()
        cert = ProgramCertifier(it)
        r = cert.certify("gemini")
        immut = next(c for c in r.criteria if c.name == "immutability")
        assert immut.passed is True


class TestScoreComputation:
    def test_score_calculation(self):
        it = build_full_integration()
        cert = ProgramCertifier(it)
        r = cert.certify("anthropic")
        assert r.score == 100.0
        assert 0 <= r.passed_count <= r.total


class TestCertificationImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
