# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 126 - Pipeline Builder tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.pipeline_stage import PipelineStage
from sam.orchestrator.pipeline_descriptor import PipelineDescriptor
from sam.orchestrator.pipeline_builder import PipelineBuilder, BuiltPipeline
from sam.orchestrator.pipeline_validator import PipelineValidator, PipelineValidationReport
from sam.orchestrator.pipeline_summary import PipelineSummary
from sam.orchestrator.conversation_pipeline import ConversationPipelineBridge
from sam.orchestrator.dashboard_pipeline import DashboardPipelineBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _builder():
    b = PipelineBuilder()
    b.register_names(
        {
            "execution": "Execution Runtime",
            "connector": "Connector Runtime",
            "orchestration": "Orchestration Runtime",
        }
    )
    return b


class TestStageImmutable:
    def test_frozen(self):
        s = PipelineStage("s", "r")
        with pytest.raises(FrozenInstanceError):
            s.order = 9


class TestDescriptorImmutable:
    def test_frozen(self):
        d = PipelineDescriptor("p")
        with pytest.raises(FrozenInstanceError):
            d.name = "x"


class TestPipelineBuilder:
    def test_build_stages(self):
        p = _builder().build("pl", ("execution", "connector", "orchestration"))
        assert p.stage_count == 3

    def test_stage_order(self):
        p = _builder().build("pl", ("execution", "connector"))
        assert p.stages[0].order == 0
        assert p.stages[1].order == 1

    def test_names_mapped(self):
        p = _builder().build("pl", ("connector",))
        assert p.stages[0].name == "Connector Runtime"

    def test_runtime_ids(self):
        p = _builder().build("pl", ("a", "b", "c"))
        assert p.runtime_ids == ("a", "b", "c")

    def test_pipeline_frozen(self):
        p = _builder().build("pl", ("a",))
        with pytest.raises(FrozenInstanceError):
            p.stages = ()


class TestPipelineValidator:
    def test_valid(self):
        p = _builder().build("pl", ("a", "b"))
        assert PipelineValidator().validate(p).valid is True

    def test_order_mismatch_invalid(self):
        p = BuiltPipeline(
            "pl",
            (PipelineStage("s1", "b", order=5),),
        )
        report = PipelineValidator().validate(p)
        assert report.valid is False
        assert report.issue_count == 1


class TestPipelineSummary:
    def test_summary(self):
        s = PipelineSummary("pl", ("a", "b"), total_stages=2)
        assert s.total_stages == 2


# ---------- Conversation bridge ----------
class TestConversationPipelineBridge:
    def test_build(self):
        b = ConversationPipelineBridge(_builder())
        p = b.build("pl", ("connector",))
        assert p.stage_count == 1

    def test_stage_count(self):
        b = ConversationPipelineBridge(_builder())
        p = b.build("pl", ("a", "b", "c"))
        assert b.stage_count(p) == 3


# ---------- Dashboard bridge ----------
class TestDashboardPipelineBridge:
    def test_five_cards(self):
        p = _builder().build("pl", ("a", "b", "c", "d"))
        cards = DashboardPipelineBridge().cards_for(p)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        p = _builder().build("pl", ("a",))
        b = DashboardPipelineBridge()
        assert "stage" in b.verdict_card(p).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        PipelineStage,
        PipelineDescriptor,
        BuiltPipeline,
        PipelineSummary,
        PipelineValidationReport,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
