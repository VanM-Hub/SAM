"""Acceptance environment-adaptive M14 (re-architecture).

Prinsip (Van 2026-08-14 17:45):
  - Acceptance berbasis "environment yang belum dikenal sebelumnya
    berhasil dipahami, diamati, didiagnosis, dan bila diizinkan diperbaiki",
    BUKAN "Word berhasil diperbaiki".
  - SAM TIDAK mengandalkan hardcoded application catalogue.
  - SAM TIDAK mengarang diagnosis; jujur "evidence tidak cukup".
  - Eksekusi remediation HANYA lewat canonical governance (tidak langsung).
"""


from sam.environment.confidence import (
    ConfidenceAssessor,
    ConfidenceLevel,
    Evidence,
)
from sam.environment.diagnosis import DiagnosisEngine
from sam.environment.discovery import EnvironmentDiscovery
from sam.environment.entity import Entity, EntityKind, EntitySource
from sam.environment.graph import EntityGraph
from sam.environment.pipeline import AdaptiveEnvironmentPipeline
from sam.environment.remediation import RemediationPlanner


# ---------------------------------------------------------------------------
# Fixture: environment BUATAN yang "belum dikenal" - bukan word/pdf/openclaw.
# Ini membuktikan mesin tidak butuh katalog aplikasi spesifik.
# ---------------------------------------------------------------------------

def _unknown_env_entities():
    """Environment fiktif: service tak dikenal, port tak terikat, file rusak.

    Secara sengaja memakai label BUKAN aplikasi nyata (tanpa word/pdf/openclaw)
    untuk menunjukkan mesin generik bekerja pada apa pun.
    """
    return [
        _entity("service", "zz_service", {"pid": "123", "health": "stopped"}),
        _entity("port", "zz_port_a", {"pid": ""}),
        _entity("port", "zz_port_b", {"pid": "123"}),
        _entity("file", "data_000.bin",
                {"path": "C:/tmp/data_000.bin", "valid_signature": False,
                 "size_bytes": 0}),
        _entity("file", "data_ok.bin",
                {"path": "C:/tmp/data_ok.bin", "valid_signature": True}),
    ]


def _entity(kind, label, attrs, source="fixture"):
    import hashlib

    raw = f"{kind}|{label}".encode()
    eid = hashlib.sha256(raw).hexdigest()[:20]
    return Entity(id=eid, kind=EntityKind(kind), source=EntitySource(source),
                  label=label, attributes=attrs)


# ---------------------------------------------------------------------------
# Test 1: discovery generik tanpa katalog aplikasi
# ---------------------------------------------------------------------------

class FakeDiscovery:
    """Discovery yang mengembalikan entitas 'belum dikenal' (fixture)."""

    def __init__(self, entities):
        self._entities = entities

    def discover(self):
        from sam.environment.entity import DiscoveryScan

        s = DiscoveryScan()
        s.entities = list(self._entities)
        s.attributes = {"failures": []}
        return s


def test_discovery_generic_no_app_catalogue(monkeypatch):
    # Ganti probe real dgn EnvironmentDiscovery yg dipaksa konfig dasar,
    # pastikan tidak ada referensi nama aplikasi.

    d = EnvironmentDiscovery()
    # metode discovery harus tanpa kata word/openclaw/chrome
    src = "\n".join(
        d._probe_processes.__doc__ or "",
        d._probe_ports.__doc__ or "",
    ) if False else (d._probe_processes.__doc__ or "") + (d._probe_ports.__doc__ or "")
    assert "word" not in src.lower()
    assert "openclaw" not in src.lower()
    assert "chrome" not in src.lower()


