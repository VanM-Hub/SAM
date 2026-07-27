"""
Tests for Planning Engine – Sprint 22 Fase 2

Covers:
- GraphTemplate model defaults, helpers, built-in templates
- PlanningEngine: template lookup, instantiate, plan pipeline
- Knowledge enrichment
- Custom template registration
- Error cases (no template, validation failure, PlanError)
- Edge cases (MONITOR, CUSTOM intent types without templates)
"""

from __future__ import annotations

import pytest
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID

from src.sam.reasoning.intent import Intent, IntentType, IntentStatus, IntentParser
from src.sam.reasoning.templates import (
    GraphTemplate,
    BUILTIN_TEMPLATES,
    get_default_template,
)
from src.sam.reasoning.planner import PlanningEngine, PlanError
from src.sam.execution.graph import ExecutionGraph, GraphStatus
from src.sam.execution.node import (
    ExecutionNode,
    NodeStatus,
    RetryPolicy,
    RetryBackoff,
    CompensationPolicy,
    CompensationOnFailure,
)


# ======================================================================
#  Fixtures
# ======================================================================


class _MockKnowledgeStore:
    """Minimal Knowledge Store stub for enrichment tests."""

    def __init__(self) -> None:
        self.search_results: List[Dict[str, Any]] = []
        self.subject_results: List[Dict[str, Any]] = []

    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self.search_results

    async def get_by_subject(self, subject: str) -> List[Dict[str, Any]]:
        return self.subject_results


@pytest.fixture
def basic_intent() -> Intent:
    return Intent(
        id="int-001",
        type=IntentType.DIAGNOSE,
        target="provider:nvidia",
        description="Check Nvidia provider",
        correlation_id="corr-001",
    )


@pytest.fixture
def repair_intent() -> Intent:
    return Intent(
        id="int-002",
        type=IntentType.REPAIR,
        target="provider:nvidia",
        description="Repair Nvidia provider after failure",
        parameters={"deep_scan": True, "dry_run": False, "version": "2.0"},
        correlation_id="corr-002",
    )


@pytest.fixture
def deploy_intent() -> Intent:
    return Intent(
        id="int-003",
        type=IntentType.DEPLOY,
        target="provider:openai",
        description="Deploy new plugin to workspace",
        parameters={"version": "3.1.0", "workspace": "production"},
        context={"environment": "prod", "priority": "high"},
        correlation_id="corr-003",
    )


@pytest.fixture
def scale_intent() -> Intent:
    return Intent(
        id="int-004",
        type=IntentType.SCALE,
        target="cluster:worker-pool",
        description="Scale worker pool up by 3 nodes",
        parameters={"direction": "up", "count": 3},
        correlation_id="corr-004",
    )


@pytest.fixture
def optimize_intent() -> Intent:
    return Intent(
        id="int-005",
        type=IntentType.OPTIMIZE,
        target="service:db-cluster",
        description="Optimize DB cluster for high throughput",
        parameters={"threshold": "0.85", "aggressive": True},
        correlation_id="corr-005",
    )


@pytest.fixture
def monitor_intent() -> Intent:
    return Intent(
        id="int-006",
        type=IntentType.MONITOR,
        target="cluster:worker-pool",
        description="Monitor worker pool performance",
        correlation_id="corr-006",
    )


@pytest.fixture
def custom_intent() -> Intent:
    return Intent(
        id="int-007",
        type=IntentType.CUSTOM,
        target="my-custom-command",
        description="Custom user-defined operation",
        correlation_id="corr-007",
    )


@pytest.fixture
def mock_knowledge() -> _MockKnowledgeStore:
    return _MockKnowledgeStore()


@pytest.fixture
def engine() -> PlanningEngine:
    return PlanningEngine()


@pytest.fixture
def engine_with_knowledge(mock_knowledge: _MockKnowledgeStore) -> PlanningEngine:
    return PlanningEngine(knowledge_store=mock_knowledge)


# ======================================================================
#  GraphTemplate Tests
# ======================================================================


