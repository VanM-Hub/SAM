"""Self-Optimization Engine — Sprint 28 Fase 1.

Analyzes historical performance data (success rate, duration, cost)
from InstitutionalMemory and suggests parameter optimizations.
Supports applying, rolling back, and tracking optimization history.
"""

from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database
from sam.institutional.memory import InstitutionalMemory, InstitutionalMemoryManager
from sam.evolution.params import OptimizableParam, ParamManager


logger = structlog.get_logger()


class OptimizationGoal(Enum):
    """Goal for the self-optimization analysis."""
    MINIMIZE_DURATION = "minimize_duration"
    MAXIMIZE_SUCCESS_RATE = "maximize_success_rate"
    MINIMIZE_COST = "minimize_cost"
    BALANCED = "balanced"


@dataclass
class OptimizationSuggestion:
    """A single parameter optimization suggestion.

    Attributes:
        param_name: Name of the parameter to adjust.
        current_value: Current parameter value.
        suggested_value: Proposed new value.
        expected_improvement: Expected improvement percentage (0.0–100.0).
        confidence: Confidence score (0.0–1.0) based on supporting evidence.
        evidence: List of evidence identifiers backing the suggestion.
    """
    param_name: str
    current_value: Any
    suggested_value: Any
    expected_improvement: float
    confidence: float
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "param_name": self.param_name,
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
            "expected_improvement": self.expected_improvement,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