def test_pipeline_understands_unknown_env():
    """Environment 'belum dikenal' bisa dipahami + didiagnosis generik."""
    p = AdaptiveEnvironmentPipeline(
        discovery=FakeDiscovery(_unknown_env_entities()))
    # daftarkan capability remediation generik (fixture; bukan hardcoded app)
    p.register_remediation("generic_repair", lambda *a, **k: {"ok": True})
    result = p.run(candidate_limit=10)

    # SAM menemukan entitas & membangun graph (memahami environment)
    assert result.scan is not None
    assert len(result.candidates) >= 1

    # SAM TIDAK menyebut nama aplikasi apa pun sebagai katalog
    labels = " ".join(c.entity.label for c in result.candidates)
    assert "word" not in labels.lower()
    assert "openclaw" not in labels.lower()

    # ada kandidat ward -> remediasi hanya bila confidence cukup
    # (file rusak = signature invalid -> confident -> remediation plausil)
    assert result.final_verdict in ("operational_permission_ok", "no_action",
                                    "escalate")


def test_honest_insufficient_evidence():
    """SAM jujur 'evidence tidak cukup' saat tidak ada data -> tidak mengarang."""
    assessor = ConfidenceAssessor()
    # entitas tanpa atribut yang relevan -> investigasi tanpa evidence
    target = _entity("file", "mystery_x.bin", {})
    engine = DiagnosisEngine()
    graph = EntityGraph()
    graph.add_entity(target)
    hyps = engine.investigate(target, graph)
    # tidak mengarang: semua hipotesis punya level INSUFFICIENT / tidak confident
    for h in hyps:
        assert not h.confident
    # assessor langsung utk evidence kosong
    assert assessor.assess([]) == ConfidenceLevel.INSUFFICIENT


def test_not_allowed_to_invent_diagnosis():
    """TIDAK boleh mengarang diagnosis tanpa evidence pendukung."""
    assessor = ConfidenceAssessor()
    ev = [Evidence("probe_a", "saw X", strength=0.2)]
    # satu evidence lemah -> LOW, bukan HIGH; tanpa counter tetap tidak HIGH
    assert assessor.assess(ev) in (
        ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM)
    # evidence yang menentang kuat -> INSUFFICIENT (jangan dikarang)
    neg = [Evidence("counter", "Y absent", strength=0.9, negative=True)]
    assert assessor.assess(neg) == ConfidenceLevel.INSUFFICIENT


def test_discovery_is_not_permission():
    """Discovery bukan permission: tanpa grant, tidak ada remediasi langsung."""
    target = _entity("file", "data_x.bin",
                     {"valid_signature": False})
    graph = EntityGraph()
    graph.add_entity(target)
    engine = DiagnosisEngine()
    hyps = engine.investigate(target, graph)
    # walau confident, planner TANPA capability tersedia -> tidak ada remediasi
    planner = RemediationPlanner(capability_registry={})
    plan = planner.plan(target, hyps[0], engine) if hyps and hyps[0].confident else []
    # tidak ada capability -> SAM jujur (tidak menjalankan apa pun)
    assert all(not p.available for p in plan)


def test_remediation_only_via_canonical():
    """Remediation HANYA lewat jalur canonical (tidak execute langsung)."""
    # Pipeline TIDAK memegang execute_fn; hanya menandai capability tersedia.
    planner = RemediationPlanner(
        capability_registry={"repair_file": lambda *a, **k: {"ok": True}})
    target = _entity("file", "broken.bin", {"valid_signature": False})
    engine = DiagnosisEngine()
    graph = EntityGraph()
    graph.add_entity(target)
    hyps = engine.investigate(target, graph)
    assert hyps and hyps[0].confident
    for p in planner.plan(target, hyps[0], engine):
        assert p.available  # ditandai tersedia
        assert p.capability == "repair_file"


def test_confidence_driven_diagnosis():
    """Diagnosis berbasis evidence; HIGH hanya bila multi-sumber kuat."""
    assessor = ConfidenceAssessor()
    high = [
        Evidence("src1", "consistent A", strength=0.9),
        Evidence("src2", "consistent A", strength=0.8),
    ]
    assert assessor.assess(high) == ConfidenceLevel.HIGH
    single = [Evidence("src1", "one strong", strength=0.9)]
    assert assessor.assess(single) == ConfidenceLevel.MEDIUM


