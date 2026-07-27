"""
Unit tests — Intelligence (Phase 1 — Incident Detection, RCA, Recommender, Knowledge)
"""

import pytest
from sam.intelligence.models import (
    Incident, IncidentSeverity, RootCause, Recommendation,
)
from sam.intelligence.detector import IncidentDetector
from sam.intelligence.rca import RootCauseAnalyzer
from sam.intelligence.recommender import Recommender
from sam.intelligence.knowledge import KnowledgeLookup


class TestIntelligenceModels:
    def test_incident_defaults(self):
        inc = Incident(title="test")
        assert inc.status == "open"
        assert inc.severity == IncidentSeverity.MEDIUM
        assert len(inc.id) == 8

    def test_incident_custom(self):
        inc = Incident(
            id="inc-001",
            title="Critical failure",
            severity=IncidentSeverity.CRITICAL,
            source="openclaw",
        )
        assert inc.id == "inc-001"
        assert inc.severity == IncidentSeverity.CRITICAL

    def test_severity_enum(self):
        assert IncidentSeverity.CRITICAL.value == "critical"
        assert IncidentSeverity.LOW.value == "low"

    def test_root_cause_defaults(self):
        rc = RootCause(incident_id="inc-001", cause="Test cause")
        assert rc.confidence == 0.5
        assert rc.evidence == []

    def test_recommendation_defaults(self):
        rec = Recommendation(incident_id="inc-001", title="Fix it")
        assert rec.risk == "medium"
        assert len(rec.id) == 8

    def test_recommendation_custom(self):
        rec = Recommendation(
            incident_id="inc-001",
            title="Restart worker",
            confidence=0.85,
            risk="low",
            steps=["Step 1", "Step 2"],
        )
        assert rec.confidence == 0.85
        assert len(rec.steps) == 2