class TestGraphTemplate:
    """GraphTemplate model behaviour, helpers, and built-in templates."""

    def test_default_id_generated(self):
        """Template without explicit ID gets a UUID."""
        tmpl = GraphTemplate(
            intent_type=IntentType.DIAGNOSE,
            name="test",
            description="test desc",
        )
        # Should be a valid UUID string
        parsed = UUID(tmpl.id)
        assert str(parsed) == tmpl.id

    def test_get_node_ids_empty(self):
        tmpl = GraphTemplate(intent_type=IntentType.DIAGNOSE, name="e", description="d")
        assert tmpl.get_node_ids() == set()

    def test_get_node_ids(self):
        tmpl = GraphTemplate(
            intent_type=IntentType.DIAGNOSE,
            name="e",
            description="d",
            nodes=[{"id": "a"}, {"id": "b"}, {}],
        )
        assert tmpl.get_node_ids() == {"a", "b"}

    def test_get_entry_node_ids(self):
        tmpl = GraphTemplate(
            intent_type=IntentType.REPAIR,
            name="e",
            description="d",
            nodes=[{"id": "d"}, {"id": "p"}, {"id": "a"}, {"id": "e"}],
            dependencies=[
                {"from": "d", "to": "p"},
                {"from": "p", "to": "a"},
                {"from": "a", "to": "e"},
            ],
        )
        assert tmpl.get_entry_node_ids() == ["d"]
        assert tmpl.get_exit_node_ids() == ["e"]

    def test_get_entry_with_fork(self):
        """Fork: multiple entry nodes, multiple exit nodes."""
        tmpl = GraphTemplate(
            intent_type=IntentType.REPAIR,
            name="e",
            description="d",
            nodes=[{"id": "a"}, {"id": "b"}, {"id": "c"}],
            dependencies=[{"from": "a", "to": "c"}, {"from": "b", "to": "c"}],
        )
        assert sorted(tmpl.get_entry_node_ids()) == ["a", "b"]
        assert tmpl.get_exit_node_ids() == ["c"]


# ======================================================================
#  Built-in Templates
# ======================================================================


class TestBuiltinTemplates:
    """All 5 built-in templates are present and structurally valid."""

    def test_all_5_templates_present(self):
        assert len(BUILTIN_TEMPLATES) == 5

    def test_diagnose_template(self):
        tmpl = BUILTIN_TEMPLATES[IntentType.DIAGNOSE]
        assert tmpl.id == "tmpl-diagnose-runtime"
        assert len(tmpl.nodes) == 3
        assert len(tmpl.dependencies) == 2
        assert tmpl.get_entry_node_ids() == ["health-check"]
        assert tmpl.get_exit_node_ids() == ["report"]

    def test_repair_template(self):
        tmpl = BUILTIN_TEMPLATES[IntentType.REPAIR]
        assert tmpl.id == "tmpl-repair-provider"
        assert len(tmpl.nodes) == 6
        assert len(tmpl.dependencies) == 4
        # Has global retry policy
        assert tmpl.retry_policy is not None
        assert tmpl.retry_policy["max_attempts"] == 2

    def test_deploy_template(self):
        tmpl = BUILTIN_TEMPLATES[IntentType.DEPLOY]
        assert tmpl.id == "tmpl-deploy-workspace"
        assert len(tmpl.nodes) == 4
        assert len(tmpl.dependencies) == 2
        # Verify compensation chain
        deploy = next(n for n in tmpl.nodes if n["id"] == "deploy")
        assert deploy.get("compensation_policy", {}).get("on_failure") == "COMPENSATE"

    def test_scale_template(self):
        tmpl = BUILTIN_TEMPLATES[IntentType.SCALE]
        assert tmpl.id == "tmpl-scale-cluster"
        assert len(tmpl.nodes) == 5
        assert tmpl.metadata.get("requires_approval") is True

    def test_optimize_template(self):
        tmpl = BUILTIN_TEMPLATES[IntentType.OPTIMIZE]
        assert tmpl.id == "tmpl-optimize-target"
        assert len(tmpl.nodes) == 5
        assert tmpl.metadata.get("version") == "1.0"

    def test_get_default_template_found(self):
        tmpl = get_default_template(IntentType.DIAGNOSE)
        assert tmpl is not None
        assert tmpl.intent_type == IntentType.DIAGNOSE

    def test_get_default_template_not_found(self):
        assert get_default_template(IntentType.CUSTOM) is None
        assert get_default_template(IntentType.MONITOR) is None