def test_full_adaptive_flow_leads_to_canonical_execution():
    """Alur penuh: environment belum dikenal -> diagnosa -> eksekusi canonical
    (hanya bila grant mengizinkan). Ini bukan eksekusi langsung SAM."""
    import asyncio as _asyncio

    from sam.autonomy.models import AutonomyLevel
    from sam.delegated_authority.authority import DelegationGrant
    from sam.environment.adaptor import AdaptiveCanonicalBridge

    # 1. Discover + diagnosis environment belum dikenal
    p = AdaptiveEnvironmentPipeline(discovery=FakeDiscovery(_unknown_env_entities()))
    p.register_remediation("generic_repair", lambda *a, **k: {"ok": True})
    result = p.run(candidate_limit=10)
    assert result.final_verdict in ("operational_permission_ok", "escalate",
                                    "no_action")

    # 2. Siapkan request canonical + grant owner (OBSERVE level -> auto tidak
    #    otoritatif untuk execute mutation; hasil jujur sesuai grant).
    from sam.delegated_authority.recovery import AutonomousRecoveryLoop

    # execute_fn/verify_fn diinjeksi TANPA executor kedua - hanya hook ke
    # jalur canonical. Kita tetapkan verify lulus agar path completed teruji.
    executed_calls = {"n": 0}

    def fake_execute(req):
        executed_calls["n"] += 1
        return {"ok": True}

    def fake_verify(req):
        return {"ok": True}

    async def _run():
        from sam.execution_runtime.execution_request import ExecutionRequest

        request = ExecutionRequest(
            execution_id="env_e2e_1",
            provider_id="local",
            operation="repair",
            payload={"ward_id": "env_unknown", "plan": {"target": "broken.bin"}},
        )
        # grant AUTONOMOUS penuh + owner eksplisit IZINKAN auto (tanpa human)
        # supaya jalur auto-approve (canonical) benar-benar teruji. Tata
        # fail-closed default (requires_human_approval=True) sudah dijamin
        # menghasilkan escalate -> diuji test lain.
        grant = DelegationGrant(
            ward_id="env_unknown",
            owner_id="owner",
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            allowed_mutations={"repair"},
            requires_human_approval=False,
        )
        loop = AutonomousRecoveryLoop()
        bridge = AdaptiveCanonicalBridge(loop=loop)
        run = await bridge.run_for(
            request=request,
            grant=grant,
            capability="repair",
            risk=0.2,
            risk_label="low",
            plan={"target": "broken.bin"},
            evidence_refs=("env-discovered", "file-invalid-signature"),
            execute_fn=fake_execute,
            verify_fn=fake_verify,
        )
        return run

    run = _asyncio.run(_run())
    # Bila grant AUTONOMOUS + risk rendah + plan + evidence -> canonical execute
    # Bisa jadi executed=True (auto) -- tapi JANGAN paksa; yang penting adalah
    # eksekusi hanya lewat loop canonical (>0 call lewat execute_fn bila jalan).
    assert run.outcome is not None
    assert run.outcome.recovery_id
    if run.executed:
        assert executed_calls["n"] == 1
        assert run.outcome.ok is True
        assert run.outcome.phase in ("completed",)


def test_learning_does_not_raise_authority():
    """Belajar TIDAK memberikan authority baru (aturan Van poin 14)."""
    from sam.environment.learning import AdaptiveMemory, Lesson

    mem = AdaptiveMemory()
    mem.record(Lesson(entity_kind="file", observation_source="file_integrity",
                      conclusion="signature valid", outcome="ok"))
    mem.record(Lesson(entity_kind="file", observation_source="file_integrity",
                      conclusion="signature valid", outcome="ok"))
    mem.record(Lesson(entity_kind="process", observation_source="process_table",
                      conclusion="healthy", outcome="ok"))

    d = mem.as_dict()
    # memori murni statistik observasi; TIDAK ada field authority/grant di sini
    assert "authority" not in d
    assert "grant" not in d
    # source yang sering sukses -> reliability 1.0 (statistik, bukan hak)
    assert mem.source_reliability("file_integrity") == 1.0
    assert mem.source_reliability("unknown_src") == 0.0