class TestIncidentDetector:
    @pytest.mark.asyncio
    async def test_detect_empty_workspace(self, tmp_path):
        """Detector di workspace tanpa log harus return empty atau minimal."""
        detector = IncidentDetector(str(tmp_path))
        incidents = await detector.detect()
        assert isinstance(incidents, list)

    @pytest.mark.asyncio
    async def test_detect_from_log_file(self, tmp_path):
        """Detector harus mendeteksi insiden dari file log."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "openclaw.log").write_text(
            "[2026-07-27 10:00:00] ERROR Worker crashed\n"
        )
        detector = IncidentDetector(str(tmp_path))
        incidents = await detector.detect()
        assert len(incidents) >= 1
        assert incidents[0].severity == IncidentSeverity.HIGH

    @pytest.mark.asyncio
    async def test_detect_critical_severity(self, tmp_path):
        """CRITICAL log harus menghasilkan CRITICAL incident."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "openclaw.log").write_text(
            "[2026-07-27 10:00:00] CRITICAL System failure\n"
        )
        detector = IncidentDetector(str(tmp_path))
        incidents = await detector.detect()
        assert len(incidents) >= 1
        assert incidents[0].severity == IncidentSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_detect_warning_is_medium(self, tmp_path):
        """WARNING log harus menghasilkan MEDIUM incident."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "openclaw.log").write_text(
            "[2026-07-27 10:00:00] WARNING Disk space low\n"
        )
        detector = IncidentDetector(str(tmp_path))
        incidents = await detector.detect()
        warning_incidents = [i for i in incidents if i.severity == IncidentSeverity.MEDIUM]
        assert len(warning_incidents) >= 1

    @pytest.mark.asyncio
    async def test_detect_unhealthy_component(self, tmp_path):
        """Unhealthy component harus terdeteksi."""
        dot_dir = tmp_path / ".openclaw"
        dot_dir.mkdir(parents=True)
        (dot_dir / "health.json").write_text(
            '{"components": [{"name": "Worker", "status": "unhealthy", "message": "Down"}]}'
        )
        detector = IncidentDetector(str(tmp_path))
        incidents = await detector.detect()
        health_incidents = [i for i in incidents if i.source == "openclaw.health"]
        assert len(health_incidents) >= 1

    def test_summarize_short(self):
        detector = IncidentDetector()
        assert detector._summarize("Short msg", 50) == "Short msg"

    def test_summarize_long(self):
        detector = IncidentDetector()
        long_msg = "A very long error message that should be truncated at a word boundary"
        summary = detector._summarize(long_msg, 30)
        assert len(summary) <= 33  # allow for ...
        assert summary.endswith("...")


class TestRootCauseAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_worker_incident(self):
        """Incident worker harus menghasilkan worker-related RCA."""
        incident = Incident(
            id="t001",
            title="Worker timeout detected",
            description="Worker connection refused after 30s",
            severity=IncidentSeverity.HIGH,
        )
        analyzer = RootCauseAnalyzer()
        causes = await analyzer.analyze(incident)
        assert len(causes) >= 1
        assert "worker" in causes[0].cause.lower()

    @pytest.mark.asyncio
    async def test_analyze_memory_incident(self):
        """Incident memory harus menghasilkan memory-related RCA."""
        incident = Incident(
            id="t002",
            title="Out of memory error",
            description="System running low on memory",
            severity=IncidentSeverity.CRITICAL,
        )
        analyzer = RootCauseAnalyzer()
        causes = await analyzer.analyze(incident)
        assert len(causes) >= 1
        assert "memory" in causes[0].cause.lower()

    @pytest.mark.asyncio
    async def test_analyze_provider_incident(self):
        """Incident provider harus menghasilkan provider-related RCA."""
        incident = Incident(
            id="t003",
            title="Provider authentication failed",
            severity=IncidentSeverity.HIGH,
        )
        analyzer = RootCauseAnalyzer()
        causes = await analyzer.analyze(incident)
        assert any("auth" in c.cause.lower() for c in causes)

    @pytest.mark.asyncio
    async def test_analyze_unknown_returns_fallback(self):
        """Incident tanpa pattern match harus return fallback."""
        incident = Incident(
            id="t004",
            title="Something completely unexpected",
        )
        analyzer = RootCauseAnalyzer()
        causes = await analyzer.analyze(incident)
        assert len(causes) >= 1
        assert causes[0].confidence < 0.5

    @pytest.mark.asyncio
    async def test_causes_sorted_by_confidence(self):
        """Root causes harus diurutkan oleh confidence descending."""
        incident = Incident(
            id="t005",
            title="Worker out of memory crash",
            severity=IncidentSeverity.CRITICAL,
        )
        analyzer = RootCauseAnalyzer()
        causes = await analyzer.analyze(incident)
        for i in range(len(causes) - 1):
            assert causes[i].confidence >= causes[i + 1].confidence


class TestRecommender:
    @pytest.mark.asyncio
    async def test_recommend_from_causes(self):
        """Recommender harus menghasilkan rekomendasi dari causes."""
        incident = Incident(id="r001", title="Worker crash")
        causes = [
            RootCause(
                incident_id="r001",
                cause="Worker resource exhaustion",
                confidence=0.8,
                recommendation="Restart worker",
            ),
        ]
        recommender = Recommender()
        recs = await recommender.recommend(incident, causes)
        assert len(recs) >= 1
        assert recs[0].confidence <= 0.8  # discounted

    @pytest.mark.asyncio
    async def test_recommend_fallback_no_causes(self):
        """Tanpa causes, recommender harus return fallback."""
        incident = Incident(id="r002", title="Unknown issue")
        recommender = Recommender()
        recs = await recommender.recommend(incident, [])
        assert len(recs) == 1
        assert recs[0].confidence == 0.4

    @pytest.mark.asyncio
    async def test_recommend_steps_template_restart(self):
        """Rekomendasi restart harus punya restart steps."""
        incident = Incident(id="r003", title="Worker down")
        causes = [
            RootCause(
                incident_id="r003",
                cause="Worker crashed",
                confidence=0.9,
                recommendation="Restart the worker component",
            ),
        ]
        recommender = Recommender()
        recs = await recommender.recommend(incident, causes)
        steps_text = " ".join(recs[0].steps).lower()
        assert "stop" in steps_text or "restart" in steps_text or "start" in steps_text

    @pytest.mark.asyncio
    async def test_recommend_sorted_by_confidence(self):
        incident = Incident(id="r004", title="Multi cause")
        causes = [
            RootCause(incident_id="r004", cause="Low confidence", confidence=0.3),
            RootCause(incident_id="r004", cause="High confidence", confidence=0.9),
        ]
        recommender = Recommender()
        recs = await recommender.recommend(incident, causes)
        assert recs[0].confidence >= recs[-1].confidence

    def test_determine_risk(self):
        recommender = Recommender()
        assert recommender._determine_risk(IncidentSeverity.CRITICAL) == "high"
        assert recommender._determine_risk(IncidentSeverity.MEDIUM) == "medium"
        assert recommender._determine_risk(IncidentSeverity.LOW) == "low"


class TestKnowledgeLookup:
    @pytest.mark.asyncio
    async def test_search_worker(self):
        """Worker keyword harus return knowledge terkait worker."""
        lookup = KnowledgeLookup()
        results = await lookup.search("worker timeout")
        assert len(results) >= 1
        assert any("worker" in r.get("fact", "").lower() for r in results)

    @pytest.mark.asyncio
    async def test_search_provider(self):
        """Provider keyword harus return knowledge terkait provider."""
        lookup = KnowledgeLookup()
        results = await lookup.search("provider auth failure")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_no_match_returns_default(self):
        """Query tanpa match harus return default top entries."""
        lookup = KnowledgeLookup()
        results = await lookup.search("xyznonexistentkeyword123")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_respects_max_results(self):
        lookup = KnowledgeLookup()
        results = await lookup.search("worker", max_results=2)
        assert len(results) <= 2

    async def test_search_empty_query(self):
        lookup = KnowledgeLookup()
        results = await lookup.search("")
        assert len(results) >= 1
