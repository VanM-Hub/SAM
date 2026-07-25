"""
Reasoning Engine – Sprint 22 Fase 3

Orchestrates the complete pipeline:
  Intent text → IntentParser → Intent → PlanningEngine → ExecutionGraph
  → (optional) Governance → (optional) Execution → GraphResult

Integrates directly with Daemon and CLI.
"""

from __future__ import annotations

import uuid
import structlog
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .intent import Intent, IntentParser, IntentType, IntentStatus
from .planner import PlanningEngine, PlanError
from ..execution.graph import ExecutionGraph, GraphStatus
from ..execution.engine import ExecutionGraphEngine, GraphResult, NodeResult

logger = structlog.get_logger()


class ReasoningResult:
    """Result of the reasoning pipeline at any stage.

    Contains the intent, graph, and optional execution result,
    allowing callers to inspect output at any level of detail.
    """

    def __init__(
        self,
        intent: Intent,
        graph: Optional[ExecutionGraph] = None,
        governance_blocked: bool = False,
        governance_decision: Optional[str] = None,
        graph_result: Optional[GraphResult] = None,
        error: Optional[str] = None,
    ) -> None:
        self.intent = intent
        self.graph = graph
        self.governance_blocked = governance_blocked
        self.governance_decision = governance_decision
        self.graph_result = graph_result
        self.error = error

    @property
    def success(self) -> bool:
        """True if the pipeline completed without errors."""
        return self.error is None and not self.governance_blocked

    def to_dict(self) -> Dict[str, Any]:
        """Compact dict representation for CLI output."""
        d: Dict[str, Any] = {
            "intent": {
                "id": self.intent.id,
                "type": self.intent.type.value,
                "target": self.intent.target,
                "status": self.intent.status.value,
            },
        }
        if self.graph:
            d["graph"] = {
                "id": self.graph.id,
                "name": self.graph.name,
                "node_count": len(self.graph.nodes),
                "status": self.graph.status.value,
            }
        if self.governance_blocked:
            d["governance"] = {
                "blocked": True,
                "decision": self.governance_decision,
            }
        if self.graph_result:
            d["execution"] = {
                "status": self.graph_result.status.value,
                "duration_ms": self.graph_result.duration_ms,
                "node_count": len(self.graph_result.node_results),
            }
        if self.error:
            d["error"] = self.error
        return d


class ReasoningEngine:
    """Coordination layer: Intent → Plan → Governance → Execute.

    All public methods are async and ready for integration into
    RuntimeDaemon, CLI, or API servers.

    Usage:
        engine = ReasoningEngine()
        result = await engine.reason("diagnose provider:nvidia")
        print(result.graph.name)
    """

    def __init__(
        self,
        intent_parser: Optional[IntentParser] = None,
        planning_engine: Optional[PlanningEngine] = None,
        execution_engine: Optional[ExecutionGraphEngine] = None,
        governance_engine: Any = None,
        knowledge_store: Any = None,
    ) -> None:
        self._intent_parser = intent_parser or IntentParser()
        self._planning_engine = planning_engine or PlanningEngine(
            knowledge_store=knowledge_store,
        )
        self._execution_engine = execution_engine or ExecutionGraphEngine()
        self._governance_engine = governance_engine
        self._knowledge_store = knowledge_store
        self._logger = logger.bind(component="ReasoningEngine")

    # ── Public API ────────────────────────────────────────────────

    async def reason(self, text: str) -> ReasoningResult:
        """Full pipeline: text → Intent → Plan → Graph.

        Does NOT execute or run governance. Returns the planned graph
        for inspection or approval.

        Args:
            text: Natural language intent description.

        Returns:
            ReasoningResult with intent and planned graph (if successful).
        """
        self._logger.info("reason.start", text=text[:120])

        # 1. Parse intent
        try:
            intent = await self._intent_parser.parse(text)
        except Exception as exc:
            self._logger.error("reason.parse_failed", error=str(exc))
            return ReasoningResult(
                intent=Intent(type=IntentType.CUSTOM, target="", description=text),
                error=f"Failed to parse intent: {exc}",
            )

        self._logger.debug("reason.intent_parsed", intent_type=intent.type.value, target=intent.target)

        # 2. Plan graph
        try:
            graph = await self._planning_engine.plan(intent)
        except PlanError as exc:
            self._logger.error("reason.plan_failed", error=str(exc))
            return ReasoningResult(
                intent=intent,
                error=f"Failed to plan: {exc}",
            )
        except Exception as exc:
            self._logger.error("reason.plan_crashed", error=str(exc))
            return ReasoningResult(
                intent=intent,
                error=f"Planning crashed: {exc}",
            )

        intent.status = IntentStatus.PLANNING
        self._logger.info(
            "reason.complete",
            intent_id=intent.id,
            graph_id=graph.id,
            node_count=len(graph.nodes),
        )
        return ReasoningResult(intent=intent, graph=graph)

    async def reason_and_execute(
        self,
        text: str,
        context: Any = None,
    ) -> ReasoningResult:
        """Full pipeline: text → Intent → Plan → Governance → Execute.

        Args:
            text: Natural language intent description.
            context: Optional ExecutionContext for governance and execution.

        Returns:
            ReasoningResult with intent, graph, governance result, and
            execution result.
        """
        # 1. Reason (parse + plan)
        result = await self.reason(text)
        if result.error:
            return result

        if not result.graph:
            return ReasoningResult(
                intent=result.intent,
                error="No graph produced (empty template?)",
            )

        intent = result.intent
        graph = result.graph

        # 2. Governance gate
        if self._governance_engine:
            try:
                gate_result = await self._governance_engine.evaluate(
                    graph, context or {},
                )
            except Exception as exc:
                self._logger.error("reason.governance_crashed", error=str(exc))
                return ReasoningResult(
                    intent=intent,
                    graph=graph,
                    error=f"Governance crashed: {exc}",
                )

            if gate_result.is_blocked():
                self._logger.warning(
                    "reason.governance_blocked",
                    decision=gate_result.decision.value,
                    reason=gate_result.reason,
                )
                return ReasoningResult(
                    intent=intent,
                    graph=graph,
                    governance_blocked=True,
                    governance_decision=gate_result.decision.value,
                    error=gate_result.reason,
                )

        # 3. Execute
        intent.status = IntentStatus.EXECUTING
        try:
            graph_result = await self._execution_engine.execute(graph)
        except Exception as exc:
            self._logger.error("reason.execution_failed", error=str(exc))
            return ReasoningResult(
                intent=intent,
                graph=graph,
                error=f"Execution failed: {exc}",
            )

        self._logger.info(
            "reason_and_execute.complete",
            intent_id=intent.id,
            graph_id=graph.id,
            execution_status=graph_result.status.value,
            duration_ms=graph_result.duration_ms,
        )

        return ReasoningResult(
            intent=intent,
            graph=graph,
            graph_result=graph_result,
        )

    async def parse_intent(self, text: str) -> Intent:
        """Parse text into an Intent without planning or executing.

        Args:
            text: Natural language intent description.

        Returns:
            Parsed Intent (may have type=CUSTOM if no keywords match).
        """
        return await self._intent_parser.parse(text)

    # ── Accessors ─────────────────────────────────────────────────

    @property
    def planning_engine(self) -> PlanningEngine:
        return self._planning_engine

    @property
    def execution_engine(self) -> ExecutionGraphEngine:
        return self._execution_engine

    @property
    def governance_engine(self) -> Any:
        return self._governance_engine
