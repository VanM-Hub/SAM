"""
Hardening tests — Edge cases, graceful degradation, validation (Batch 11)
"""

import pytest
import json
import yaml
import os
from pathlib import Path


class TestMissionValidation:
    def test_valid_mission_yaml(self):
        """mission.yaml yang valid harus bisa di-load."""
        from sam.mission.loader import MissionLoader
        loader = MissionLoader("workspace")
        mission = loader.load()
        assert mission is not None
        assert hasattr(mission, "id")

    def test_mission_file_not_found_returns_default(self, tmp_path):
        """Jika mission.yaml tidak ada, loader harus return default mission."""
        from sam.mission.loader import MissionLoader
        loader = MissionLoader(str(tmp_path))
        mission = loader.load()
        # Should return default (fallback) without crash
        assert mission is not None


class TestDOSValidation:
    def test_valid_dos_yaml(self):
        """desired-state.yaml yang valid harus bisa di-load."""
        from sam.dos.loader import DOSLoader
        loader = DOSLoader("workspace")
        dos = loader.load()
        assert dos is not None
        assert hasattr(dos, "runtime_state")

    def test_dos_file_not_found_returns_default(self, tmp_path):
        """Jika desired-state.yaml tidak ada, loader harus return default DOS."""
        from sam.dos.loader import DOSLoader
        loader = DOSLoader(str(tmp_path))
        dos = loader.load()
        assert dos is not None


class TestGracefulDegradation:
    @pytest.mark.asyncio
    async def test_coordinator_start_no_workspace(self, tmp_path):
        """Coordinator start tanpa workspace valid harus tidak crash."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator(workspace_path=str(tmp_path / "nonexistent"))
        state = await coord.start()
        # Should not crash — safe_mode or ready both acceptable
        assert state.value in ("ready", "safe_mode")

    @pytest.mark.asyncio
    async def test_coordinator_start_empty_workspace(self, tmp_path):
        """Coordinator di workspace kosong harus tetap bisa start."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator(workspace_path=str(tmp_path))
        state = await coord.start()
        # Should at least get to ready or safe_mode, not crash
        assert state.value in ("ready", "safe_mode")

    @pytest.mark.asyncio
    async def test_shutdown_doesnt_crash(self):
        """Shutdown dari state INITIALIZING harus graceful."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        # Stop without start — should not crash
        state = await coord.stop()
        assert state.value in ("shutdown", "initializing")

    @pytest.mark.asyncio
    async def test_run_from_wrong_state_raises_error(self):
        """Run dari INITIALIZING harus raise error (bukan crash)."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        with pytest.raises(RuntimeError):
            await coord.run()

    @pytest.mark.asyncio
    async def test_health_collector_no_workspace(self):
        """Health collector harus tidak crash dengan workspace tidak ada."""
        from sam.openclaw.health import OpenClawHealthCollector
        collector = OpenClawHealthCollector()
        health = await collector.collect("/nonexistent/path")
        assert health is not None
        assert health.components  # Should return simulated components


class TestErrorHandling:
    def test_telemetry_service_max_events(self):
        """Telemetry dengan max_events kecil harus tetap jalan."""
        from sam.telemetry.service import TelemetryService
        svc = TelemetryService(max_events=3)
        for i in range(10):
            svc.emit_event("test.{0}".format(i))
        assert len(svc._buffer) == 3

    @pytest.mark.asyncio
    async def test_incident_detector_bad_workspace(self, tmp_path):
        """Incident detector dengan workspace tidak ada harus tidak crash."""
        from sam.intelligence.detector import IncidentDetector
        bad_path = str(tmp_path / "does_not_exist_12345")
        detector = IncidentDetector(bad_path)
        incidents = await detector.detect()
        assert isinstance(incidents, list)

    def test_knowledge_search_empty(self):
        """Knowledge search dengan query kosong harus return default entries."""
        from sam.intelligence.knowledge import KnowledgeLookup
        lookup = KnowledgeLookup()
        results = asyncio.run(lookup.search(""))
        assert len(results) >= 1


class TestConfigurationValidation:
    def test_dos_loader_invalid_yaml(self, tmp_path):
        """DOS YAML yang corrupt harus tidak crash (return default)."""
        from sam.dos.loader import DOSLoader
        # Create invalid YAML
        (tmp_path / "desired-state.yaml").write_text("invalid: [yaml: broken")
        loader = DOSLoader(str(tmp_path))
        # Should not crash — return default
        dos = loader.load()
        assert dos is not None

    def test_mission_loader_invalid_yaml(self, tmp_path):
        """Mission YAML yang corrupt harus tidak crash."""
        from sam.mission.loader import MissionLoader
        (tmp_path / "mission.yaml").write_text("{{{broken")
        loader = MissionLoader(str(tmp_path))
        mission = loader.load()
        assert mission is not None

    def test_web_server_import(self):
        """Web server harus bisa di-import tanpa error."""
        from sam.web.server import app
        assert app is not None


class TestSecurityHardening:
    def test_web_default_host_localhost(self):
        """Web dashboard harus default ke 127.0.0.1."""
        from sam.web.server import run_server
        # Check that run_server defaults to localhost
        import inspect
        sig = inspect.signature(run_server)
        host_default = sig.parameters["host"].default
        assert host_default == "127.0.0.1"

    def test_coordinator_no_hardcoded_credentials(self):
        """Coordinator harus tidak memiliki hardcoded credentials."""
        from sam.runtime.coordinator import RuntimeCoordinator
        import inspect
        source = inspect.getsource(RuntimeCoordinator.__init__)
        suspicious = ["password", "secret", "token", "api_key", "apikey"]
        for word in suspicious:
            assert word not in source.lower(), "Hardcoded credential found: {0}".format(word)


# Need asyncio import
import asyncio
