# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 125 - Runtime Selection tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.selection_policy import SelectionPolicy
from sam.orchestrator.selection_score import SelectionScore
from sam.orchestrator.runtime_selector import RuntimeSelector, RuntimeSelection
from sam.orchestrator.selection_summary import SelectionSummary
from sam.orchestrator.selection_validator import SelectionValidator, SelectionValidationReport
from sam.orchestrator.conversation_selection import ConversationSelectionBridge
from sam.orchestrator.dashboard_selection import DashboardSelectionBridge
from sam.orchestrator.runtime_inventory import RuntimeInventory
from sam.orchestrator.runtime_descriptor import RuntimeDescriptor
from sam.connectors.dashboard_connector import ExecutionCard


def _inventory():
    return RuntimeInventory(
        runtimes=(
            RuntimeDescriptor("connector", "Connector", pipeline_position=8),
            RuntimeDescriptor("execution", "Execution", pipeline_position=6),
            RuntimeDescriptor("orchestration", "Orchestrator", pipeline_position=9),
        )
    )


def _selector():
    return RuntimeSelector(SelectionPolicy("default", weights={"pipeline": 1.0}))


class TestPolicyImmutable:
    def test_frozen(self):
        p = SelectionPolicy("p")
        with pytest.raises(FrozenInstanceError):
            p.weights = {}


class TestScoreImmutable:
    def test_frozen(self):
        s = SelectionScore("r")
        with pytest.raises(FrozenInstanceError):
            s.score = 5.0


class TestRuntimeSelector:
    def test_select_ordered_chain(self):
        sel = _selector().select(_inventory())
        # order by pipeline position (6, 8, 9)
        assert sel.chain == ("execution", "connector", "orchestration")
        assert sel.is_selected is True

    def test_scores_present(self):
        sel = _selector().select(_inventory())
        assert len(sel.scores) == 3
        assert all(isinstance(s, SelectionScore) for s in sel.scores)

    def test_selection_frozen(self):
        sel = _selector().select(_inventory())
        with pytest.raises(FrozenInstanceError):
            sel.chain = ()


class TestSelectionValidator:
    def test_valid(self):
        sel = _selector().select(_inventory())
        assert SelectionValidator().validate(sel).valid is True

    def test_duplicate_invalid(self):
        sel = RuntimeSelection(chain=("a", "a"))
        report = SelectionValidator().validate(sel)
        assert report.valid is False
        assert report.issue_count == 1


class TestSelectionSummary:
    def test_summary(self):
        sum_ = SelectionSummary("default", ("a", "b"), total_candidates=2)
        assert sum_.selected_count == 2

    def test_frozen(self):
        sum_ = SelectionSummary("default", ("a",))
        with pytest.raises(FrozenInstanceError):
            sum_.policy = "x"


# ---------- Conversation bridge ----------
class TestConversationSelectionBridge:
    def test_select(self):
        b = ConversationSelectionBridge(_selector())
        sel = b.select(_inventory())
        assert sel.chain[0] == "execution"

    def test_summarize(self):
        b = ConversationSelectionBridge(_selector())
        sel = b.select(_inventory())
        sum_ = b.summarize(sel)
        assert sum_.selected_count == 3


# ---------- Dashboard bridge ----------
class TestDashboardSelectionBridge:
    def test_five_cards(self):
        sel = _selector().select(_inventory())
        cards = DashboardSelectionBridge().cards_for(sel)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        sel = _selector().select(_inventory())
        b = DashboardSelectionBridge()
        assert "chain" in b.verdict_card(sel).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        SelectionPolicy,
        SelectionScore,
        RuntimeSelection,
        SelectionSummary,
        SelectionValidationReport,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