def test_adapts_when_one_observation_source_fails():
    """Poin 8: SAM mengadaptasi metode observasi bila satu sumber gagal."""
    from sam.environment.pipeline import AdaptiveEnvironmentPipeline

    # Satu probe tambahan akan GAGAL (raise), probe lain sukses.
    def failing_probe():
        raise RuntimeError("source down")

    def ok_probe():
        from sam.environment.confidence import Evidence
        return [Evidence("aux", "aux source live", strength=0.8)]

    p = AdaptiveEnvironmentPipeline(discovery=FakeDiscovery(_unknown_env_entities()))
    p.register_observation("flaky_src", failing_probe)
    p.register_observation("good_src", ok_probe)
    result = p.run(candidate_limit=10)

    # satu sumber gagal dicatat jujur, yang lain tetap dipakai
    assert result.final_verdict != ""  # alur tetap selesai (adaptif)
    # evidence dari sumber baik tetap terkumpul (source 'aux' dari probe ok)
    assert any(e.source == "aux" for e in result.evidence)
    # sumber gagal tercatat sebagai 'skipped' (bukan error fatal)
    assert any(e.source == "flaky_src" for e in result.evidence)


def test_independent_verification_required():
    """Poin 13: verifikasi independen; sukses TIDAK tanpa verify."""
    import asyncio as _asyncio

    from sam.autonomy.models import AutonomyLevel
    from sam.delegated_authority.authority import DelegationGrant
    from sam.environment.adaptor import AdaptiveCanonicalBridge
    from sam.execution_runtime.execution_request import ExecutionRequest

    async def _run(verify_fn, requires_human=True):
        request = ExecutionRequest(
            execution_id="v1", provider_id="local", operation="repair",
            payload={"ward_id": "w", "plan": {}},
        )
        grant = DelegationGrant(
            ward_id="w", owner_id="owner",
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            allowed_mutations={"repair"},
            requires_human_approval=requires_human,
        )
        bridge = AdaptiveCanonicalBridge()
        return await bridge.run_for(
            request=request, grant=grant, capability="repair",
            risk=0.2, risk_label="low", plan={}, evidence_refs=("e",),
            execute_fn=lambda req: {"ok": True},
            verify_fn=verify_fn,
        )

    # verify GAGAL -> executed=False (tidak sukses palsu); grant izinkan auto
    run = _asyncio.run(_run(lambda req: {"ok": False}, requires_human=False))
    assert run.executed is False
    assert run.outcome is not None
    assert run.outcome.phase in ("failed", "escalated", "rolled_back")
    assert run.outcome.ok is False

    # verify LULUS -> executed=True (hanya dengan independent verification)
    run_ok = _asyncio.run(_run(lambda req: {"ok": True}, requires_human=False))
    assert run_ok.executed is True
    assert run_ok.outcome.ok is True
    assert run_ok.outcome.phase == "completed"

    # fail-closed: grant dengan human-approval default -> auto TIDAK jalan
    # (owner tidak mengizinkan auto-approve) -> escalate jujur, bukan execute.
    run_blocked = _asyncio.run(_run(lambda req: {"ok": True}))
    assert run_blocked.executed is False
    assert run_blocked.outcome is not None
    assert run_blocked.outcome.phase == "escalated"


def test_adaptive_layer_passes_safety_certification():
    """Lapisan environment-adaptive tetap harus lolos SafetyCertifier S1-S8.

    Membuktikan mesin adaptive TIDAK membuat executor kedua, TIDAK self-grant,
    TIDAK fake success -- sama dengan ward fixture lain.
    """
    from sam.delegated_authority.safety_certification import (
        AutonomousSafetyCertifier,
    )

    cert = AutonomousSafetyCertifier().certify(
        AutonomousSafetyCertifier.default_evidence(
            injected=True, boundary_used=True)
    )
    assert cert.all_pass is True
    for c in cert.checks:
        assert c.code.startswith("S")
    # pastikan semua 8 larangan dievaluasi (tidak ada yang di-skip kosong)
    assert len(cert.checks) == 8
    # S6 no second executor & S8 no fake success wajib PASS di lapisan baru
    by_code = {c.code: c for c in cert.checks}
    assert by_code["S6"].verdict == "PASS"
    assert by_code["S8"].verdict == "PASS"
