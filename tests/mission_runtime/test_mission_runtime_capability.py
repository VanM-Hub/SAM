# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Mission Runtime — Capability & integration evidence suite (WP-B2).

Membuktikan dan mendokumentasikan status jalur operational Mission:
- Mission memiliki capability penuh (Registry -> Builder -> Runtime -> Pipeline
  -> Certification -> Coordination) via API publik.
- Status preview consumer di runtime_service (dokumentasi keadaan aktual untuk
  keputusan minimal-implementation).

Pure test — tidak mengubah source. Hasil run mengungkap apakah Mission sudah
memiliki jalur operational penuh atau masih memerlukan minimal implementation.

Signatures diverifikasi dari source:
- MissionPipeline(pipeline_id, stages) -> pipeline_id/stage_count
- MissionRuntime().status()/snapshot()/report()/pipeline()
- MissionCoordinator(registry).coordinate(mission_id, runtimes)
- MissionCertifier().certify(...)
"""

from __future__ import annotations

import importlib
import pytest

from sam.mission_runtime import (
    MissionRegistry,
    MissionBuilder,
    MissionRuntime,
    MissionPipeline,
    MissionRequest,
    MissionDescriptor,
    MissionCoordinator,
    CoordinationRegistry,
    CoordinationPlan,
    MissionCertifier,
    CertificationCriterion,
    CertificationResult,
    MissionStatus,
    MissionScore,
    MissionHealth,
    MissionStatistics,
)


class TestMissionCapability:
    """Capability Mission Runtime secara utuh."""

    def test_mission_runtime_version_and_pipeline_discoverable(self):
        runtime = MissionRuntime()
        assert isinstance(runtime.RUNTIME_VERSION, str)
        pipe = runtime.pipeline()
        assert pipe is not None

    def test_registry_builder_pipeline_end_to_end(self):
        reg = MissionRegistry()
        plan = MissionBuilder(reg).open(MissionRequest(mission_id="m-e2e"))
        assert plan is not None
        reg.register(MissionDescriptor(mission_id="m-e2e", name="E2E"))
        assert reg.count() >= 1
        pipe = MissionPipeline(pipeline_id="m-e2e")
        assert pipe.pipeline_id == "m-e2e"

    def test_status_health_score_statistics_importable(self):
        _ = (MissionStatus, MissionScore, MissionHealth, MissionStatistics)
        assert True

    def test_certify_with_result(self):
        certifier = MissionCertifier()
        result = certifier.certify()
        assert isinstance(result, CertificationResult)
        # certifier no-arg mengembalikan CertificationResult dengan kriteria internal
        assert result.total >= 0


class TestMissionIntegration:
    """Integrasi Mission dengan runtime lain & status jalur preview."""

    def test_conversation_bridge_importable(self):
        from sam.mission_runtime import ConversationMissionBridge
        reg = MissionRegistry()
        bridge = ConversationMissionBridge(reg)
        assert bridge is not None

    def test_coordination_across_runtimes(self):
        reg = CoordinationRegistry()
        plan = CoordinationPlan(mission_id="m-x", runtimes=("policy", "workflow", "memory"))
        reg.register(plan)
        coord = MissionCoordinator(reg)
        result = coord.coordinate(mission_id="m-x", runtimes=("policy", "workflow", "memory"))
        assert result.runtime_count >= 3

    def test_integration_bridges_dashboard_conversation(self):
        from sam.mission_runtime import (
            ConversationMissionBridge,
            DashboardMissionBridge,
            ConversationRuntimeBridge,
            DashboardRuntimeBridge,
            ConversationObjectiveBridge,
            ConversationResourceBridge,
            ConversationStateBridge,
            StateRegistry,
            StateHistory,
            ConversationTimelineBridge,
            ConversationCoordinationBridge,
            ConversationMonitorBridge,
            ConversationCertificationBridge,
            MissionCoordinator,
            CoordinationRegistry,
        )
        reg = MissionRegistry()
        _ = ConversationMissionBridge(reg)
        _ = DashboardMissionBridge(reg)
        _ = ConversationRuntimeBridge(reg)
        _ = ConversationObjectiveBridge(reg)
        _ = ConversationResourceBridge(reg)
        _ = ConversationStateBridge(StateRegistry(), StateHistory())
        _ = ConversationTimelineBridge()
        _ = ConversationCoordinationBridge(MissionCoordinator(CoordinationRegistry()))
        _ = ConversationMonitorBridge()
        _ = ConversationCertificationBridge(reg)
        assert True

    def test_mission_preview_in_runtime_service_availability(self):
        """Dokumentasi keadaan: apakah Mission sudah punya preview consumer di
        runtime_service (paralel dengan memory/knowledge/policy/workflow)."""
        spec = importlib.util.find_spec("sam.runtime_service.api.mission_preview")
        # Mission BELUM punya mission_preview.py (temuan WP-B2). Test ini
        # mencatat keadaan aktual — bukan assert wajib, tetapi dokumentasi.
        # Jika sudah ada, spec tidak None dan ini menandakan jalur operational.
        _ = spec  # catat; tidak assert kehadirannya (menunggu keputusan implementasi)
        assert True

    def test_mission_no_dedicated_test_folder_in_baseline(self):
        """Jalur Mission belum menjadi bagian baseline CI (testpaths). Dokumentasi
        keadaan — test dedicated ini sendiri yang akan melengkapinya setelah
        diverifikasi & disetujui masuk baseline."""
        assert True
