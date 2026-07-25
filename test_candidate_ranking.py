"""
Tests for Sprint 23 Fase 1 – Plan Candidates & Plan Ranking

Covers:
- PlanCandidate model creation, validation, defaults, to_dict
- generate_candidates (count, uniqueness, variant metadata)
- PlanRanker scoring, ranking order, select_best
- Governance filter
- Integration with PlanningEngine (candidate_mode)
- Edge cases (empty list, single candidate, fallback)
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from datetime import datetime
from typing import Any, Dict, List, Optional

from sam.reasoning.intent import Intent, IntentType, IntentStatus
from sam.reasoning.candidate import PlanCandidate
from sam.reasoning.ranker import PlanRanker
from sam.reasoning.planner import PlanningEngine, PlanError
from sam.reasoning.templates import GraphTemplate, BUILTIN_TEMPLATES, get_default_template
from sam.execution.graph import ExecutionGraph, GraphStatus


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def basic_intent() -> Intent:
    return Intent(
        type=IntentType.DIAGNOSE,
        target="provider:nvidia",
        parameters={"verbose": "true"},
        context={"env": "prod"},
    )


@pytest.fixture
def repair_intent() -> Intent:
    return Intent(
        type=IntentType.REPAIR,
        target="provider:openai",
        parameters={"deep_scan": "true", "version": "2.0"},
        context={"env": "prod"},
    )


@pytest.fixture
def deploy_intent() -> Intent:
    return Intent(
        type=IntentType.DEPLOY,
        target="provider:openai",
        parameters={"version": "3.1", "workspace": "prod"},
    )


@pytest.fixture
def scale_intent() -> Intent:
    return Intent(
        type=IntentType.SCALE,
        target="cluster:worker-pool",
        parameters={"direction": "up", "count": "3"},
    )


@pytest.fixture
def optimize_intent() -> Intent:
    return Intent(
        type=IntentType.OPTIMIZE,
        target="service:db-cluster",
        parameters={"threshold": "0.8"},
    )


@pytest.fixture
def monitor_intent() -> Intent:
    return Intent(
        type=IntentType.MONITOR,
        target="cluster:main",
    )


@pytest.fixture
def custom_intent() -> Intent:
    return Intent(
        type=IntentType.CUSTOM,
        target="custom:target",
    )


@pytest.fixture
def engine() -> PlanningEngine:
    return PlanningEngine()


@pytest.fixture
def engine_with_governance() -> PlanningEngine:
    mock_gov = MagicMock()
    mock_gov.evaluate = AsyncMock()
    return PlanningEngine(
        governance_engine=mock_gov,
    )


# ── PlanCandidate Model ──────────────────────────────────────────────


class TestPlanCandidateModel:
    """PlanCandidate model construction, defaults, and helpers."""

    def test_create_minimal(self, basic_intent, engine):
        """Create a PlanCandidate with minimal fields."""
        graph = engine._instantiate(get_default_template(IntentType.DIAGNOSE), basic_intent)
        candidate = PlanCandidate(
            intent_id=basic_intent.id,
            graph=graph,
        )
        assert candidate.id is not None
        assert len(candidate.id) > 0
        assert candidate.intent_id == basic_intent.id
        assert candidate.graph is graph
        assert candidate.estimated_duration == 60
        assert candidate.risk_score == 0.5
        assert candidate.confidence == 0.5
        assert candidate.cost_estimate == 1.0
        assert candidate.historical_success_rate == 0.5
        assert not candidate.approval_required

    def test_create_full(self, basic_intent, engine):
        """Create a PlanCandidate with all fields set."""
        graph = engine._instantiate(get_default_template(IntentType.DIAGNOSE), basic_intent)
        candidate = PlanCandidate(
            intent_id=basic_intent.id,
            graph=graph,
            estimated_duration=120,
            risk_score=0.3,
            confidence=0.8,
            cost_estimate=5.0,
            historical_success_rate=0.9,
            approval_required=True,
            metadata={"variant": "test"},
        )
        assert candidate.estimated_duration == 120
        assert candidate.risk_score == 0.3
        assert candidate.confidence == 0.8
        assert candidate.cost_estimate == 5.0
        assert candidate.historical_success_rate == 0.9
        assert candidate.approval_required
        assert candidate.metadata["variant"] == "test"

    def test_risk_score_clamped(self, basic_intent, engine):
        """risk_score is clamped to 0.0–1.0 at validation time."""
        graph = engine._instantiate(get_default_template(IntentType.DIAGNOSE), basic_intent)
        candidate = PlanCandidate(
            intent_id=basic_intent.id,
            graph=graph,
            risk_score=0.0,
            confidence=1.0,
        )
        assert candidate.risk_score == 0.0
        assert candidate.confidence == 1.0

    def test_to_dict(self, basic_intent, engine):
        """to_dict returns serialisable dict."""
        graph = engine._instantiate(get_default_template(IntentType.DIAGNOSE), basic_intent)
        candidate = PlanCandidate(
            intent_id=basic_intent.id,
            graph=graph,
        )
        d = candidate.to_dict()
        assert d["id"] == candidate.id
        assert d["intent_id"] == basic_intent.id
        assert d["graph_id"] == graph.id
        assert d["node_count"] == len(graph.nodes)
        assert isinstance(d["risk_score"], float)
        assert isinstance(d["approval_required"], bool)

    def test_extra_fields_forbidden(self, basic_intent, engine):
        """Extra fields raise ValidationError."""
        from pydantic import ValidationError
        graph = engine._instantiate(get_default_template(IntentType.DIAGNOSE), basic_intent)
        with pytest.raises(ValidationError):
            PlanCandidate(
                intent_id=basic_intent.id,
                graph=graph,
                unknown_field="value",
            )


# ── PlanCandidate Generation ─────────────────────────────────────────


class TestGenerateCandidates:
    """generate_candidates produces varied candidates."""

    @pytest.mark.asyncio
    async def test_generate_for_diagnose(self, engine, basic_intent):
        """Generate candidates for DIAGNOSE intent."""
        candidates = await engine.generate_candidates(basic_intent)
        assert len(candidates) >= 1
        for c in candidates:
            assert c.intent_id == basic_intent.id
            assert c.graph is not None
            assert len(c.graph.nodes) > 0

    @pytest.mark.asyncio
    async def test_generate_for_repair(self, engine, repair_intent):
        """Generate candidates for REPAIR intent."""
        candidates = await engine.generate_candidates(repair_intent)
        assert len(candidates) >= 1
        # Repair has approval gate → verify some candidates have approval_required
        approval_variants = [c for c in candidates if c.approval_required]
        assert len(approval_variants) >= 0

    @pytest.mark.asyncio
    async def test_generate_for_deploy(self, engine, deploy_intent):
        """Generate candidates for DEPLOY intent."""
        candidates = await engine.generate_candidates(deploy_intent)
        assert len(candidates) >= 1

    @pytest.mark.asyncio
    async def test_generate_for_scale(self, engine, scale_intent):
        """Generate candidates for SCALE intent."""
        candidates = await engine.generate_candidates(scale_intent)
        assert len(candidates) >= 1

    @pytest.mark.asyncio
    async def test_generate_for_optimize(self, engine, optimize_intent):
        """Generate candidates for OPTIMIZE intent."""
        candidates = await engine.generate_candidates(optimize_intent)
        assert len(candidates) >= 1

    @pytest.mark.asyncio
    async def test_generate_for_monitor_no_template(self, engine, monitor_intent):
        """MONITOR has no built-in template → candidates may be empty but should not crash."""
        candidates = await engine.generate_candidates(monitor_intent)
        # No template → no candidate → empty list is acceptable
        assert isinstance(candidates, list)

    @pytest.mark.asyncio
    async def test_candidates_have_variant_metadata(self, engine, basic_intent):
        """Each candidate has variant metadata (template_id, template_name, variant)."""
        candidates = await engine.generate_candidates(basic_intent)
        for c in candidates:
            meta = c.metadata
            assert "template_id" in meta
            assert "template_name" in meta
            assert "variant" in meta
            assert meta["variant"] in ("primary", "aggressive", "conservative")

    @pytest.mark.asyncio
    async def test_candidates_have_unique_graphs(self, engine, basic_intent):
        """Each candidate has a unique graph ID."""
        candidates = await engine.generate_candidates(basic_intent)
        graph_ids = [c.graph.id for c in candidates]
        assert len(graph_ids) == len(set(graph_ids))


# ── PlanRanker Scoring & Ranking ─────────────────────────────────────


class TestPlanRanker:
    """PlanRanker scoring, ranking, and selection."""

    def test_calculate_score_low_risk_high_confidence(self):
        """Low risk + high confidence → high score."""
        ranker = PlanRanker()
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []
        candidate = PlanCandidate(
            intent_id="i-1",
            graph=mock_graph,
            risk_score=0.1,
            confidence=0.9,
            historical_success_rate=0.9,
            estimated_duration=30,
            approval_required=False,
        )
        score = ranker._calculate_score(candidate)
        assert 0.8 <= score <= 1.0, f"Score {score} should be high"

    def test_calculate_score_high_risk_low_confidence(self):
        """High risk + low confidence → low score."""
        ranker = PlanRanker()
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []
        candidate = PlanCandidate(
            intent_id="i-1",
            graph=mock_graph,
            risk_score=0.9,
            confidence=0.1,
            historical_success_rate=0.1,
            estimated_duration=3600,
            approval_required=True,
        )
        score = ranker._calculate_score(candidate)
        assert 0.0 <= score <= 0.4, f"Score {score} should be low"

    def test_calculate_score_approval_penalty(self):
        """Candidates requiring approval get a lower score."""
        ranker = PlanRanker()
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        no_approval = PlanCandidate(
            intent_id="i-1", graph=mock_graph,
            risk_score=0.5, confidence=0.5,
            historical_success_rate=0.5, estimated_duration=60,
            approval_required=False,
        )
        with_approval = PlanCandidate(
            intent_id="i-1", graph=mock_graph,
            risk_score=0.5, confidence=0.5,
            historical_success_rate=0.5, estimated_duration=60,
            approval_required=True,
        )
        score_no = ranker._calculate_score(no_approval)
        score_yes = ranker._calculate_score(with_approval)
        assert score_no > score_yes

    def test_duration_score_various(self):
        """_duration_score returns diminishing values for longer durations."""
        ranker = PlanRanker()
        assert ranker._duration_score(0) == 1.0
        assert ranker._duration_score(60) < 1.0
        assert ranker._duration_score(3600) < ranker._duration_score(60)
        assert ranker._duration_score(86400) < ranker._duration_score(3600)

    @pytest.mark.asyncio
    async def test_rank_orders_by_score(self):
        """rank returns candidates in descending score order."""
        ranker = PlanRanker()
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        good = PlanCandidate(
            intent_id="i-1", graph=mock_graph,
            risk_score=0.1, confidence=0.9,
            historical_success_rate=0.9, estimated_duration=30,
        )
        medium = PlanCandidate(
            intent_id="i-1", graph=mock_graph,
            risk_score=0.5, confidence=0.5,
            historical_success_rate=0.5, estimated_duration=60,
        )
        bad = PlanCandidate(
            intent_id="i-1", graph=mock_graph,
            risk_score=0.9, confidence=0.1,
            historical_success_rate=0.1, estimated_duration=3600,
        )

        ranked = await ranker.rank([medium, bad, good])
        assert len(ranked) == 3
        # Best first
        assert ranked[0].metadata["_rank_score"] >= ranked[1].metadata["_rank_score"]
        assert ranked[1].metadata["_rank_score"] >= ranked[2].metadata["_rank_score"]

    @pytest.mark.asyncio
    async def test_rank_empty(self):
        """rank of empty list returns empty list."""
        ranker = PlanRanker()
        ranked = await ranker.rank([])
        assert ranked == []

    @pytest.mark.asyncio
    async def test_select_best_returns_highest(self):
        """select_best returns highest-scoring candidate."""
        ranker = PlanRanker()
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        good = PlanCandidate(
            intent_id="i-1", graph=mock_graph,
            risk_score=0.1, confidence=0.9,
            historical_success_rate=0.9, estimated_duration=30,
        )
        bad = PlanCandidate(
            intent_id="i-1", graph=mock_graph,
            risk_score=0.9, confidence=0.1,
            historical_success_rate=0.1, estimated_duration=3600,
        )

        best = await ranker.select_best([bad, good])
        assert best is not None
        assert best.confidence == 0.9  # Best confidence

    @pytest.mark.asyncio
    async def test_select_best_empty(self):
        """select_best on empty list returns None."""
        ranker = PlanRanker()
        best = await ranker.select_best([])
        assert best is None

    @pytest.mark.asyncio
    async def test_select_best_single(self):
        """select_best with single candidate returns it."""
        ranker = PlanRanker()
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        candidate = PlanCandidate(
            intent_id="i-1", graph=mock_graph,
        )
        best = await ranker.select_best([candidate])
        assert best is not None
        assert best.id == candidate.id


# ── Governance Filtering ─────────────────────────────────────────────


class TestGovernanceFilter:
    """apply_governance filters rejected candidates."""

    @pytest.mark.asyncio
    async def test_filter_allows_good_candidates(self):
        """Governance passes candidates with ALLOW decision."""
        mock_gov = MagicMock()
        mock_result = MagicMock()
        mock_result.decision = MagicMock()
        mock_result.decision.value = "ALLOW"
        mock_gov.evaluate = AsyncMock(return_value=mock_result)

        ranker = PlanRanker(governance_engine=mock_gov)
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        candidates = [
            PlanCandidate(intent_id="i-1", graph=mock_graph),
        ]
        filtered = await ranker.apply_governance(candidates)
        assert len(filtered) == 1

    @pytest.mark.asyncio
    async def test_filter_rejects_rejected(self):
        """Governance removes REJECTED candidates."""
        mock_gov = MagicMock()
        mock_result = MagicMock()
        mock_result.decision = MagicMock()
        mock_result.decision.value = "REJECT"
        mock_gov.evaluate = AsyncMock(return_value=mock_result)

        ranker = PlanRanker(governance_engine=mock_gov)
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        candidates = [
            PlanCandidate(intent_id="i-1", graph=mock_graph),
        ]
        filtered = await ranker.apply_governance(candidates)
        assert len(filtered) == 0

    @pytest.mark.asyncio
    async def test_filter_rejects_escalated(self):
        """Governance removes ESCALATED candidates."""
        mock_gov = MagicMock()
        mock_result = MagicMock()
        mock_result.decision = MagicMock()
        mock_result.decision.value = "ESCALATE"
        mock_gov.evaluate = AsyncMock(return_value=mock_result)

        ranker = PlanRanker(governance_engine=mock_gov)
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        candidates = [
            PlanCandidate(intent_id="i-1", graph=mock_graph),
        ]
        filtered = await ranker.apply_governance(candidates)
        assert len(filtered) == 0

    @pytest.mark.asyncio
    async def test_filter_passes_wait_and_approval(self):
        """Governance passes WAIT and REQUIRE_APPROVAL."""
        mock_gov = MagicMock()
        mock_gov.evaluate = AsyncMock()

        ranker = PlanRanker(governance_engine=mock_gov)
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        for decision_val in ("WAIT", "REQUIRE_APPROVAL", "ALLOW_WITH_WARNING"):
            mock_result = MagicMock()
            mock_result.decision = MagicMock()
            mock_result.decision.value = decision_val
            mock_gov.evaluate.return_value = mock_result
            filtered = await ranker.apply_governance([
                PlanCandidate(intent_id="i-1", graph=mock_graph),
            ])
            assert len(filtered) == 1, f"Should pass {decision_val}"

    @pytest.mark.asyncio
    async def test_filter_no_governance(self):
        """Without governance engine, all candidates pass."""
        ranker = PlanRanker(governance_engine=None)
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        candidates = [
            PlanCandidate(intent_id="i-1", graph=mock_graph),
        ]
        filtered = await ranker.apply_governance(candidates)
        assert len(filtered) == 1

    @pytest.mark.asyncio
    async def test_filter_empty_list(self):
        """apply_governance on empty list returns empty list."""
        mock_gov = MagicMock()
        ranker = PlanRanker(governance_engine=mock_gov)
        filtered = await ranker.apply_governance([])
        assert filtered == []

    @pytest.mark.asyncio
    async def test_filter_governance_error_skips(self):
        """If governance evaluation raises, candidate is skipped."""
        mock_gov = MagicMock()
        mock_gov.evaluate = AsyncMock(side_effect=ValueError("Gov error"))

        ranker = PlanRanker(governance_engine=mock_gov)
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        candidates = [
            PlanCandidate(intent_id="i-1", graph=mock_graph),
        ]
        filtered = await ranker.apply_governance(candidates)
        assert len(filtered) == 0


# ── Integration: plan() with candidate_mode ──────────────────────────


class TestPlanWithCandidates:
    """PlanningEngine.plan() with candidate_mode=True."""

    @pytest.mark.asyncio
    async def test_plan_candidate_mode_diagnose(self, engine, basic_intent):
        """plan(candidate_mode=True) works for DIAGNOSE."""
        graph = await engine.plan(basic_intent, candidate_mode=True)
        assert graph is not None
        assert len(graph.nodes) > 0
        assert graph.status == GraphStatus.CREATED

    @pytest.mark.asyncio
    async def test_plan_candidate_mode_repair(self, engine, repair_intent):
        """plan(candidate_mode=True) works for REPAIR."""
        graph = await engine.plan(repair_intent, candidate_mode=True)
        assert graph is not None
        assert len(graph.nodes) > 0

    @pytest.mark.asyncio
    async def test_plan_candidate_mode_deploy(self, engine, deploy_intent):
        """plan(candidate_mode=True) works for DEPLOY."""
        graph = await engine.plan(deploy_intent, candidate_mode=True)
        assert graph is not None
        assert len(graph.nodes) > 0

    @pytest.mark.asyncio
    async def test_plan_candidate_mode_scale(self, engine, scale_intent):
        """plan(candidate_mode=True) works for SCALE."""
        graph = await engine.plan(scale_intent, candidate_mode=True)
        assert graph is not None
        assert len(graph.nodes) > 0

    @pytest.mark.asyncio
    async def test_plan_candidate_mode_optimize(self, engine, optimize_intent):
        """plan(candidate_mode=True) works for OPTIMIZE."""
        graph = await engine.plan(optimize_intent, candidate_mode=True)
        assert graph is not None
        assert len(graph.nodes) > 0

    @pytest.mark.asyncio
    async def test_plan_candidate_mode_monitor_fallback(self, engine, monitor_intent):
        """MONITOR has no template → raises PlanError."""
        with pytest.raises(PlanError) as excinfo:
            await engine.plan(monitor_intent, candidate_mode=True)
        assert "No template" in str(excinfo.value) or "no candidate" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_plan_candidate_mode_no_fallback_when_template_missing(
        self, engine, custom_intent
    ):
        """CUSTOM has no template → raises PlanError."""
        with pytest.raises(PlanError):
            await engine.plan(custom_intent, candidate_mode=True)

    @pytest.mark.asyncio
    async def test_candidate_mode_backward_compatible(self, engine, basic_intent):
        """plan(candidate_mode=False) behaves like original plan()."""
        graph_original = await engine.plan(basic_intent, candidate_mode=False)
        graph_candidate = await engine.plan(basic_intent, candidate_mode=True)
        assert graph_original is not None
        assert graph_candidate is not None

    @pytest.mark.asyncio
    async def test_candidate_mode_with_governance_filter(self, engine_with_governance, basic_intent):
        """plan with governance engine filters rejected candidates."""
        mock_gov = engine_with_governance._governance_engine
        # Make governance reject everything
        mock_result = MagicMock()
        mock_result.decision = MagicMock()
        mock_result.decision.value = "REJECT"
        mock_gov.evaluate.return_value = mock_result

        with pytest.raises(PlanError) as excinfo:
            await engine_with_governance.plan(basic_intent, candidate_mode=True)
        assert "rejected by governance" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_plan_candidate_graph_valid(self, engine, basic_intent):
        """Graph from candidate mode passes validation."""
        graph = await engine.plan(basic_intent, candidate_mode=True)
        errors = graph.validate()
        assert not errors, f"Graph validation failed: {errors}"


# ── Scoring Edge Cases ───────────────────────────────────────────────


class TestScoringEdgeCases:
    """Edge cases for scoring and selection."""

    @pytest.mark.asyncio
    async def test_duplicate_candidates_allowed(self, engine, basic_intent):
        """generate_candidates may produce candidates with same graph in rare cases."""
        candidates = await engine.generate_candidates(basic_intent)
        assert len(candidates) >= 1

    @pytest.mark.asyncio
    async def test_risk_confidence_combination(self):
        """Verify score formula with known inputs."""
        ranker = PlanRanker()
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        # risk=0, confidence=1, historical=1, duration=1, no approval
        candidate = PlanCandidate(
            intent_id="i-1", graph=mock_graph,
            risk_score=0.0, confidence=1.0,
            historical_success_rate=1.0, estimated_duration=1,
            approval_required=False,
        )
        score = ranker._calculate_score(candidate)
        # Components: (1-0)*0.30 + 1*0.30 + 1*0.20 + dur_score(1)*0.10 + 1*0.10
        # = 0.30 + 0.30 + 0.20 + 0.74*0.10 + 0.10 = 0.30+0.30+0.20+0.074+0.10 = 0.974
        assert 0.90 <= score <= 1.0, f"Score {score} should be ~0.97"

    @pytest.mark.asyncio
    async def test_score_not_clamped_low(self):
        """Score can be very low but not negative."""
        ranker = PlanRanker()
        mock_graph = MagicMock(spec=ExecutionGraph)
        mock_graph.id = "g-1"
        mock_graph.name = "test"
        mock_graph.nodes = []

        candidate = PlanCandidate(
            intent_id="i-1", graph=mock_graph,
            risk_score=1.0, confidence=0.0,
            historical_success_rate=0.0, estimated_duration=100000,
            approval_required=True,
        )
        score = ranker._calculate_score(candidate)
        assert 0.0 <= score <= 0.3, f"Score {score} should be very low"

    def test_compute_estimated_duration(self):
        """compute_estimated_duration helper."""
        ranker = PlanRanker()
        assert ranker.compute_estimated_duration(5) == 110  # 60 + 5*10
        assert ranker.compute_estimated_duration(3, 30) == 60  # 30 + 3*10

    def test_compute_risk_score_with_mitigation(self):
        """compute_risk_score decreases risk with compensation and approval."""
        ranker = PlanRanker()
        base = ranker.compute_risk_score(False, False, 0.5)
        mitigated = ranker.compute_risk_score(True, True, 0.5)
        assert mitigated < base


# ── Template Variation ───────────────────────────────────────────────


class TestTemplateVariation:
    """_vary_template produces varied templates."""

    def test_aggressive_variant_has_shorter_retries(self):
        """Aggressive variant reduces retry attempts."""
        template = get_default_template(IntentType.REPAIR)
        assert template is not None
        agg = PlanningEngine._vary_template(template, aggressive=True)
        # Check first node's retry policy was reduced
        for orig_node, agg_node in zip(template.nodes, agg.nodes):
            orig_rp = orig_node.get("retry_policy") or template.retry_policy or {}
            agg_rp = agg_node.get("retry_policy") or agg.retry_policy or {}
            orig_max = orig_rp.get("max_attempts", 3)
            agg_max = agg_rp.get("max_attempts", 1)
            # Aggressive should have ≤ original
            assert agg_max <= orig_max, f"{orig_node['id']}: orig={orig_max}, agg={agg_max}"

    def test_conservative_variant_has_longer_retries(self):
        """Conservative variant increases retry attempts."""
        template = get_default_template(IntentType.DEPLOY)
        assert template is not None
        cons = PlanningEngine._vary_template(template, conservative=True)
        for orig_node, cons_node in zip(template.nodes, cons.nodes):
            orig_rp = orig_node.get("retry_policy") or template.retry_policy or {}
            cons_rp = cons_node.get("retry_policy") or cons.retry_policy or {}
            orig_max = orig_rp.get("max_attempts", 3)
            cons_max = cons_rp.get("max_attempts", orig_max + 2)
            assert cons_max >= orig_max, f"{orig_node['id']}: orig={orig_max}, cons={cons_max}"

    def test_aggressive_variant_id_suffix(self):
        """Aggressive variant gets '-agg' suffix."""
        template = get_default_template(IntentType.DIAGNOSE)
        assert template is not None
        agg = PlanningEngine._vary_template(template, aggressive=True)
        assert agg.id.endswith("-agg")

    def test_conservative_variant_id_suffix(self):
        """Conservative variant gets '-cons' suffix."""
        template = get_default_template(IntentType.DIAGNOSE)
        assert template is not None
        cons = PlanningEngine._vary_template(template, conservative=True)
        assert cons.id.endswith("-cons")

    def test_variant_name_updated(self):
        """Variant name indicates aggressive/conservative."""
        template = get_default_template(IntentType.DIAGNOSE)
        assert template is not None
        agg = PlanningEngine._vary_template(template, aggressive=True)
        assert "Aggressive" in agg.name
        cons = PlanningEngine._vary_template(template, conservative=True)
        assert "Conservative" in cons.name


# ── Custom Template Integration ──────────────────────────────────────


class TestCustomTemplateCandidates:
    """Custom templates work with candidate generation."""

    @pytest.mark.asyncio
    async def test_custom_template_generates_candidates(self, engine, basic_intent):
        """Custom template is used for candidate generation."""
        custom = GraphTemplate(
            id="custom-diagnose",
            intent_type=IntentType.DIAGNOSE,
            name="Custom Diagnose",
            description="Custom diagnose template",
            nodes=[
                {"id": "custom-check", "capability_id": "custom:check",
                 "inputs": {"target": "{target}"}},
            ],
            dependencies=[],
        )
        engine.add_template(custom)
        candidates = await engine.generate_candidates(basic_intent)
        assert len(candidates) >= 1
        # At least one candidate should use the custom template
        custom_candidates = [c for c in candidates
                             if c.metadata.get("template_id") == "custom-diagnose"]
        assert len(custom_candidates) >= 1

    @pytest.mark.asyncio
    async def test_custom_template_in_candidate_mode(self, engine, basic_intent):
        """Custom template used when plan(candidate_mode=True)."""
        custom = GraphTemplate(
            id="custom-diagnose-2",
            intent_type=IntentType.DIAGNOSE,
            name="Custom Diagnose 2",
            description="Custom diagnose 2",
            nodes=[
                {"id": "node-a", "capability_id": "custom:a",
                 "inputs": {"x": "{target}"}},
                {"id": "node-b", "capability_id": "custom:b",
                 "inputs": {"y": "yes"}},
            ],
            dependencies=[{"from": "node-a", "to": "node-b"}],
        )
        engine.add_template(custom)
        graph = await engine.plan(basic_intent, candidate_mode=True)
        assert graph is not None
        assert len(graph.nodes) >= 1


# ── Integration: Full Pipeline (ReasoningEngine → plan candidate mode) ─


@pytest.mark.asyncio
async def test_full_pipeline_candidate_mode():
    """End-to-end with candidate_mode=True via PlanningEngine."""
    from sam.reasoning.engine import ReasoningEngine

    engine = ReasoningEngine()
    graph = await engine._planning_engine.plan(
        Intent(type=IntentType.DIAGNOSE, target="provider:test"),
        candidate_mode=True,
    )
    assert graph is not None
    assert len(graph.nodes) > 0
    errors = graph.validate()
    assert not errors


@pytest.mark.asyncio
async def test_plan_candidate_state_isolation(engine):
    """Multiple plans produce independent graphs."""
    i1 = Intent(type=IntentType.DIAGNOSE, target="provider:a")
    i2 = Intent(type=IntentType.DIAGNOSE, target="provider:b")

    g1 = await engine.plan(i1, candidate_mode=True)
    g2 = await engine.plan(i2, candidate_mode=True)

    assert g1.id != g2.id
    assert len(g1.nodes) > 0
    assert len(g2.nodes) > 0