# ======================================================================
#  PlanningEngine — Template & Pipeline Tests
# ======================================================================


class TestPlanningEngineBasic:
    """Template lookup, instantiation, basic plan."""

    @pytest.mark.asyncio
    async def test_get_template_found(self, engine: PlanningEngine):
        tmpl = await engine.get_template(IntentType.DIAGNOSE)
        assert tmpl is not None
        assert tmpl.intent_type == IntentType.DIAGNOSE

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, engine: PlanningEngine):
        assert await engine.get_template(IntentType.CUSTOM) is None
        assert await engine.get_template(IntentType.MONITOR) is None

    @pytest.mark.asyncio
    async def test_plan_diagnose(self, engine: PlanningEngine, basic_intent: Intent):
        graph = await engine.plan(basic_intent)
        assert isinstance(graph, ExecutionGraph)
        assert graph.status == GraphStatus.CREATED
        assert graph.correlation_id == "corr-001"
        assert len(graph.nodes) == 3
        assert graph.nodes[0].graph_id == graph.id

    @pytest.mark.asyncio
    async def test_plan_repair(self, engine: PlanningEngine, repair_intent: Intent):
        graph = await engine.plan(repair_intent)
        assert len(graph.nodes) == 6
        assert graph.metadata["template_id"] == "tmpl-repair-provider"
        assert graph.metadata["requires_approval"] is True

    @pytest.mark.asyncio
    async def test_plan_deploy(self, engine: PlanningEngine, deploy_intent: Intent):
        graph = await engine.plan(deploy_intent)
        assert "Deploy to Workspace" in graph.name
        assert len(graph.nodes) == 4
        # Verify placeholder substitution for target
        deploy = next(n for n in graph.nodes if n.id == "deploy")
        assert "provider.openai" in deploy.capability_id  # target with ":" replaced by "."

    @pytest.mark.asyncio
    async def test_plan_scale(self, engine: PlanningEngine, scale_intent: Intent):
        graph = await engine.plan(scale_intent)
        assert graph.metadata["requires_approval"] is True
        stablise = next(n for n in graph.nodes if n.id == "stabilise")
        assert stablise.retry_policy.backoff == RetryBackoff.LINEAR

    @pytest.mark.asyncio
    async def test_plan_optimize(self, engine: PlanningEngine, optimize_intent: Intent):
        graph = await engine.plan(optimize_intent)
        assert "Optimize Target" in graph.name
        assert graph.metadata["intent_id"] == "int-005"

    @pytest.mark.asyncio
    async def test_plan_monitor_no_template(self, engine: PlanningEngine, monitor_intent: Intent):
        """MONITOR has no built-in template → PlanError."""
        with pytest.raises(PlanError) as exc:
            await engine.plan(monitor_intent)
        assert "No template" in str(exc.value)
        assert exc.value.intent_id == "int-006"

    @pytest.mark.asyncio
    async def test_plan_custom_no_template(self, engine: PlanningEngine, custom_intent: Intent):
        """CUSTOM has no built-in template → PlanError."""
        with pytest.raises(PlanError) as exc:
            await engine.plan(custom_intent)
        assert "No template" in str(exc.value)

    @pytest.mark.asyncio
    async def test_plan_validated_graph(self, engine: PlanningEngine, basic_intent: Intent):
        """Generated graph passes validation."""
        graph = await engine.plan(basic_intent)
        errors = graph.validate()
        assert errors == [], f"Graph validation errors: {errors}"


# ======================================================================
#  Placeholder Substitution Tests
# ======================================================================


