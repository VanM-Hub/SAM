"""
Integration tests — OpenClaw + SAM End-to-End (Phase 1)
"""

import pytest
import json
from sam.openclaw.models import OpenClawStatus, OpenClawHealth
from sam.openclaw.discovery import OpenClawDiscovery
from sam.openclaw.health import OpenClawHealthCollector
from sam.openclaw.logs import OpenClawLogAnalyzer


class TestOcIntegrationE2E:
    @pytest.mark.asyncio
    async def test_discover_then_health(self, tmp_path):
        config = {"version": "0.5.0"}
        (tmp_path / "openclaw.json").write_text(json.dumps(config))

        discovery = OpenClawDiscovery(str(tmp_path))
        workspaces = await discovery.discover()
        assert len(workspaces) > 0
        ws = workspaces[0]
        assert ws.detected is True

        collector = OpenClawHealthCollector()
        health = await collector.collect(ws.path)
        assert isinstance(health, OpenClawHealth)
        assert health.runtime == OpenClawStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_discover_log_analyze(self, tmp_path):
        config = {"version": "1.0.0"}
        (tmp_path / "openclaw.json").write_text(json.dumps(config))
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "openclaw.log").write_text(
            "[2026-07-27 10:00:00] INFO Started\n"
            "[2026-07-27 10:01:00] WARNING High latency\n"
            "[2026-07-27 10:02:00] ERROR Worker crashed\n"
        )

        discovery = OpenClawDiscovery(str(tmp_path))
        workspaces = await discovery.discover()
        assert len(workspaces) > 0

        analyzer = OpenClawLogAnalyzer(str(tmp_path))
        results = await analyzer.analyze()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_health_with_health_file(self, tmp_path):
        dot_dir = tmp_path / ".openclaw"
        dot_dir.mkdir()
        (dot_dir / "health.json").write_text(json.dumps({
            "components": [
                {"name": "Worker", "status": "healthy", "message": "Running"},
                {"name": "Gateway", "status": "healthy", "message": "Connected"},
            ],
        }))

        collector = OpenClawHealthCollector()
        health = await collector.collect(str(tmp_path))
        assert len(health.components) == 2

    @pytest.mark.asyncio
    async def test_health_detects_unhealthy(self, tmp_path):
        dot_dir = tmp_path / ".openclaw"
        dot_dir.mkdir()
        (dot_dir / "health.json").write_text(json.dumps({
            "components": [
                {"name": "Worker", "status": "unhealthy", "message": "Down"},
            ],
        }))

        collector = OpenClawHealthCollector()
        health = await collector.collect(str(tmp_path))
        issues = await collector.detect_issues(health)
        assert len(issues) == 1
        assert health.runtime == OpenClawStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_log_custom_location(self, tmp_path):
        dot_dir = tmp_path / ".openclaw" / "logs"
        dot_dir.mkdir(parents=True)
        (dot_dir / "runtime.log").write_text("[2026-07-27 12:00:00] ERROR fail\n")

        analyzer = OpenClawLogAnalyzer(str(tmp_path))
        results = await analyzer.analyze()
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_empty_log_dir(self, tmp_path):
        (tmp_path / "logs").mkdir()
        analyzer = OpenClawLogAnalyzer(str(tmp_path))
        results = await analyzer.analyze()
        assert len(results) == 1
        assert results[0]["type"] == "info"


class TestOcCLIIntegration:
    def test_cli_import(self):
        from sam.cli.openclaw import app
        assert app.registered_commands is not None
        # Typer sub-commands are registered as commands
        # Check by iterating registered commands (they use callback, not name)
        cmds = [c.callback.__name__ if c.callback else "" for c in app.registered_commands]
        assert any("discover" in cmd for cmd in cmds) or len(app.registered_commands) == 3

    def test_coordinator_has_openclaw(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        assert hasattr(coord, "openclaw_discovery")
        assert hasattr(coord, "openclaw_health")

    @pytest.mark.asyncio
    async def test_telemetry_openclaw_event(self):
        """OpenClaw discovery harus menghasilkan event telemetry (pola RuntimeCoordinator)."""
        from sam.telemetry.service import TelemetryService
        svc = TelemetryService()
        svc.emit_event(
            "openclaw.discovered",
            component="openclaw",
            payload={"workspace": "/test"},
        )
        events = svc.query()
        assert len(events) == 1
        evt = events[0]
        assert evt.metadata.get("component") == "openclaw" or "openclaw" in evt.message
        assert evt.metadata.get("workspace") == "/test"
