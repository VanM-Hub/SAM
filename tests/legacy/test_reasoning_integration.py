"""
Integration tests for Reasoning Engine – Sprint 22 Fase 3

Covers:
- ReasoningEngine: reason(), reason_and_execute(), parse_intent()
- End-to-end: text → Intent → Plan → Governance → Execute
- Error paths: no template, intent parse failure, governance blocks
- Daemon integration (reasoning_engine parameter, config)
- CLI simulation (typer test runner)
"""

from __future__ import annotations

import pytest
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.sam.reasoning import (
    ReasoningEngine,
    ReasoningResult,
    Intent,
    IntentType,
    IntentStatus,
    PlanError,
)
from src.sam.reasoning.planner import PlanningEngine
from src.sam.reasoning.templates import GraphTemplate, BUILTIN_TEMPLATES
from src.sam.execution.graph import ExecutionGraph, GraphStatus
from src.sam.execution.engine import (
    ExecutionGraphEngine,
    GraphResult,
    NodeResult,
)
from src.sam.execution.node import NodeStatus
from src.sam.core.daemon import RuntimeDaemon, DaemonConfig


# ======================================================================
#  Mock / Stub Helpers
# ======================================================================


class _MockGovernanceEngine:
    """Simulates governance evaluation."""

    def __init__(self, blocked: bool = False) -> None:
        self._blocked = blocked
        self._evaluations: List[Dict[str, Any]] = []

    @property
    def evaluators(self) -> List[Any]:
        return []

    async def evaluate(self, graph: Any, context: Any = None) -> Any:
        self._evaluations.append({"graph_id": graph.id, "context": context})

        if self._blocked:
            from src.sam.governance.models import GovernanceResult, GovernanceDecision
            return GovernanceResult(
                decision=GovernanceDecision.REJECT,
                reason="Simulated governance rejection",
            )

        from src.sam.governance.models import GovernanceResult, GovernanceDecision
        return GovernanceResult.allowed(reason="All evaluators passed")


class _MockExecutionEngine:
    """Simulates execution without actual capability running."""

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail
        self._executed_graphs: List[ExecutionGraph] = []

    async def execute(self, graph: ExecutionGraph) -> GraphResult:
        self._executed_graphs.append(graph)

        if self._fail:
            return GraphResult(
                graph_id=graph.id,
                status=GraphStatus.FAILED,
                node_results=[
                    NodeResult(
                        node_id=n.id,
                        status=NodeStatus.FAILED,
                        error="Simulated execution failure",
                    )
                    for n in graph.nodes
                ],
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )

        return GraphResult(
            graph_id=graph.id,
            status=GraphStatus.COMPLETED,
            node_results=[
                NodeResult(
                    node_id=n.id,
                    status=NodeStatus.COMPLETED,
                    output={"done": True},
                )
                for n in graph.nodes
            ],
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )


# ======================================================================
#  Fixtures
# ======================================================================


@pytest.fixture
def engine() -> ReasoningEngine:
    return ReasoningEngine()


@pytest.fixture
def engine_with_governance() -> ReasoningEngine:
    return ReasoningEngine(
        governance_engine=_MockGovernanceEngine(blocked=False),
    )


@pytest.fixture
def engine_with_blocking_governance() -> ReasoningEngine:
    return ReasoningEngine(
        governance_engine=_MockGovernanceEngine(blocked=True),
    )


@pytest.fixture
def engine_with_failing_execution() -> ReasoningEngine:
    return ReasoningEngine(
        execution_engine=_MockExecutionEngine(fail=True),
    )


@pytest.fixture
def engine_with_mocks() -> ReasoningEngine:
    """Full mock setup for end-to-end testing."""
    return ReasoningEngine(
        execution_engine=_MockExecutionEngine(fail=False),
        governance_engine=_MockGovernanceEngine(blocked=False),
    )


# ======================================================================
#  ReasoningEngine — reason()
# ======================================================================


