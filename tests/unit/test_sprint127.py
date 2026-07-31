# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 127 - Dependency Resolver tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.dependency_graph import DependencyGraph
from sam.orchestrator.dependency_resolver import DependencyResolver
from sam.orchestrator.dependency_validator import DependencyValidator, DependencyValidationReport
from sam.orchestrator.dependency_report import DependencyReport
from sam.orchestrator.dependency_snapshot import DependencySnapshot
from sam.orchestrator.conversation_dependency import ConversationDependencyBridge
from sam.orchestrator.dashboard_dependency import DashboardDependencyBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _graph():
    g = DependencyGraph()
    g.add_edge("connector", "runtime_kernel")
    g.add_edge("orchestration", "connector")
    g.add_edge("execution", "runtime_kernel")
    return g


class TestDependencyGraph:
    def test_dependencies(self):
        g = _graph()
        assert g.dependencies("connector") == frozenset({"runtime_kernel"})

    def test_dependents(self):
        g = _graph()
        assert g.dependents("runtime_kernel") == frozenset({"connector", "execution"})

    def test_edge_count(self):
        assert _graph().edge_count() == 3

    def test_nodes(self):
        g = _graph()
        assert "runtime_kernel" in g.all_nodes()


class TestDependencyResolver:
    def test_resolve_deps_first(self):
        order = DependencyResolver(_graph()).resolve()
        # dependents must appear after dependencies
        assert order.index("runtime_kernel") < order.index("connector")
        assert order.index("runtime_kernel") < order.index("execution")

    def test_deterministic(self):
        r = DependencyResolver(_graph())
        assert r.resolve() == r.resolve()

    def test_cycle(self):
        g = DependencyGraph()
        g.add_edge("a", "b")
        g.add_edge("b", "a")
        assert DependencyResolver(g).has_cycle() is True


class TestDependencyValidator:
    def test_valid(self):
        assert DependencyValidator(_graph()).validate().valid is True

    def test_cycle_invalid(self):
        g = DependencyGraph()
        g.add_edge("a", "b")
        g.add_edge("b", "a")
        report = DependencyValidator(g).validate()
        assert report.valid is False
        assert report.issue_count >= 1


class TestDependencyReport:
    def test_report(self):
        r = DependencyReport(("a", "b"), acyclic=True, edge_count=1)
        assert r.order == ("a", "b")

    def test_frozen(self):
        r = DependencyReport(("a",))
        with pytest.raises(FrozenInstanceError):
            r.order = ()


class TestDependencySnapshot:
    def test_frozen(self):
        s = DependencySnapshot()
        with pytest.raises(FrozenInstanceError):
            s.nodes = ()


# ---------- Conversation bridge ----------
class TestConversationDependencyBridge:
    def test_resolve(self):
        b = ConversationDependencyBridge(_graph())
        assert len(b.resolve()) == 4

    def test_cycle(self):
        g = DependencyGraph()
        g.add_edge("a", "b")
        g.add_edge("b", "a")
        assert ConversationDependencyBridge(g).has_cycle() is True


# ---------- Dashboard bridge ----------
class TestDashboardDependencyBridge:
    def test_five_cards(self):
        r = DependencyReport(("a", "b"), acyclic=True, edge_count=1)
        cards = DashboardDependencyBridge().cards_for(r)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        r = DependencyReport(("a",))
        b = DashboardDependencyBridge()
        assert "order" in b.verdict_card(r).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [DependencyReport, DependencySnapshot, DependencyValidationReport]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