class TestPlaceholderSubstitution:
    """Verify {placeholder} values are correctly replaced in graph."""

    @pytest.mark.asyncio
    async def test_target_substitution(self, engine: PlanningEngine, basic_intent: Intent):
        graph = await engine.plan(basic_intent)
        hc = next(n for n in graph.nodes if n.id == "health-check")
        assert "provider.nvidia" in hc.capability_id

    @pytest.mark.asyncio
    async def test_parameter_substitution(self, engine: PlanningEngine, repair_intent: Intent):
        graph = await engine.plan(repair_intent)
        # Repair template first node is "diagnose"
        diagnose = next(n for n in graph.nodes if n.id == "diagnose")
        assert diagnose.inputs["target"] == "provider.nvidia"

    @pytest.mark.asyncio
    async def test_colon_in_target_replaced(self, engine: PlanningEngine):
        """Colons in target like provider:nvidia → provider.nvidia in capability IDs."""
        intent = Intent(
            id="int-colon", type=IntentType.DIAGNOSE,
            target="provider:nvidia", correlation_id="corr-x",
        )
        graph = await engine.plan(intent)
        hc = next(n for n in graph.nodes if n.id == "health-check")
        assert "provider.nvidia" in hc.capability_id

    @pytest.mark.asyncio
    async def test_dependency_substitution(self, engine: PlanningEngine):
        """Verify dependencies are correctly assigned to the right nodes."""
        intent = Intent(
            id="int-dep", type=IntentType.DIAGNOSE,
            target="my-service", correlation_id="corr-dep",
        )
        graph = await engine.plan(intent)
        provider_test = next(n for n in graph.nodes if n.id == "provider-test")
        assert "health-check" in provider_test.dependencies

    @pytest.mark.asyncio
    async def test_placeholder_unknown_left_as_is(self):
        """Unknown placeholders like {unknown_key} are left as-is."""
        engine = PlanningEngine()
        sub = {"target": "x"}
        result = engine._substitute("hello {target} and {unknown_key}", sub)
        assert result == "hello x and {unknown_key}"


# ======================================================================
#  Knowledge Enrichment Tests
# ======================================================================


class TestKnowledgeEnrichment:
    """Enrich graph with facts from Knowledge Store."""

    @pytest.mark.asyncio
    async def test_enrich_without_store_returns_unchanged(
        self, engine: PlanningEngine, basic_intent: Intent
    ):
        graph = await engine.plan(basic_intent)
        # No knowledge_store set, enrichment skipped
        assert "knowledge_facts" not in graph.metadata

    @pytest.mark.asyncio
    async def test_enrich_with_facts(
        self,
        engine_with_knowledge: PlanningEngine,
        mock_knowledge: _MockKnowledgeStore,
        basic_intent: Intent,
    ):
        mock_knowledge.search_results = [
            {"id": "fact-1", "target": "provider.nvidia", "key": "health", "value": "degraded"},
            {"id": "fact-2", "target": "provider.nvidia", "key": "last_incident", "value": "2026-07-24"},
        ]
        graph = await engine_with_knowledge.plan(basic_intent)
        assert "knowledge_facts" in graph.metadata
        assert "fact-1" in graph.metadata["knowledge_facts"]
        assert "fact-2" in graph.metadata["knowledge_facts"]
        # Individual facts stored as metadata keys
        assert graph.metadata.get("knowledge.provider.nvidia.health") == "degraded"

    @pytest.mark.asyncio
    async def test_enrich_with_fallback_get_by_subject(
        self,
        engine_with_knowledge: PlanningEngine,
        mock_knowledge: _MockKnowledgeStore,
        basic_intent: Intent,
    ):
        """When search returns empty, falls back to get_by_subject."""
        mock_knowledge.search_results = []  # search returns nothing
        mock_knowledge.subject_results = [
            {"id": "fact-3", "target": "provider.nvidia", "key": "version", "value": "1.2.3"},
        ]
        graph = await engine_with_knowledge.plan(basic_intent)
        assert "fact-3" in graph.metadata.get("knowledge_facts", [])

    @pytest.mark.asyncio
    async def test_enrich_context_propagated(
        self,
        engine_with_knowledge: PlanningEngine,
        deploy_intent: Intent,
    ):
        graph = await engine_with_knowledge.plan(deploy_intent)
        assert graph.metadata.get("context.environment") == "prod"
        assert graph.metadata.get("context.priority") == "high"

    @pytest.mark.asyncio
    async def test_enrich_without_store_plan_still_succeeds(
        self, engine: PlanningEngine, basic_intent: Intent
    ):
        graph = await engine.plan(basic_intent)
        assert isinstance(graph, ExecutionGraph)
        assert graph.name


# ======================================================================
#  Custom Template Registration Tests
# ======================================================================