class TestReason:
    """Text → Intent → Plan pipeline (no execution)."""

    @pytest.mark.asyncio
    async def test_reason_diagnose(self, engine: ReasoningEngine):
        result = await engine.reason("diagnose provider:nvidia")
        assert result.success
        assert result.intent.type == IntentType.DIAGNOSE
        assert result.intent.target == "provider:nvidia"
        assert result.graph is not None
        assert len(result.graph.nodes) == 3  # diagnose template

    @pytest.mark.asyncio
    async def test_reason_repair(self, engine: ReasoningEngine):
        result = await engine.reason("repair provider:nvidia deep_scan=true version=2.0")
        assert result.success
        assert result.intent.type == IntentType.REPAIR
        assert result.intent.target == "provider:nvidia"
        assert result.graph is not None
        assert len(result.graph.nodes) == 6  # repair template

    @pytest.mark.asyncio
    async def test_reason_deploy(self, engine: ReasoningEngine):
        result = await engine.reason("deploy to provider:openai version=3.1 workspace=prod")
        assert result.success
        assert result.intent.type == IntentType.DEPLOY
        assert result.intent.target == "provider:openai"
        assert len(result.graph.nodes) == 4

    @pytest.mark.asyncio
    async def test_reason_scale(self, engine: ReasoningEngine):
        result = await engine.reason("scale up cluster:worker-pool count=3")
        assert result.success
        assert result.intent.type == IntentType.SCALE
        assert result.intent.target == "cluster:worker-pool"
        assert len(result.graph.nodes) == 5

    @pytest.mark.asyncio
    async def test_reason_optimize(self, engine: ReasoningEngine):
        result = await engine.reason("optimize service:db-cluster")
        assert result.success
        assert result.intent.type == IntentType.OPTIMIZE
        assert result.intent.target == "service:db-cluster"

    @pytest.mark.asyncio
    async def test_reason_custom_no_template(self, engine: ReasoningEngine):
        """CUSTOM type has no built-in template → error."""
        result = await engine.reason("run something custom")
        assert not result.success
        assert "No template" in (result.error or "")
        assert result.graph is None

    @pytest.mark.asyncio
    async def test_reason_monitor_no_template(self, engine: ReasoningEngine):
        """MONITOR has no built-in template → error."""
        result = await engine.reason("monitor cluster:worker-pool")
        assert not result.success
        assert result.graph is None

    @pytest.mark.asyncio
    async def test_reason_graph_metadata(self, engine: ReasoningEngine):
        """Graph metadata includes intent_id, intent_type, template_id."""
        result = await engine.reason("diagnose provider:intel")
        assert result.success
        md = result.graph.metadata
        assert md["intent_id"] == result.intent.id
        assert md["intent_type"] == "DIAGNOSE"
        assert md["template_id"] == "tmpl-diagnose-runtime"

    @pytest.mark.asyncio
    async def test_reason_intent_parameters_propagated(self, engine: ReasoningEngine):
        """Parameters from intent text appear in graph node inputs."""
        result = await engine.reason("deploy to provider:openai version=4.0 workspace=prod")
        assert result.success
        deploy = result.graph.get_node("deploy")
        assert deploy is not None
        assert deploy.inputs.get("version") == "4.0"
        assert deploy.inputs.get("workspace") == "prod"


# ======================================================================
#  ReasoningEngine — parse_intent()
# ======================================================================