class SelfOptimizer:
    """Self-optimization engine that analyzes historical performance
    and suggests or applies parameter adjustments.

    Uses InstitutionalMemory for historical data and ParamManager
    for parameter CRUD and version tracking.
    """

    def __init__(
        self,
        institutional_memory: InstitutionalMemoryManager,
        param_manager: ParamManager,
    ) -> None:
        self.memory = institutional_memory
        self.params = param_manager
        self.db = param_manager.db  # shared DB connection
        self.logger = logger.bind(component="SelfOptimizer")

    async def analyze(
        self, goal: OptimizationGoal
    ) -> List[OptimizationSuggestion]:
        """Analyze historical data and generate optimization suggestions.

        Examines institutional memory entries (KNOWLEDGE, PATTERN, LESSON)
        and computes suggested parameter adjustments aligned with the goal.

        Returns a list of OptimizationSuggestion objects, ordered by
        expected_improvement descending.
        """
        suggestions: List[OptimizationSuggestion] = []

        all_params = await self.params.list()

        if goal == OptimizationGoal.MAXIMIZE_SUCCESS_RATE:
            suggestions = await self._analyze_success_rate(all_params)
        elif goal == OptimizationGoal.MINIMIZE_DURATION:
            suggestions = await self._analyze_duration(all_params)
        elif goal == OptimizationGoal.MINIMIZE_COST:
            suggestions = await self._analyze_cost(all_params)
        elif goal == OptimizationGoal.BALANCED:
            sr = await self._analyze_success_rate(all_params)
            dur = await self._analyze_duration(all_params)
            cost = await self._analyze_cost(all_params)
            suggestions = self._merge_suggestions(sr, dur, cost)

        suggestions.sort(key=lambda s: s.expected_improvement, reverse=True)
        return suggestions

    async def apply_suggestion(
        self, suggestion: OptimizationSuggestion
    ) -> str:
        """Apply an optimization suggestion.

        Records the change in optimizable_params + writes an entry
        to optimization_history. Returns the history entry ID.
        """
        param = await self.params.get(suggestion.param_name)
        if param is None:
            raise ValueError(
                f"Cannot apply suggestion: parameter "
                f"'{suggestion.param_name}' not found"
            )

        old_value = param.current_value
        await self.params.set(suggestion.param_name, suggestion.suggested_value)

        history_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            """INSERT INTO optimization_history
               (id, param_name, old_value, new_value, reason,
                evidence, confidence, applied_at, success_metric)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                history_id,
                suggestion.param_name,
                json.dumps(old_value),
                json.dumps(suggestion.suggested_value),
                f"Auto-optimization targeting improvement of "
                f"{suggestion.expected_improvement:.1f}%",
                json.dumps(suggestion.evidence),
                suggestion.confidence,
                now,
                None,  # success_metric unknown at apply time
            ),
        )

        self.logger.info(
            "Optimization applied",
            param_name=suggestion.param_name,
            old_value=old_value,
            new_value=suggestion.suggested_value,
            confidence=suggestion.confidence,
        )
        return history_id

    async def get_optimization_history(
        self, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve recent optimization history."""
        rows = await self.db.fetch_all(
            "SELECT * FROM optimization_history ORDER BY applied_at DESC LIMIT ?",
            (limit,),
        )
        result = []
        for r in rows:
            d = dict(r)
            d["old_value"] = _parse_json(d["old_value"])
            d["new_value"] = _parse_json(d["new_value"])
            d["evidence"] = _parse_json(d["evidence"])
            result.append(d)
        return result

    async def rollback(self, param_name: str, version: int = 0) -> str:
        """Rollback a parameter to a previous version.

        Args:
            param_name: Name of the parameter to rollback.
            version: Index into history (0 = most recent). Default 0.

        Returns:
            History ID of the rollback entry.

        Raises:
            ValueError: If no history entries exist for the parameter
                        or the version index is out of range.
        """
        rows = await self.db.fetch_all(
            "SELECT * FROM optimization_history WHERE param_name = ? "
            "ORDER BY applied_at DESC",
            (param_name,),
        )
        if not rows:
            raise ValueError(
                f"No optimization history found for '{param_name}'"
            )
        if version < 0 or version >= len(rows):
            raise ValueError(
                f"Version index {version} out of range "
                f"(0-{len(rows) - 1} for '{param_name}')"
            )

        entry = dict(rows[version])
        rollback_value = _parse_json(entry["old_value"])

        # Save current before rollback as a new history entry
        current_param = await self.params.get(param_name)
        if current_param is None:
            raise ValueError(f"Parameter '{param_name}' not found")

        old_value = current_param.current_value
        await self.params.set(param_name, rollback_value)

        history_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            """INSERT INTO optimization_history
               (id, param_name, old_value, new_value, reason,
                evidence, confidence, applied_at, success_metric)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                history_id,
                param_name,
                json.dumps(old_value),
                json.dumps(rollback_value),
                f"Rollback to version {version} (history entry {entry['id']})",
                json.dumps([]),
                1.0,
                now,
                None,
            ),
        )

        self.logger.info(
            "Parameter rolled back",
            param_name=param_name,
            version=version,
            restored_value=rollback_value,
        )
        return history_id

    # ── Internal analysis helpers ────────────────────────────────────

    async def _analyze_success_rate(
        self, params: List[OptimizableParam]
    ) -> List[OptimizationSuggestion]:
        """Analyze for maximizing success rate."""
        suggestions: List[OptimizationSuggestion] = []

        # Gather success rate data from institutional memory
        patterns = await self.memory.search({"type": "PATTERN", "min_confidence": 0.5})
        lessons = await self._get_lessons_as_memory()

        total_rate = self._compute_avg_success_rate(patterns + lessons)
        self.logger.debug(
            "Success rate analysis",
            entries=len(patterns) + len(lessons),
            avg_success_rate=total_rate,
        )

        # Suggest retry adjustments based on observed failure rate
        if total_rate < 0.7:
            retry_param = next(
                (p for p in params if p.name == "retry.max_attempts"), None
            )
            if retry_param and isinstance(retry_param.current_value, (int, float)):
                if retry_param.current_value < (retry_param.max_value or 10):
                    suggested = min(
                        retry_param.current_value + 1,
                        retry_param.max_value or 10,
                    )
                    improvement = (1.0 - total_rate) * 20.0  # scale
                    suggestions.append(OptimizationSuggestion(
                        param_name="retry.max_attempts",
                        current_value=retry_param.current_value,
                        suggested_value=suggested,
                        expected_improvement=round(improvement, 1),
                        confidence=0.5 + (1.0 - total_rate) * 0.3,
                        evidence=[
                            m.id for m in (patterns + lessons)[:5]
                            if m.failure_count > m.success_count
                        ],
                    ))

        # Suggest success_probability weight increase
        weight_param = next(
            (p for p in params if p.name == "ranking.weights.success_probability"), None
        )
        if weight_param and isinstance(weight_param.current_value, (int, float)):
            if weight_param.current_value < (weight_param.max_value or 1.0):
                suggested = min(
                    weight_param.current_value + 0.1,
                    weight_param.max_value or 1.0,
                )
                improvement = 5.0 if total_rate > 0.8 else 10.0
                suggestions.append(OptimizationSuggestion(
                    param_name="ranking.weights.success_probability",
                    current_value=weight_param.current_value,
                    suggested_value=suggested,
                    expected_improvement=improvement,
                    confidence=0.6,
                    evidence=[m.id for m in patterns[:3] if m.success_count > m.failure_count],
                ))

        return suggestions

    async def _analyze_duration(
        self, params: List[OptimizableParam]
    ) -> List[OptimizationSuggestion]:
        """Analyze for minimizing execution duration."""
        suggestions: List[OptimizationSuggestion] = []
        patterns = await self.memory.search({"type": "PATTERN", "min_confidence": 0.5})

        # Suggest reducing template max_nodes to keep graphs small
        tmpl = next(
            (p for p in params if p.name == "template.max_nodes"), None
        )
        if tmpl and isinstance(tmpl.current_value, (int, float)):
            if tmpl.current_value > (tmpl.min_value or 5):
                suggested = max(
                    tmpl.current_value - 5,
                    tmpl.min_value or 5,
                )
                improvement = 8.0  # smaller graphs execute faster
                suggestions.append(OptimizationSuggestion(
                    param_name="template.max_nodes",
                    current_value=tmpl.current_value,
                    suggested_value=suggested,
                    expected_improvement=improvement,
                    confidence=0.5,
                    evidence=[m.id for m in patterns[:3]],
                ))

        # Suggest reducing scheduler interval for faster reaction
        sched = next(
            (p for p in params if p.name == "scheduler.interval_seconds"), None
        )
        if sched and isinstance(sched.current_value, (int, float)):
            if sched.current_value > (sched.min_value or 5):
                suggested = max(
                    sched.current_value // 2,
                    sched.min_value or 5,
                )
                improvement = 15.0
                suggestions.append(OptimizationSuggestion(
                    param_name="scheduler.interval_seconds",
                    current_value=sched.current_value,
                    suggested_value=suggested,
                    expected_improvement=improvement,
                    confidence=0.4,
                    evidence=[m.id for m in patterns[:2]],
                ))

        return suggestions

    async def _analyze_cost(
        self, params: List[OptimizableParam]
    ) -> List[OptimizationSuggestion]:
        """Analyze for minimizing execution cost."""
        suggestions: List[OptimizationSuggestion] = []
        patterns = await self.memory.search({"type": "PATTERN", "min_confidence": 0.5})

        # Suggest reducing budget if patterns show low actual cost
        budget = next(
            (p for p in params if p.name == "budget.max_execution_cost"), None
        )
        if budget and isinstance(budget.current_value, (int, float)):
            if budget.current_value > (budget.min_value or 100):
                avg_cost = self._compute_avg_cost(patterns)
                if avg_cost is not None and avg_cost < budget.current_value * 0.5:
                    suggested = max(
                        int(budget.current_value * 0.8),
                        budget.min_value or 100,
                    )
                    improvement = 20.0
                    suggestions.append(OptimizationSuggestion(
                        param_name="budget.max_execution_cost",
                        current_value=budget.current_value,
                        suggested_value=suggested,
                        expected_improvement=improvement,
                        confidence=0.5,
                        evidence=[m.id for m in patterns[:3]],
                    ))

        # Suggest reducing retry backoff to lower cost of retries
        backoff = next(
            (p for p in params if p.name == "retry.backoff_seconds"), None
        )
        if backoff and isinstance(backoff.current_value, (int, float)):
            if backoff.current_value > (backoff.min_value or 1.0):
                suggested = max(
                    backoff.current_value - 1.0,
                    backoff.min_value or 1.0,
                )
                improvement = 10.0
                suggestions.append(OptimizationSuggestion(
                    param_name="retry.backoff_seconds",
                    current_value=backoff.current_value,
                    suggested_value=suggested,
                    expected_improvement=improvement,
                    confidence=0.4,
                    evidence=[m.id for m in patterns[:2]],
                ))

        return suggestions

    async def _get_lessons_as_memory(self) -> List[InstitutionalMemory]:
        """Get institutional memory entries derived from lessons."""
        try:
            return await self.memory.search({"type": "KNOWLEDGE"})
        except Exception:
            return []

    def _compute_avg_success_rate(
        self, entries: List[InstitutionalMemory]
    ) -> float:
        """Compute average success rate across memory entries."""
        total_ops = 0
        total_success = 0
        for e in entries:
            ops = e.success_count + e.failure_count
            if ops > 0:
                total_success += e.success_count
                total_ops += ops
        if total_ops == 0:
            return 1.0  # no data = assume healthy
        return total_success / total_ops

    def _compute_avg_cost(
        self, entries: List[InstitutionalMemory]
    ) -> Optional[float]:
        """Extract average cost from memory entry content."""
        costs: List[float] = []
        for e in entries:
            if isinstance(e.content, dict):
                cost = e.content.get("cost") or e.content.get("execution_cost")
                if cost is not None:
                    try:
                        costs.append(float(cost))
                    except (ValueError, TypeError):
                        pass
        if not costs:
            return None
        return sum(costs) / len(costs)

    def _merge_suggestions(
        self, *suggestion_lists: List[OptimizationSuggestion]
    ) -> List[OptimizationSuggestion]:
        """Merge suggestions from multiple analysis passes.

        If the same param_name appears in multiple lists, keep the
        one with the highest expected_improvement.
        """
        merged: Dict[str, OptimizationSuggestion] = {}
        for lst in suggestion_lists:
            for s in lst:
                key = s.param_name
                if key not in merged or s.expected_improvement > merged[key].expected_improvement:
                    merged[key] = s
        return list(merged.values())


def _parse_json(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (str, bytes)):
        try:
            return json.loads(val)
        except (ValueError, TypeError):
            return val
    return val
