"""
Integration tests — Intelligence Pipeline End-to-End (Phase 1)
"""

import pytest
import json
from sam.intelligence.models import Incident, IncidentSeverity
from sam.intelligence.detector import IncidentDetector
from sam.intelligence.rca import RootCauseAnalyzer
from sam.intelligence.recommender import Recommender
from sam.intelligence.knowledge import KnowledgeLookup


class TestIntelligencePipelineE2E:
    @pytest.mark.asyncio
    async def test_full_pipeline(self, tmp_path):
        """Pipeline lengkap: detect -> rca -> recommend."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "openclaw.log").write_text(
            "[2026-07-27 10:00:00] ERROR Worker timeout after 30s\n"
        )

        detector = IncidentDetector(str(tmp_path))
        incidents = await detector.detect()
        assert len(incidents) >= 1

        incident = incidents[0]
        analyzer = RootCauseAnalyzer()
        causes = await analyzer.analyze(incident)
        assert len(causes) >= 1

        recommender = Recommender()
        recommendations = await recommender.recommend(incident, causes)
        assert len(recommendations) >= 1

    @pytest.mark.asyncio
    async def test_log_and_health_detection(self, tmp_path):
        """Deteksi dari log dan health.json."""
        (tmp_path / "logs").mkdir()
        (tmp_path / "logs" / "openclaw.log").write_text("[2026-07-27 10:00:00] ERROR crash\n")

        dot_dir = tmp_path / ".openclaw"
        dot_dir.mkdir()
        (dot_dir / "health.json").write_text(json.dumps({
            "components": [{"name": "Worker", "status": "unhealthy", "message": "Not responding"}],
        }))

        detector = IncidentDetector(str(tmp_path))
        incidents = await detector.detect()
        assert len(incidents) >= 2
        sources = [i.source for i in incidents]
        assert "openclaw.health" in sources

    @pytest.mark.asyncio
    async def test_knowledge_database(self):
        """Knowledge search harus return database-related entry."""
        lookup = KnowledgeLookup()
        results = await lookup.search("database connection failure")
        assert len(results) >= 1
        all_text = " ".join(r.get("fact", "") for r in results).lower()
        assert any(word in all_text for word in ["database", "connection", "pool"])

    @pytest.mark.asyncio
    async def test_multi_cause(self):
        """Insiden dengan multiple keywords harus return multiple causes."""
        incident = Incident(id="multi", title="Worker provider runtime error",
                            description="Worker crashed due to provider auth and memory issues",
                            severity=IncidentSeverity.CRITICAL)
        analyzer = RootCauseAnalyzer()
        causes = await analyzer.analyze(incident)
        assert len(causes) >= 2

    @pytest.mark.asyncio
    async def test_steps_not_empty(self):
        """Setiap rekomendasi harus memiliki steps."""
        incident = Incident(id="steps", title="Gateway down")
        analyzer = RootCauseAnalyzer()
        recommender = Recommender()
        causes = await analyzer.analyze(incident)
        recs = await recommender.recommend(incident, causes)
        for rec in recs:
            assert len(rec.steps) > 0

    @pytest.mark.asyncio
    async def test_no_log_fallback(self, tmp_path):
        """Workspace tanpa log harus tetap bisa detect."""
        detector = IncidentDetector(str(tmp_path))
        incidents = await detector.detect()
        assert isinstance(incidents, list)


class TestIntelligenceIntegration:
    def test_cli_import(self):
        from sam.cli.intelligence import app
        assert len(app.registered_commands) >= 3

    def test_coordinator_has_intelligence(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        assert hasattr(coord, "incident_detector")
        assert hasattr(coord, "rca_analyzer")
        assert hasattr(coord, "recommender")
        assert hasattr(coord, "knowledge_lookup")