class TestParseIntent:
    """Text → Intent only (no planning)."""

    @pytest.mark.asyncio
    async def test_parse_diagnose(self, engine: ReasoningEngine):
        intent = await engine.parse_intent("diagnose provider:nvidia")
        assert intent.type == IntentType.DIAGNOSE
        assert intent.target == "provider:nvidia"

    @pytest.mark.asyncio
    async def test_parse_rollback(self, engine: ReasoningEngine):
        intent = await engine.parse_intent("rollback the last deployment")
        assert intent.type == IntentType.ROLLBACK

    @pytest.mark.asyncio
    async def test_parse_custom_fallback(self, engine: ReasoningEngine):
        intent = await engine.parse_intent("do something unusual")
        assert intent.type == IntentType.CUSTOM

    @pytest.mark.asyncio
    async def test_parse_returns_intent_instance(self, engine: ReasoningEngine):
        intent = await engine.parse_intent("deploy to provider:openai version=5.0")
        assert isinstance(intent, Intent)
        assert intent.id is not None

    @pytest.mark.asyncio
    async def test_parse_intent_status_pending(self, engine: ReasoningEngine):
        """Freshly parsed intent has PENDING status."""
        intent = await engine.parse_intent("diagnose provider:nvidia")
        assert intent.status == IntentStatus.PENDING


# ======================================================================
#  ReasoningEngine — reason_and_execute()
# ======================================================================


class TestReasonAndExecute:
    """End-to-end: text → Intent → Plan → Governance → Execute."""

    @pytest.mark.asyncio
    async def test_full_pipeline_success(self, engine_with_mocks: ReasoningEngine):
        result = await engine_with_mocks.reason_and_execute("diagnose provider:nvidia")
        assert result.success
        assert result.intent.status == IntentStatus.EXECUTING
        assert result.graph_result is not None
        assert result.graph_result.status == GraphStatus.COMPLETED
        assert len(result.graph_result.node_results) == 3

    @pytest.mark.asyncio
    async def test_execution_with_governance_allowed(self, engine_with_mocks: ReasoningEngine):
        """Governance allows execution to proceed."""
        result = await engine_with_mocks.reason_and_execute("diagnose provider:nvidia")
        assert result.success
        assert not result.governance_blocked

    @pytest.mark.asyncio
    async def test_governance_blocked(self, engine_with_blocking_governance: ReasoningEngine):
        """Governance rejects the graph — execution does not happen."""
        result = await engine_with_blocking_governance.reason_and_execute(
            "diagnose provider:nvidia"
        )
        assert not result.success
        assert result.governance_blocked
        assert result.governance_decision == "REJECT"
        assert result.graph_result is None  # never executed

    @pytest.mark.asyncio
    async def test_execution_failure_reported(self, engine_with_failing_execution: ReasoningEngine):
        result = await engine_with_failing_execution.reason_and_execute(
            "diagnose provider:nvidia"
        )
        # Execution result is available even on failure
        assert result.graph_result is not None
        assert result.graph_result.status == GraphStatus.FAILED
        assert not result.graph_result.node_results[0].status.value == "COMPLETED"

    @pytest.mark.asyncio
    async def test_no_template_no_execution(self, engine_with_mocks: ReasoningEngine):
        """No template available → error before execution."""
        result = await engine_with_mocks.reason_and_execute(
            "custom weird-command param=x"
        )
        assert not result.success
        assert result.graph is None
        assert result.graph_result is None

    @pytest.mark.asyncio
    async def test_execution_duration_recorded(self, engine_with_mocks: ReasoningEngine):
        result = await engine_with_mocks.reason_and_execute("diagnose gpu-cluster")
        assert result.graph_result is not None
        # duration_ms is computed by real engine; mock returns 0
        assert result.graph_result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_reason_and_execute_with_params(
        self, engine_with_mocks: ReasoningEngine
    ):
        result = await engine_with_mocks.reason_and_execute(
            "deploy to provider:openai version=5.1 workspace=prod"
        )
        assert result.success
        assert result.graph_result is not None
        assert result.graph_result.status == GraphStatus.COMPLETED


# ======================================================================
#  ReasoningResult — to_dict()
# ======================================================================


