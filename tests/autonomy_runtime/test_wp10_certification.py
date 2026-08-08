# IP-3.2-001 WP-10 - End-to-end Integration & Certification test
# Runtime Observation & Diagnostics (AO-3.2-001 / ED-3.2-001)
#
# Definisi Done IP-3.2-001: Runtime mampu menjawab secara deterministik:
#   keadaan saat ini, dependency aktif, health, readiness, penyebab kegagalan,
#   bottleneck, rekomendasi observasional - TANPA mengubah runtime apa pun.

from pathlib import Path

import pytest
from sam.autonomy_runtime.observation.engine import ObservationEngine
from sam.autonomy_runtime.observation.dependency import DependencyGraph
from sam.autonomy_runtime.diagnostics.engine import DiagnosticsEngine
from sam.autonomy_runtime.diagnostics.failure import FailureClassifier
from sam.autonomy_runtime.readiness.analyzer import ReadinessAnalyzer
from sam.autonomy_runtime.api.observation import RuntimeObservationAPI
from sam.autonomy_runtime.compliance.checker import compliance_check, default_source_files


def _healthy_engine() -> ObservationEngine:
    eng = ObservationEngine()
    eng.register("kernel", lambda n: {"kind": "kernel", "status": "ok", "ready": True})
    eng.register("provider", lambda n: {
        "kind": "provider", "status": "ok", "ready": True,
        "dependencies": ["kernel"],
    })
    eng.register("gateway", lambda n: {
        "kind": "gateway", "status": "ok", "ready": True,
        "dependencies": ["provider"],
    })
    return eng


def _failing_engine() -> ObservationEngine:
    eng = ObservationEngine()
    eng.register("kernel", lambda n: {"kind": "kernel", "status": "ok", "ready": True})
    eng.register("provider", lambda n: {
        "kind": "provider", "status": "error", "ready": False,
        "detail": "connection timeout to upstream", "dependencies": ["kernel"],
    })
    eng.register("gateway", lambda n: {
        "kind": "gateway", "status": "error", "ready": False,
        "dependencies": ["provider"],
    })
    return eng


def _graph() -> DependencyGraph:
    g = DependencyGraph()
    g.add("gateway", {"provider"})
    g.add("provider", {"kernel"})
    return g


def _api(eng: ObservationEngine) -> RuntimeObservationAPI:
    g = _graph()
    return RuntimeObservationAPI(
        eng,
        diagnostics=DiagnosticsEngine(dependency_graph=g),
        failure=FailureClassifier(dependency_graph=g),
        readiness=ReadinessAnalyzer(dependency_graph=g),
    )


def test_state_self_description_deterministic():
    """Runtime mampu menjawab keadaan dirinya saat ini secara deterministik."""
    eng = _healthy_engine()
    s1 = eng.observe(timestamp="2026-08-09T00:00:00Z")
    s2 = eng.observe(timestamp="2026-08-09T00:00:00Z")
    assert s1.status == "ok"
    assert s1.state_id == s2.state_id
    assert eng.snapshot(s1).checksum == eng.snapshot(s2).checksum
    assert len(s1.components) == 3


def test_dependency_graph_active():
    """Runtime mengetahui dependency aktif (query graph read-only)."""
    g = _graph()
    assert g.dependencies_of("gateway") == ["provider"]
    assert g.transitive_dependencies("gateway") == {"provider", "kernel"}
    assert g.has_cycle() is False


def test_health_report():
    """Runtime menilai health-nya secara deterministik."""
    api = _api(_healthy_engine())
    h = api.get_health()
    assert h.overall == "healthy"
    assert h.score == 100


def test_readiness_assessment():
    """Runtime menilai readiness-nya."""
    api = _api(_healthy_engine())
    r = api.get_readiness()
    assert r.ready is True
    assert r.level == "ready"


def test_failure_classification():
    """Runtime mengidentifikasi penyebab kegagalan."""
    api = _api(_failing_engine())
    cls = api.get_classification()
    assert cls.class_of("provider") == "connectivity_failure"
    assert cls.class_of("gateway") == "dependency_failure"
    assert "provider" in cls.failed_components()


def test_diagnostics_bottleneck_and_root():
    """Runtime menemukan bottleneck utama & akar penyebab."""
    api = _api(_failing_engine())
    diag = api.get_diagnostics()
    assert diag.overall == "unhealthy"
    assert "provider" in diag.root_candidates  # akar: provider error berdiri sendiri
    assert "gateway" not in diag.root_candidates  # gateway error karena provider
    assert diag.bottleneck_candidates  # ada bottleneck terdeteksi
    assert all(r.kind.startswith("inspect_") for r in diag.recommendations)


def test_observational_recommendations_no_action():
    """Rekomendasi murni observasional - tidak ada rekomendasi yang memicu aksi."""
    api = _api(_failing_engine())
    diag = api.get_diagnostics()
    assert all(not r.kind.startswith(("restart", "recover", "schedule"))
               for r in diag.recommendations)


def test_read_only_no_runtime_mutation():
    """Seluruh operasi observasi tidak mengubah state runtime apa pun."""
    eng = _failing_engine()
    api = _api(eng)
    before = eng.snapshot(eng.observe()).checksum
    api.get_summary()
    api.get_health()
    api.get_diagnostics()
    api.get_classification()
    api.get_readiness()
    after = eng.snapshot(eng.observe()).checksum
    assert before == after  # observasi tidak memutasi apa pun


def test_compliance_suite_passed():
    """Compliance suite IP-3.2-001 lulus (Autonomy without Authority)."""
    pkg = Path("src/sam/autonomy_runtime").resolve()
    passed, report = compliance_check(pkg, default_source_files(pkg))
    assert passed is True
    assert report["passed"] == report["total"] == 5


def test_summary_shape():
    """Summary observasi berisi seluruh artefak yang diharapkan."""
    api = _api(_healthy_engine())
    summ = api.get_summary()
    keys = set(summ.as_dict().keys())
    assert keys == {"state", "snapshot", "health", "diagnostics",
                    "classification", "readiness"}
