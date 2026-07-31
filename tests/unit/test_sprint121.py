"""Sprint 121 — Connector Runtime Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.connector_descriptor import ConnectorDescriptor
from sam.connectors.connector_capability import ConnectorCapability
from sam.connectors.connector_registry import ConnectorRegistry
from sam.connectors.runtime import RuntimeCheck, RuntimeReadiness, ConnectorRuntime
from sam.connectors.runtime_pipeline import PipelineStage, RuntimePipeline, RuntimePipelineBuilder
from sam.connectors.runtime_coordinator import CoordinationResult, RuntimeCoordinator
from sam.connectors.runtime_status import RuntimeStatus
from sam.connectors.runtime_report import RuntimeReport, RuntimeReporter
from sam.connectors.conversation_runtime import ConversationRuntimeBridge
from sam.connectors.dashboard_runtime import DashboardRuntimeBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _ready_registry():
    r = ConnectorRegistry()
    r.register(ConnectorDescriptor("c1", "OpenAI", "llm"))
    r.attach_capability(ConnectorCapability("cap1", "c1", "generate", "llm"))
    return r


# ============================================================
# DTO
# ============================================================
class TestRuntimeCheck:
    def test_default(self):
        c = RuntimeCheck("registry")
        assert c.ok is True

    def test_immutable(self):
        c = RuntimeCheck("registry")
        with pytest.raises(FrozenInstanceError):
            c.ok = False


class TestRuntimeReadiness:
    def test_immutable(self):
        r = RuntimeReadiness()
        with pytest.raises(FrozenInstanceError):
            r.ready = True


class TestRuntimeStatus:
    def test_default(self):
        s = RuntimeStatus()
        assert s.phase == "boot"

    def test_immutable(self):
        s = RuntimeStatus()
        with pytest.raises(FrozenInstanceError):
            s.ready = True


# ============================================================
# Engine — ConnectorRuntime
# ============================================================
class TestConnectorRuntime:
    def test_ready(self):
        rt = ConnectorRuntime(_ready_registry())
        rd = rt.readiness()
        assert rd.ready is True

    def test_not_ready_empty(self):
        rt = ConnectorRuntime(ConnectorRegistry())
        rd = rt.readiness()
        assert rd.ready is False


# ============================================================
# Engine — RuntimePipelineBuilder
# ============================================================
class TestRuntimePipelineBuilder:
    def test_build_8_stages(self):
        p = RuntimePipelineBuilder().build()
        assert len(p.stages) == 8
        assert p.stages[0].name == "registry"
        assert p.stages[-1].name == "preview"


# ============================================================
# Engine — RuntimeCoordinator
# ============================================================
class TestRuntimeCoordinator:
    def test_readiness(self):
        c = RuntimeCoordinator(_ready_registry())
        assert c.readiness().ready is True

    def test_pipeline(self):
        c = RuntimeCoordinator(_ready_registry())
        assert len(c.pipeline().stages) == 8

    def test_health(self):
        c = RuntimeCoordinator(_ready_registry())
        h = c.health()
        assert h.ready is True


# ============================================================
# Engine — RuntimeReporter
# ============================================================
class TestRuntimeReporter:
    def test_report(self):
        rep = RuntimeReporter(ConnectorRuntime(_ready_registry()))
        r = rep.report()
        assert r.ready is True
        assert r.stage_count >= 3


# ============================================================
# Bridges
# ============================================================
class TestConversationRuntimeBridge:
    def test_readiness(self):
        b = ConversationRuntimeBridge(_ready_registry())
        assert b.readiness().ready is True

    def test_report(self):
        b = ConversationRuntimeBridge(_ready_registry())
        assert b.report().ready is True


class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        b = DashboardRuntimeBridge(_ready_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)


# ============================================================
# Immutability
# ============================================================
class TestRuntimeImmutability:
    DTO_CLASSES = [
        RuntimeCheck, RuntimeReadiness, RuntimeStatus, RuntimeReport, CoordinationResult,
        PipelineStage, RuntimePipeline,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