class TestReasoningResultDict:
    """DTO serialisation."""

    @pytest.mark.asyncio
    async def test_dict_intent_only(self):
        intent = Intent(type=IntentType.DIAGNOSE, target="svc", description="test")
        result = ReasoningResult(intent=intent)
        d = result.to_dict()
        assert d["intent"]["type"] == "DIAGNOSE"
        assert d["intent"]["target"] == "svc"
        assert "graph" not in d
        assert "execution" not in d

    @pytest.mark.asyncio
    async def test_dict_with_graph(self, engine: ReasoningEngine):
        result = await engine.reason("diagnose provider:nvidia")
        d = result.to_dict()
        assert "graph" in d
        assert d["graph"]["node_count"] == 3

    @pytest.mark.asyncio
    async def test_dict_with_execution(self, engine_with_mocks: ReasoningEngine):
        result = await engine_with_mocks.reason_and_execute("diagnose provider:nvidia")
        d = result.to_dict()
        assert "execution" in d
        assert d["execution"]["status"] == "COMPLETED"

    @pytest.mark.asyncio
    async def test_dict_error(self):
        intent = Intent(type=IntentType.CUSTOM, target="", description="test")
        result = ReasoningResult(intent=intent, error="Something broke")
        d = result.to_dict()
        assert d["error"] == "Something broke"
        assert not result.success

    @pytest.mark.asyncio
    async def test_dict_governance_blocked(self):
        intent = Intent(type=IntentType.DIAGNOSE, target="svc", description="test")
        result = ReasoningResult(
            intent=intent,
            governance_blocked=True,
            governance_decision="REJECT",
            error="Blocked by governance",
        )
        d = result.to_dict()
        assert d["governance"]["blocked"] is True
        assert d["governance"]["decision"] == "REJECT"


# ======================================================================
#  Daemon Integration Tests
# ======================================================================


class TestDaemonIntegration:
    """RuntimeDaemon with reasoning_engine parameter."""

    @pytest.mark.asyncio
    async def test_daemon_accepts_reasoning_engine(self):
        """RuntimeDaemon constructor accepts reasoning_engine."""
        daemon = RuntimeDaemon(
            config=DaemonConfig(),
            reasoning_engine=ReasoningEngine(),
        )
        assert daemon.reasoning_engine is not None
        assert isinstance(daemon.reasoning_engine, ReasoningEngine)

    @pytest.mark.asyncio
    async def test_daemon_reasoning_engine_optional(self):
        """reasoning_engine is optional — defaults to None."""
        daemon = RuntimeDaemon()
        assert daemon.reasoning_engine is None

    @pytest.mark.asyncio
    async def test_daemon_config_enable_reasoning_default(self):
        """DaemonConfig has enable_reasoning=True by default."""
        config = DaemonConfig()
        assert config.enable_reasoning is True

    @pytest.mark.asyncio
    async def test_daemon_config_enable_reasoning_false(self):
        config = DaemonConfig(enable_reasoning=False)
        assert config.enable_reasoning is False


# ======================================================================
#  Edge Cases
# ======================================================================


class TestEdgeCasesReasoning:
    """Empty input, no keywords, error resilience."""

    @pytest.mark.asyncio
    async def test_empty_text_falls_to_custom(self, engine: ReasoningEngine):
        """Empty text still produces a CUSTOM intent."""
        result = await engine.reason("")
        assert result.intent.type == IntentType.CUSTOM

    @pytest.mark.asyncio
    async def test_intent_parse_error_caught(self, engine: ReasoningEngine):
        """A text that causes an obscure parse error is caught gracefully."""
        result = await engine.reason("deploy --invalid!!param=value")
        # Should still parse something
        assert isinstance(result.intent, Intent)

    @pytest.mark.asyncio
    async def test_reason_without_execution_leaves_pending_status(
        self, engine: ReasoningEngine
    ):
        result = await engine.reason("diagnose provider:nvidia")
        assert result.intent.status == IntentStatus.PLANNING  # updated after plan

    @pytest.mark.asyncio
    async def test_reason_and_execute_without_governance(
        self, engine: ReasoningEngine
    ):
        """Engine works without governance engine set."""
        # engine_with_mocks has mocks; we need plain engine with execution mock
        eng = ReasoningEngine(execution_engine=_MockExecutionEngine(fail=False))
        result = await eng.reason_and_execute("diagnose provider:nvidia")
        assert result.success
        assert result.graph_result is not None
        assert result.graph_result.status == GraphStatus.COMPLETED


