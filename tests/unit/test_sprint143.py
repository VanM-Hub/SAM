# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 143 - Mission Certification tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.mission_runtime.mission_certification import (
    MissionCertifier,
    CertificationCriterion,
    CertificationResult,
)
from sam.mission_runtime.mission_score import MissionScore
from sam.mission_runtime.mission_validator import (
    CertificationValidator,
    CertificationValidation,
)
from sam.mission_runtime.mission_summary import MissionSummary
from sam.mission_runtime.mission_manifest import MissionManifest
from sam.mission_runtime.conversation_certification import ConversationCertificationBridge
from sam.mission_runtime.dashboard_certification import DashboardCertificationBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestCriterionImmutable:
    def test_frozen(self):
        c = CertificationCriterion("x", True)
        with pytest.raises(FrozenInstanceError):
            c.met = False


class TestCertifier:
    def test_certified(self):
        result = MissionCertifier().certify()
        assert result.certified is True

    def test_all_criteria(self):
        result = MissionCertifier().certify()
        assert result.total == 12
        assert result.met_count == 12

    def test_constraints_present(self):
        result = MissionCertifier().certify()
        names = {c.name for c in result.criteria}
        for expected in (
            "no_network",
            "no_async",
            "no_thread",
            "no_subprocess",
            "frozen_dto",
            "plan_only",
            "no_execute",
        ):
            assert expected in names


class TestResultImmutable:
    def test_frozen(self):
        r = CertificationResult(True)
        with pytest.raises(FrozenInstanceError):
            r.criteria = ()


class TestScoreImmutable:
    def test_frozen(self):
        s = MissionScore()
        with pytest.raises(FrozenInstanceError):
            s.score = 0

    def test_passed(self):
        assert MissionScore(score=95.0, certified=True).passed is True


class TestValidator:
    def test_valid(self):
        result = MissionCertifier().certify()
        assert CertificationValidator().validate(result).valid is True

    def test_inconsistent(self):
        result = CertificationResult(True, criteria=(CertificationCriterion("a", False),))
        report = CertificationValidator().validate(result)
        assert report.valid is False


class TestSummaryImmutable:
    def test_frozen(self):
        s = MissionSummary()
        with pytest.raises(FrozenInstanceError):
            s.version = "9"


class TestManifestImmutable:
    def test_frozen(self):
        m = MissionManifest()
        with pytest.raises(FrozenInstanceError):
            m.subsystems = ()

    def test_subsystem_count(self):
        assert MissionManifest().subsystem_count == 10


# ---------- Conversation bridge ----------
class TestConversationCertificationBridge:
    def test_certify(self):
        b = ConversationCertificationBridge(MissionCertifier())
        result = b.certify()
        assert b.criteria_met(result) == 12


# ---------- Dashboard bridge ----------
class TestDashboardCertificationBridge:
    def test_five_cards(self):
        result = MissionCertifier().certify()
        cards = DashboardCertificationBridge().cards_for(result)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        result = MissionCertifier().certify()
        b = DashboardCertificationBridge()
        assert "lifecycle" in b.verdict_card(result).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        CertificationCriterion,
        CertificationResult,
        MissionScore,
        CertificationValidation,
        MissionSummary,
        MissionManifest,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