class TestCustomTemplates:
    """Register, override, remove custom templates."""

    @pytest.mark.asyncio
    async def test_add_custom_template(self, engine: PlanningEngine):
        """Custom template for CUSTOM type."""
        tmpl = GraphTemplate(
            id="my-custom-plan",
            intent_type=IntentType.CUSTOM,
            name="My Custom Plan",
            description="User-defined plan",
            nodes=[{"id": "step1", "capability_id": "my-cap:run"}],
        )
        engine.add_template(tmpl)

        retrieved = await engine.get_template(IntentType.CUSTOM)
        assert retrieved is not None
        assert retrieved.id == "my-custom-plan"

    @pytest.mark.asyncio
    async def test_custom_plan_execution(self, engine: PlanningEngine, custom_intent: Intent):
        """Custom template allows CUSTOM intents to be planned."""
        tmpl = GraphTemplate(
            id="my-custom-plan",
            intent_type=IntentType.CUSTOM,
            name="My Custom Plan",
            description="User-defined plan",
            nodes=[{"id": "step1", "capability_id": "my-cap:run", "inputs": {"target": "{target}"}}],
        )
        engine.add_template(tmpl)
        graph = await engine.plan(custom_intent)
        assert graph is not None
        assert len(graph.nodes) == 1
        assert graph.nodes[0].capability_id == "my-cap:run"

    @pytest.mark.asyncio
    async def test_custom_overrides_builtin(self, engine: PlanningEngine):
        """Custom template for DIAGNOSE overrides built-in."""
        tmpl = GraphTemplate(
            id="my-diagnose",
            intent_type=IntentType.DIAGNOSE,
            name="Custom Diagnose",
            description="My custom diagnose",
            nodes=[{"id": "quick-check", "capability_id": "custom:quick-check"}],
        )
        engine.add_template(tmpl)
        retrieved = await engine.get_template(IntentType.DIAGNOSE)
        assert retrieved.id == "my-diagnose"

    @pytest.mark.asyncio
    async def test_remove_template(self, engine: PlanningEngine):
        tmpl = GraphTemplate(
            id="to-remove",
            intent_type=IntentType.CUSTOM,
            name="Remove me",
            description="will be removed",
        )
        engine.add_template(tmpl)
        engine.remove_template("to-remove")
        assert await engine.get_template(IntentType.CUSTOM) is None

    @pytest.mark.asyncio
    async def test_list_templates(self, engine: PlanningEngine):
        """list_templates returns all built-in + custom (deduplicated)."""
        tmpl_count_custom = len(engine._custom_templates)
        # 5 built-in + 0 custom = 5
        all_tmpls = engine.list_templates()
        # Deduplication: custom overrides built-in, so we expect all types
        assert len(all_tmpls) >= 5  # 5 built-in + maybe custom

    @pytest.mark.asyncio
    async def test_list_templates_with_custom(self, engine: PlanningEngine):
        """Custom template for existing type replaces built-in in list."""
        custom = GraphTemplate(
            id="custom-d",
            intent_type=IntentType.DIAGNOSE,
            name="Custom D",
            description="c",
        )
        engine.add_template(custom)
        all_tmpls = engine.list_templates()
        diagnose_templates = [t for t in all_tmpls if t.intent_type == IntentType.DIAGNOSE]
        # Only the custom one should appear
        assert len(diagnose_templates) == 1
        assert diagnose_templates[0].id == "custom-d"


# ======================================================================
#  Edge Cases & Error Handling
# ======================================================================


