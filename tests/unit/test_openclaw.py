"""
Unit tests — OpenClaw Integration (Phase 1)
"""

import pytest
from sam.openclaw.models import (
    OpenClawStatus, OpenClawComponent, OpenClawHealth, OpenClawWorkspace,
)
from sam.openclaw.discovery import OpenClawDiscovery
from sam.openclaw.health import OpenClawHealthCollector
from sam.openclaw.logs import OpenClawLogAnalyzer


class TestOpenClawModels:
    def test_status_enum(self):
        assert OpenClawStatus.HEALTHY.value == "healthy"
        assert OpenClawStatus.UNKNOWN.value == "unknown"

    def test_component_defaults(self):
        comp = OpenClawComponent(name="Gateway")
        assert comp.status == OpenClawStatus.UNKNOWN
        assert comp.message is None

    def test_component_custom(self):
        comp = OpenClawComponent(
            name="Worker",
            status=OpenClawStatus.HEALTHY,
            message="All running",
            details={"count": 3},
        )
        assert comp.name == "Worker"
        assert comp.details["count"] == 3

    def test_health_defaults(self):
        health = OpenClawHealth()
        assert health.runtime == OpenClawStatus.UNKNOWN
        assert health.components == []

    def test_health_custom(self):
        comp = OpenClawComponent(name="Test", status=OpenClawStatus.HEALTHY)
        health = OpenClawHealth(
            workspace="/test",
            runtime=OpenClawStatus.HEALTHY,
            components=[comp],
        )
        assert health.workspace == "/test"
        assert len(health.components) == 1

    def test_workspace_defaults(self):
        ws = OpenClawWorkspace(path="/tmp")
        assert ws.detected is False
        assert ws.version is None
        assert ws.health is None


class TestOpenClawDiscovery:
    @pytest.mark.asyncio
    async def test_discover_no_path(self):
        """Discovery tanpa path harus return list kosong atau hasil scan."""
        discovery = OpenClawDiscovery()
        results = await discovery.discover()
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_discover_nonexistent_path(self):
        """Discovery path yang tidak ada harus return list kosong."""
        discovery = OpenClawDiscovery("/nonexistent/path/xyz")
        results = await discovery.discover()
        found_nonexistent = any("nonexistent" in ws.path for ws in results)
        assert not found_nonexistent

    @pytest.mark.asyncio
    async def test_scan_empty_directory(self, tmp_path):
        """Scan direktori kosong harus return None."""
        discovery = OpenClawDiscovery()
        result = await discovery._scan_directory(tmp_path)
        assert result is None

    @pytest.mark.asyncio
    async def test_scan_with_openclaw_json(self, tmp_path):
        """Scan direktori dengan openclaw.json harus return workspace."""
        config = {"version": "0.1.0", "name": "test"}
        config_file = tmp_path / "openclaw.json"
        config_file.write_text(json.dumps(config))

        discovery = OpenClawDiscovery()
        result = await discovery._scan_directory(tmp_path)
        assert result is not None
        assert result.detected is True
        assert result.version == "0.1.0"
        assert result.path == str(tmp_path)

    @pytest.mark.asyncio
    async def test_scan_with_dot_openclaw(self, tmp_path):
        """Scan dengan .openclaw/config.json."""
        config = {"version": "1.0.0"}
        dot_dir = tmp_path / ".openclaw"
        dot_dir.mkdir()
        config_file = dot_dir / "config.json"
        config_file.write_text(json.dumps(config))

        discovery = OpenClawDiscovery()
        result = await discovery._scan_directory(tmp_path)
        assert result is not None
        assert result.detected is True
        assert result.version == "1.0.0"


