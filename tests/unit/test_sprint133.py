# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 133 - Certification tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.orchestration_certification import (
    OrchestrationCertifier,
    CertificationCriterion,
    CertificationResult,
)
from sam.orchestrator.orchestration_score import OrchestrationScore
from sam.orchestrator.orchestration_validator import (
    CertificationValidator,
    CertificationValidation,
)
from sam.orchestrator.orchestration_summary import OrchestrationSummary
from sam.orchestrator.orchestration_manifest import OrchestrationManifest
from sam.orchestrator.conversation_certification import ConversationCertificationBridge
from sam.orchestrator.dashboard_certification import DashboardCertificationBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestCriterionImmutable:
    def test_frozen(self):
        c = CertificationCriterion("x", True)
        with pytest.raises(FrozenInstanceError):
            c.met = False


class TestCertifier:
    def test_certified(self):
        result = OrchestrationCertifier().certify()
        assert result.certified is True

    def test_all_criteria(self):
        result = OrchestrationCertifier().certify()
        assert result.total == 10
        assert result.met_count == 10

    def test_constraint_names_present(self):
        result = OrchestrationCertifier().certify()
        names = {c.name for c in result.criteria}
        for expected in ("no_network", "no_async", "no_thread", "frozen_dto", "preview_only"):
            assert expected in names


class TestResultImmutable:
    def test_frozen(self):
        r = CertificationResult(True)
        with pytest.raises(FrozenInstanceError):
            r.criteria = ()


class TestScoreImmutable:
    def test_frozen(self):
        s = OrchestrationScore()
        with pytest.raises(FrozenInstanceError):
            s.score = 0

    def test_pass(self):
        assert OrchestrationScore(score=95.0, certified=True).passed is True


class TestValidator:
    def test_valid(self):
        result = OrchestrationCertifier().certify()
        assert CertificationValidator().validate(result).valid is True

    def test_inconsistent(self):
        result = CertificationResult(True, criteria=(CertificationCriterion("a", False),))
        report = CertificationValidator().validate(result)
        assert report.valid is False
        assert report.issue_count >= 1


class TestSummaryImmutable:
    def test_frozen(self):
        s = OrchestrationSummary()
        with pytest.raises(FrozenInstanceError):
            s.version = "9"


class TestManifestImmutable:
    def test_frozen(self):
        m = OrchestrationManifest()
        with pytest.raises(FrozenInstanceError):
            m.subsystems = ()

    def test_eleven_subsystems(self):
        assert OrchestrationManifest().subsystem_count == 11


# ---------- Conversation bridge ----------
class TestConversationCertificationBridge:
    def test_certify(self):
        b = ConversationCertificationBridge(OrchestrationCertifier())
        result = b.certify()
        assert b.criteria_met(result) == 10


# ---------- Dashboard bridge ----------
class TestDashboardCertificationBridge:
    def test_five_cards(self):
        result = OrchestrationCertifier().certify()
        cards = DashboardCertificationBridge().cards_for(result)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        result = OrchestrationCertifier().certify()
        b = DashboardCertificationBridge()
        assert "plan" in b.verdict_card(result).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        CertificationCriterion,
        CertificationResult,
        OrchestrationScore,
        CertificationValidation,
        OrchestrationSummary,
        OrchestrationManifest,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