class TestEdgeCases:
    """PlanError, validation failures, edge cases."""

    @pytest.mark.asyncio
    async def test_plan_error_has_intent_id(self):
        err = PlanError("test error", intent_id="int-999")
        assert str(err) == "test error"
        assert err.intent_id == "int-999"

    @pytest.mark.asyncio
    async def test_plan_error_default_intent_id(self):
        err = PlanError("test error")
        assert err.intent_id == ""

    @pytest.mark.asyncio
    async def test_graph_valid_after_plan(
        self, engine: PlanningEngine, repair_intent: Intent
    ):
        graph = await engine.plan(repair_intent)
        errors = graph.validate()
        assert errors == []

    @pytest.mark.asyncio
    async def test_multiple_plans_independent(
        self, engine: PlanningEngine, basic_intent: Intent, repair_intent: Intent
    ):
        """Each plan() call produces a fresh, independent graph."""
        g1 = await engine.plan(basic_intent)
        g2 = await engine.plan(repair_intent)
        assert g1.id != g2.id
        assert len(g1.nodes) == 3   # diagnose has 3 nodes
        assert len(g2.nodes) == 6   # repair has 6 nodes

    @pytest.mark.asyncio
    async def test_correlation_id_preserved(
        self, engine: PlanningEngine, basic_intent: Intent
    ):
        graph = await engine.plan(basic_intent)
        assert graph.correlation_id == "corr-001"

    @pytest.mark.asyncio
    async def test_node_default_policies(self, engine: PlanningEngine):
        """Nodes inherit default RetryPolicy when template doesn't define one."""
        intent = Intent(
            id="int-def",
            type=IntentType.DIAGNOSE,
            target="svc",
            correlation_id="corr-def",
        )
        graph = await engine.plan(intent)
        for node in graph.nodes:
            assert isinstance(node.retry_policy, RetryPolicy)
            assert isinstance(node.compensation_policy, CompensationPolicy)

    @pytest.mark.asyncio
    async def test_node_custom_policies(self, engine: PlanningEngine):
        """Template-level retry policy propagates to nodes that don't override it."""
        intent = Intent(
            id="int-cust",
            type=IntentType.DEPLOY,
            target="provider:test",
            parameters={"version": "1.0", "workspace": "staging"},
            correlation_id="corr-cust",
        )
        graph = await engine.plan(intent)
        # deploy node has its own retry_policy = 3
        deploy = next(n for n in graph.nodes if n.id == "deploy")
        assert deploy.retry_policy.max_attempts == 3

    @pytest.mark.asyncio
    async def test_template_with_get_entry_exit(self):
        """Entry/exit node extraction with complex graph."""
        tmpl = GraphTemplate(
            intent_type=IntentType.DEPLOY,
            name="complex",
            description="complex graph",
            nodes=[
                {"id": "auth"},
                {"id": "validate"},
                {"id": "deploy"},
                {"id": "notify"},
            ],
            dependencies=[
                {"from": "auth", "to": "validate"},
                {"from": "auth", "to": "deploy"},
                {"from": "validate", "to": "deploy"},
                {"from": "deploy", "to": "notify"},
            ],
        )
        assert tmpl.get_entry_node_ids() == ["auth"]
        assert tmpl.get_exit_node_ids() == ["notify"]


# ======================================================================
#  Integration-style Tests
# ======================================================================


class TestPlanningIntegration:
    """End-to-end: Intent → Plan → Validated Graph."""

    @pytest.mark.asyncio
    async def test_diagnose_to_graph(self, engine: PlanningEngine):
        intent = Intent(
            type=IntentType.DIAGNOSE,
            target="service:api-gateway",
            correlation_id="int-diag-e2e",
        )
        graph = await engine.plan(intent)
        assert isinstance(graph, ExecutionGraph)
        assert len(graph.nodes) == 3
        assert graph.status == GraphStatus.CREATED
        assert graph.nodes[0].graph_id == graph.id
        assert graph.nodes[0].status == NodeStatus.PENDING

    @pytest.mark.asyncio
    async def test_repair_graph_structure(self, engine: PlanningEngine):
        intent = Intent(
            type=IntentType.REPAIR,
            target="provider:ollama",
            parameters={"deep_scan": True},
            correlation_id="int-repair-e2e",
        )
        graph = await engine.plan(intent)
        assert len(graph.nodes) == 6
        # Verify chain: diagnose → plan → approve → execute → verify
        node_map = graph.node_map
        assert node_map["diagnose"].dependencies == []
        assert "diagnose" in node_map["plan"].dependencies
        assert "plan" in node_map["approve"].dependencies
        assert "approve" in node_map["execute"].dependencies
        assert "execute" in node_map["verify"].dependencies
        # Rollback is separate (compensation-only)
        assert "rollback" in node_map
        assert node_map["rollback"].dependencies == []

    @pytest.mark.asyncio
    async def test_deploy_compensation_chain(self, engine: PlanningEngine):
        intent = Intent(
            type=IntentType.DEPLOY,
            target="provider:openai",
            parameters={"version": "4.0", "workspace": "prod"},
            correlation_id="int-deploy-e2e",
        )
        graph = await engine.plan(intent)
        deploy = graph.get_node("deploy")
        assert deploy is not None
        assert deploy.compensation_policy.compensation_node_id == "rollback"
        assert deploy.compensation_policy.on_failure == CompensationOnFailure.COMPENSATE

    @pytest.mark.asyncio
    async def test_scale_approval_required(self, engine: PlanningEngine):
        intent = Intent(
            type=IntentType.SCALE,
            target="cluster:web",
            parameters={"direction": "down", "count": 2},
            correlation_id="int-scale-e2e",
        )
        graph = await engine.plan(intent)
        assert graph.metadata.get("requires_approval") is True

    @pytest.mark.asyncio
    async def test_plan_with_intent_parameters_flow(
        self, engine: PlanningEngine, deploy_intent: Intent
    ):
        graph = await engine.plan(deploy_intent)
        deploy = graph.get_node("deploy")
        assert deploy is not None
        # Workspace parameter propagated to deploy inputs
        assert deploy.inputs.get("workspace") == "production"
        assert deploy.inputs.get("version") == "3.1.0"

    @pytest.mark.asyncio
    async def test_entry_exit_nodes_correct(self, engine: PlanningEngine, basic_intent: Intent):
        graph = await engine.plan(basic_intent)
        assert graph.entry_nodes == ["health-check"]
        assert graph.exit_nodes == ["report"]


