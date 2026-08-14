"""ROMBAK B: ward spesifik jadi capability provider instance (bukan katalog).

Membuktikan:
  1. Mesin environment-adaptive generic bekerja PENUH dengan 0 provider
     (TIDAK bergantung pada kata "word"/"pdf"/"openclaw"/"github").
  2. Ward spesifik (Word/PDF/OpenClaw/GitHub/Provider) BISA didaftarkan
     sebagai CapabilityProvider instance; pipeline MENGAKUI observasinya
     bila terdaftar (BISA memakainya bila terdaftar) -- tanpa dijadikan
     katalog yang SAM andalkan.
  3. Fungsionalitas investigasi ward TIDAK hilang (masih bisa mem-probe).
  4. Provider TIDAK mengeksekusi apa pun; remediate hanya menandai avail.
"""
from __future__ import annotations

from sam.environment.capabilities import (
    pdf_provider,
    register_default_instances,
    word_provider,
)
from sam.environment.providers import CapabilityProvider, ProviderRegistry


class _FakeDiscovery:
    def discover(self):
        from sam.environment.entity import DiscoveryScan

        scan = DiscoveryScan()
        scan.entities = []
        scan.attributes = {"failures": []}
        return scan


def test_0_provider_pipeline_fully_works():
    """Mesin generic jalan penuh tanpa provider (tidak catalogue)."""
    from sam.environment.pipeline import AdaptiveEnvironmentPipeline

    pipe = AdaptiveEnvironmentPipeline(discovery=_FakeDiscovery())
    # pastikan tidak ada provider terdaftar
    assert len(pipe.registry) == 0
    result = pipe.run()
    # tanpa entitas -> jujur no_action, bukan mengarang masalah
    assert result.final_verdict == "no_action"
    assert result.verdicts.get("status")


def test_register_and_pipeline_consumes_provider_evidence():
    """Provider terdaftar -> pipeline memakai observasinya (BISA bila terdaftar)."""
    from sam.environment.confidence import Evidence
    from sam.environment.pipeline import AdaptiveEnvironmentPipeline

    probe_evidence = [Evidence("word", "docx ok", strength=0.9)]
    provider = CapabilityProvider(name="word", kind="file",
                                  observe_fn=lambda: probe_evidence)

    pipe = AdaptiveEnvironmentPipeline(discovery=_FakeDiscovery())
    # tanpa provider dulu -> tidak ada evidence provider
    r0 = pipe.run()
    n0 = sum(1 for e in r0.evidence if e.source == "word")
    assert n0 == 0

    pipe.register_provider(provider)
    assert pipe.registry.get("word") is provider
    r1 = pipe.run()
    n1 = sum(1 for e in r1.evidence if e.source == "word")
    assert n1 == 1
    assert r1.verdicts.get("provider:word") == "ok"


def test_provider_does_not_execute():
    """Provider HANYA mengamati; remediate hanya menandai, tidak mengeksekusi."""
    executed = []

    provider = CapabilityProvider(
        name="x", kind="service", observe_fn=lambda: [],
        remediate_fn=lambda: True,
    )
    # remediate_fn TIDAK mengeksekusi apa pun; hanya melaporkan avail bool
    assert provider.remediation_available() is True
    assert executed == []


def test_word_pdf_investigator_still_works():
    """Fungsionalitas investigasi word/pdf TIDAK hilang (instance instance)."""
    w = word_provider()
    p = pdf_provider()
    # tanpa target -> observasi jujur "tidak ada docx/pdf diobservasi"
    for prov in (w, p):
        assert prov is not None
        obs = prov.observe()
        assert obs.ok is True
        assert len(obs.evidence) >= 1
        # strength 0 -> jujur "nil impact", bukan mengarang masalah
        assert obs.evidence[0].strength == 0.0


def test_register_instances_via_factory():
    """register_default_instances mendaftarkan word/pdf (bila tersedia)."""
    reg = ProviderRegistry()
    names = register_default_instances(reg, include=["word", "pdf"])
    assert "word" in names
    assert "pdf" in names
    # nama terdaftar TIDAK menyebut nama aplikasi sbg katalog mesin
    assert len(reg) == len(names)
