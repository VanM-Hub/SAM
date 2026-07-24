"""
Governance Evaluator Interface – Sprint 21

Defines the Evaluator abstract base class and BaseEvaluator
convenience class that evaluators extend.
"""

from __future__ import annotations

import structlog
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .models import GovernanceResult

if TYPE_CHECKING:
    from ..execution.graph import ExecutionGraph
    from ..runtime.context import ExecutionContext


class Evaluator(ABC):
    """
    Abstract interface for governance evaluators.

    Each evaluator examines an execution graph (and optionally its context)
    and returns a GovernanceResult with a decision.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique evaluator name (e.g. 'risk', 'approval', 'maintenance')."""
        ...

    @abstractmethod
    async def evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        """
        Evaluate the given execution graph.

        Args:
            graph: The execution graph to evaluate.
            context: Current execution context.

        Returns:
            GovernanceResult with decision, reason, warnings, etc.
        """
        ...


class BaseEvaluator(Evaluator):
    """
    Convenience base class with logging and error handling.

    Subclasses override _do_evaluate() instead of evaluate().
    The base evaluate() wraps the call with logging and converts
    exceptions into REJECT decisions so one failing evaluator
    does not crash the engine.
    """

    def __init__(self) -> None:
        self._logger = structlog.get_logger()

    async def evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        self._logger.debug(
            "evaluator_started",
            evaluator=self.name,
            graph_id=graph.id,
        )
        try:
            result = await self._do_evaluate(graph, context)
            self._logger.debug(
                "evaluator_result",
                evaluator=self.name,
                decision=result.decision.value,
                reason=result.reason,
            )
            return result
        except Exception as exc:
            self._logger.error(
                "evaluator_error",
                evaluator=self.name,
                error=str(exc),
            )
            return GovernanceResult.rejected(
                reason=f"Evaluator '{self.name}' failed: {exc}",
            )

    @abstractmethod
    async def _do_evaluate(
        self,
        graph: "ExecutionGraph",
        context: "ExecutionContext",
    ) -> GovernanceResult:
        """Actual evaluation logic — override in subclasses."""
        ...