class TestOpenClawHealthCollector:
    @pytest.mark.asyncio
    async def test_collect_returns_health(self):
        """Collect harus return OpenClawHealth."""
        collector = OpenClawHealthCollector()
        health = await collector.collect("/test")
        assert isinstance(health, OpenClawHealth)
        assert health.workspace == "/test"

    @pytest.mark.asyncio
    async def test_collect_components_not_empty(self):
        """Collect harus memiliki komponen."""
        collector = OpenClawHealthCollector()
        health = await collector.collect("/test")
        assert len(health.components) > 0
        assert any(c.name == "Worker" for c in health.components)

    @pytest.mark.asyncio
    async def test_collect_healthy_status(self):
        """Semua komponen simulated harus healthy."""
        collector = OpenClawHealthCollector()
        health = await collector.collect("/test")
        assert health.runtime == OpenClawStatus.HEALTHY

    def test_determine_runtime_all_healthy(self):
        collector = OpenClawHealthCollector()
        components = [
            OpenClawComponent(name="A", status=OpenClawStatus.HEALTHY),
            OpenClawComponent(name="B", status=OpenClawStatus.HEALTHY),
        ]
        status = collector._determine_runtime_status(components)
        assert status == OpenClawStatus.HEALTHY

    def test_determine_runtime_with_unhealthy(self):
        collector = OpenClawHealthCollector()
        components = [
            OpenClawComponent(name="A", status=OpenClawStatus.HEALTHY),
            OpenClawComponent(name="B", status=OpenClawStatus.UNHEALTHY),
        ]
        status = collector._determine_runtime_status(components)
        assert status == OpenClawStatus.UNHEALTHY

    def test_determine_runtime_with_degraded(self):
        collector = OpenClawHealthCollector()
        components = [
            OpenClawComponent(name="A", status=OpenClawStatus.HEALTHY),
            OpenClawComponent(name="B", status=OpenClawStatus.DEGRADED),
        ]
        status = collector._determine_runtime_status(components)
        assert status == OpenClawStatus.DEGRADED

    def test_determine_runtime_empty(self):
        collector = OpenClawHealthCollector()
        status = collector._determine_runtime_status([])
        assert status == OpenClawStatus.UNKNOWN

    @pytest.mark.asyncio
    async def test_detect_issues_no_issues(self):
        collector = OpenClawHealthCollector()
        health = await collector.collect("/test")
        issues = await collector.detect_issues(health)
        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_detect_issues_with_issues(self):
        collector = OpenClawHealthCollector()
        health = OpenClawHealth(
            workspace="/test",
            runtime=OpenClawStatus.UNHEALTHY,
            components=[
                OpenClawComponent(name="Broken", status=OpenClawStatus.UNHEALTHY, message="Down"),
            ],
        )
        issues = await collector.detect_issues(health)
        assert len(issues) == 1
        assert "Broken" in issues[0]


class TestOpenClawLogAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_no_log_file(self, tmp_path):
        """Analyzer tanpa log file harus return info message."""
        analyzer = OpenClawLogAnalyzer(str(tmp_path))
        results = await analyzer.analyze()
        assert len(results) > 0
        assert results[0]["type"] == "info"

    @pytest.mark.asyncio
    async def test_parse_error_line(self, tmp_path):
        """Baris ERROR dalam log harus terdeteksi."""
        log_file = tmp_path / "openclaw.log"
        log_file.write_text("[2026-07-27 12:00:00] ERROR Connection refused\n")

        analyzer = OpenClawLogAnalyzer(str(tmp_path))
        results = await analyzer.analyze(lines=10)
        assert len(results) == 1
        assert results[0]["severity"] == "ERROR"

    @pytest.mark.asyncio
    async def test_parse_mixed_lines(self, tmp_path):
        """Campuran line INFO, WARNING, ERROR."""
        content = (
            "[2026-07-27 12:00:00] INFO Starting\n"
            "[2026-07-27 12:01:00] WARNING Disk space low\n"
            "[2026-07-27 12:02:00] ERROR Out of memory\n"
            "[2026-07-27 12:03:00] INFO Running\n"
        )
        log_file = tmp_path / "openclaw.log"
        log_file.write_text(content)

        analyzer = OpenClawLogAnalyzer(str(tmp_path))
        results = await analyzer.analyze(lines=10)
        assert len(results) == 2  # WARNING + ERROR
        severities = [r["severity"] for r in results]
        assert "WARNING" in severities
        assert "ERROR" in severities

    def test_detect_severity(self):
        analyzer = OpenClawLogAnalyzer()
        assert analyzer._detect_severity("ERROR: fail") == "ERROR"
        assert analyzer._detect_severity("WARNING: low") == "WARNING"
        assert analyzer._detect_severity("CRITICAL: dead") == "CRITICAL"
        assert analyzer._detect_severity("INFO: ok") is None
        assert analyzer._detect_severity("DEBUG: trace") is None

    def test_extract_timestamp(self):
        analyzer = OpenClawLogAnalyzer()
        line = "[2026-07-27 12:00:00] ERROR test"
        assert analyzer._extract_timestamp(line) == "2026-07-27 12:00:00"

    def test_extract_timestamp_none(self):
        analyzer = OpenClawLogAnalyzer()
        assert analyzer._extract_timestamp("no timestamp here") == ""


# Need json import for tests
import json