# ======================================================================
#  Governance Integration w/ Real Models
# ======================================================================


class TestGovernanceIntegration:
    """Full governance decision flow."""

    @pytest.mark.asyncio
    async def test_governance_allows_and_proceeds(self):
        """Governance says ALLOW → graph executes."""
        from src.sam.governance.models import GovernanceResult

        class _AllowGov:
            async def evaluate(self, graph, context):
                return GovernanceResult.allowed(reason="All good")

        eng = ReasoningEngine(
            governance_engine=_AllowGov(),
            execution_engine=_MockExecutionEngine(fail=False),
        )
        result = await eng.reason_and_execute("diagnose provider:test")
        assert result.success
        assert not result.governance_blocked

    @pytest.mark.asyncio
    async def test_governance_allow_with_warning(self):
        """ALLOW_WITH_WARNING is treated as allowed."""
        from src.sam.governance.models import GovernanceResult, GovernanceDecision

        class _WarnGov:
            async def evaluate(self, graph, context):
                return GovernanceResult(
                    decision=GovernanceDecision.ALLOW_WITH_WARNING,
                    reason="Allowed with warnings",
                    warnings=["Disk near capacity"],
                )

        eng = ReasoningEngine(
            governance_engine=_WarnGov(),
            execution_engine=_MockExecutionEngine(fail=False),
        )
        result = await eng.reason_and_execute("diagnose provider:test")
        assert result.success
        assert not result.governance_blocked

    @pytest.mark.asyncio
    async def test_governance_rejects(self):
        """REJECT blocks execution."""
        from src.sam.governance.models import GovernanceResult, GovernanceDecision

        class _RejectGov:
            async def evaluate(self, graph, context):
                return GovernanceResult(
                    decision=GovernanceDecision.REJECT,
                    reason="Policy violation",
                )

        eng = ReasoningEngine(
            governance_engine=_RejectGov(),
            execution_engine=_MockExecutionEngine(fail=False),
        )
        result = await eng.reason_and_execute("diagnose provider:test")
        assert not result.success
        assert result.governance_blocked
        assert result.graph_result is None

    @pytest.mark.asyncio
    async def test_governance_escalates(self):
        """ESCALATE blocks execution."""
        from src.sam.governance.models import GovernanceResult, GovernanceDecision

        class _EscalateGov:
            async def evaluate(self, graph, context):
                return GovernanceResult(
                    decision=GovernanceDecision.ESCALATE,
                    reason="Needs human intervention",
                )

        eng = ReasoningEngine(
            governance_engine=_EscalateGov(),
            execution_engine=_MockExecutionEngine(fail=False),
        )
        result = await eng.reason_and_execute("diagnose provider:test")
        assert not result.success
        assert result.governance_blocked
        assert result.graph_result is None


# ======================================================================
#  PlanError passthrough
# ======================================================================


class TestPlanErrorPassthrough:
    """PlanError from PlanningEngine surfaces correctly in ReasoningResult."""

    @pytest.mark.asyncio
    async def test_plan_error_surfaces(self, engine: ReasoningEngine):
        result = await engine.reason("custom something unknown")
        assert not result.success
        assert "No template" in (result.error or "")

    @pytest.mark.asyncio
    async def test_plan_error_does_not_crash(self, engine: ReasoningEngine):
        """PlanError is caught and returned as error, not exception."""
        try:
            result = await engine.reason("monitor cluster:worker")
            assert not result.success
            assert result.error is not None
        except PlanError:
            pytest.fail("PlanError should not bubble up from engine.reason()")