# ======================================================================
#  Knowledge Store Error Resilience
# ======================================================================


class TestKnowledgeErrors:
    """Planning survives Knowledge Store errors gracefully."""

    @pytest.mark.asyncio
    async def test_search_raises_error(self, basic_intent: Intent):
        class _BrokenStore:
            async def search(self, query, limit=20):
                raise RuntimeError("DB down")

        engine = PlanningEngine(knowledge_store=_BrokenStore())
        graph = await engine.plan(basic_intent)
        # Planning still works, enrichment logs warning
        assert isinstance(graph, ExecutionGraph)
        assert "knowledge_facts" not in graph.metadata

    @pytest.mark.asyncio
    async def test_get_by_subject_raises_error(self, basic_intent: Intent):
        class _BrokenStore2:
            async def search(self, query, limit=20):
                return []

            async def get_by_subject(self, subject):
                raise RuntimeError("DB down")

        engine = PlanningEngine(knowledge_store=_BrokenStore2())
        graph = await engine.plan(basic_intent)
        assert isinstance(graph, ExecutionGraph)

    @pytest.mark.asyncio
    async def test_non_dict_facts(self, basic_intent: Intent, engine_with_knowledge, mock_knowledge):
        """Facts that aren't dicts are skipped gracefully."""
        mock_knowledge.search_results = [None, "string", 42]
        graph = await engine_with_knowledge.plan(basic_intent)
        assert isinstance(graph, ExecutionGraph)
        assert "knowledge_facts" not in graph.metadata or graph.metadata["knowledge_facts"] == []


# ======================================================================
#  Planner State Isolation
# ======================================================================


class TestStateIsolation:
    """Each plan() call does not mutate shared state."""

    @pytest.mark.asyncio
    async def test_consecutive_plans_different_graphs(
        self, engine: PlanningEngine
    ):
        ids = set()
        for i in range(3):
            intent = Intent(
                type=IntentType.DIAGNOSE,
                target=f"svc-{i}",
                correlation_id=f"corr-{i}",
            )
            graph = await engine.plan(intent)
            ids.add(graph.id)
        assert len(ids) == 3

    @pytest.mark.asyncio
    async def test_same_intent_creates_different_graphs(self, engine: PlanningEngine):
        """Even with identical input, each plan creates a unique graph."""
        intent = Intent(
            type=IntentType.DIAGNOSE,
            target="svc",
            correlation_id="corr",
        )
        g1 = await engine.plan(intent)
        g2 = await engine.plan(intent)
        assert g1.id != g2.id
        # Nodes have same IDs (from template) but different graph_ids
        assert g1.nodes[0].id == g2.nodes[0].id
        assert g1.nodes[0].graph_id != g2.nodes[0].graph_id
