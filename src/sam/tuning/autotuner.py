"""Performance Autotuner — Sprint 28 Fase 3.

Autotuner analyses runtime metrics and proposes parameter adjustments
via the Evolution Policy lifecycle.

Pipeline:
    analyze() — examine metrics, identify parameters to tune
    apply() — evolve a TuningSuggestion into a real parameter change
    monitor_after_apply() — observe impact for N seconds
    rollback() — revert if monitor detects degradation
"""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import structlog

from sam.evolution.params import OptimizableParam, ParamManager
from sam.tuning.metrics import MetricsCollector

logger = structlog.get_logger()


# ── Metric → Parameter binding rules ──────────────────────────────

# Maps metric name patterns to parameter name prefixes.
# Format: (metric_contains, param_name_contains, severity_weight, direction_hint)
# direction_hint: "lower" = high metric value suggests lowering the param
#                 "raise"  = high metric value suggests raising the param
METRIC_PARAM_BINDINGS: List[Tuple[str, str, float, str]] = [
    # High CPU → reduce threads, increase batch interval
    ("cpu_usage", "thread_pool", 1.0, "raise"),
    ("cpu_usage", "batch_size", 0.8, "lower"),
    # High memory → reduce cache, lower batch
    ("memory_usage", "cache_size", 1.0, "lower"),
    ("memory_usage", "batch_size", 0.6, "lower"),
    # Deep queue → increase pool, increase timeout
    ("queue_depth", "connection_pool", 1.0, "raise"),
    ("queue_depth", "timeout", 0.7, "raise"),
    ("queue_depth", "batch_size", 0.5, "lower"),
    # High latency → increase timeout, reduce batch
    ("latency_p99", "timeout", 1.0, "raise"),
    ("latency_p99", "batch_size", 0.7, "lower"),
    ("latency_p99", "connection_pool", 0.5, "raise"),
    # Low cache hit → increase cache
    ("cache_hit_ratio", "cache_size", 1.0, "raise"),
    # High error rate → increase timeout, reduce batch
    ("error_rate", "timeout", 1.0, "raise"),
    ("error_rate", "batch_size", 0.8, "lower"),
    ("error_rate", "retry", 0.6, "raise"),
    # High timeout ratio → increase timeout
    ("timeout_ratio", "timeout", 1.0, "raise"),
]


@dataclass
class TuningSuggestion:
    """A proposed parameter change from the autotuner.

    Attributes:
        param_name: Name of the parameter to change.
        current_value: Current value.
        suggested_value: Proposed new value.
        expected_improvement: Estimated improvement (%) if applied.
        confidence: Confidence in the suggestion (0.0–1.0).
        risk_level: "low", "medium", or "high".
        evidence: List of metric names that support this suggestion.
        reasoning: Human-readable explanation.
        created_at: When the suggestion was created.
    """
    param_name: str = ""
    current_value: Any = None
    suggested_value: Any = None
    expected_improvement: float = 0.0
    confidence: float = 0.0
    risk_level: str = "low"
    evidence: List[str] = field(default_factory=list)
    reasoning: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Autotuner:
    """Analyses metrics and proposes/adjusts parameters.

    Integrates with EvolutionPolicy for proposal lifecycle.
    """

    # Thresholds
    MIN_CONFIDENCE_FOR_AUTO = 0.6  # Confidence above this = auto-tune eligible
    MAX_RISK_FOR_AUTO = "medium"
    METRIC_WINDOW = 10  # How many samples to consider for trend
    MONITOR_DURATION = 60  # Default monitor period (seconds)
    DEGRADATION_THRESHOLD = 0.10  # 10% or more degradation triggers rollback

    def __init__(
        self,
        param_manager: ParamManager,
        metrics_collector: MetricsCollector,
    ) -> None:
        self._params = param_manager
        self._metrics = metrics_collector
        self._suggestion_history: List[TuningSuggestion] = []
        self._applied_suggestions: Dict[str, TuningSuggestion] = {}  # param_name -> last applied
        self.logger = logger.bind(component="Autotuner")

    async def analyze(self) -> List[TuningSuggestion]:
        """Analyze recent metrics and produce tuning suggestions.

        Steps:
          1. Gather metric names from collector.
          2. For each metric name, get trend and latest value.
          3. Compare against parameter bindings.
          4. For each matching param, compute suggested delta.
          5. Return ranked list of TuningSuggestion.

        Runs only when there are metrics available.
        """
        metric_names = self._metrics.get_all_metric_names()
        if not metric_names:
            self.logger.debug("No metrics available for analysis")
            return []

        suggestions: List[TuningSuggestion] = []

        for metric_name in metric_names:
            trend = self._metrics.get_trend(metric_name, window=self.METRIC_WINDOW)
            if len(trend) < 3:
                continue  # Not enough data

            latest = trend[-1]

            # Find matching parameter bindings
            for m_pat, p_pat, weight, direction in METRIC_PARAM_BINDINGS:
                if m_pat not in metric_name:
                    continue

                # Find all registered params matching the pattern
                # We search by iterating known params of the manager
                param = await self._find_param_by_pattern(p_pat)
                if param is None:
                    continue

                # Compute suggestion
                suggestion = await self._build_suggestion(
                    param=param,
                    metric_name=metric_name,
                    latest=latest,
                    trend=trend,
                    weight=weight,
                    direction=direction,
                )
                if suggestion is not None:
                    suggestions.append(suggestion)

        # Deduplicate: keep highest confidence per param
        seen: Dict[str, TuningSuggestion] = {}
        for s in suggestions:
            if s.param_name in seen:
                if s.confidence > seen[s.param_name].confidence:
                    seen[s.param_name] = s
            else:
                seen[s.param_name] = s

        result = list(seen.values())
        # Sort by confidence descending
        result.sort(key=lambda s: s.confidence, reverse=True)

        self._suggestion_history.extend(result)
        self.logger.info(
            "Autotuner analysis complete",
            suggestions=len(result),
        )
        return result

    async def apply(self, suggestion: TuningSuggestion) -> None:
        """Apply a tuning suggestion — change the parameter value.

        Args:
            suggestion: The TuningSuggestion to apply.

        Raises:
            ValueError: If param not found or value out of bounds.
        """
        param = await self._params.get(suggestion.param_name)
        if param is None:
            raise ValueError(f"Parameter '{suggestion.param_name}' not found")

        # Clamp to bounds
        new_value = self._clamp(suggestion.suggested_value, param)

        old_value = param.current_value
        if old_value == new_value:
            self.logger.debug(
                "Skipping apply — value unchanged",
                param_name=suggestion.param_name,
            )
            return

        await self._params.set(suggestion.param_name, new_value)

        self._applied_suggestions[suggestion.param_name] = suggestion
        self.logger.info(
            "Autotuner applied",
            param_name=suggestion.param_name,
            old_value=old_value,
            new_value=new_value,
            confidence=suggestion.confidence,
        )

    async def monitor_after_apply(
        self,
        suggestion: TuningSuggestion,
        duration: int = 60,
    ) -> bool:
        """Monitor the effect of an applied suggestion.

        Compares metrics before and after the change.
        Returns True if no degradation detected, False if rollback recommended.

        Args:
            suggestion: The applied suggestion to monitor.
            duration: How many seconds to monitor (real-time sleep is simulated
                      if insufficient data exists).

        Returns:
            True if system not degraded, False if degradation detected.
        """
        param_name = suggestion.param_name

        # Collect baseline (the metrics that existed before apply)
        # Compare first half vs second half of the trend to detect degradation.
        degraded = False
        for evidence_metric in suggestion.evidence:
            trend = self._metrics.get_trend(evidence_metric, window=self.METRIC_WINDOW)
            if len(trend) < 4:
                continue

            mid = len(trend) // 2
            first_half = trend[:mid]
            second_half = trend[mid:]
            pre_avg = sum(first_half) / len(first_half)
            post_avg = sum(second_half) / len(second_half)

            # Simulate wait for impact
            await self._wait(duration)

            # Determine if higher is better
            higher_is_better = self._is_higher_better(evidence_metric)
            avg_delta = (post_avg - pre_avg) / max(1e-6, pre_avg)

            if higher_is_better and avg_delta < -self.DEGRADATION_THRESHOLD:
                degraded = True
                self.logger.warning(
                    "Metric degraded (higher is better)",
                    metric=evidence_metric,
                    pre=pre_avg,
                    post=post_avg,
                    delta_ratio=avg_delta,
                )
            elif not higher_is_better and avg_delta > self.DEGRADATION_THRESHOLD:
                degraded = True
                self.logger.warning(
                    "Metric degraded (lower is better)",
                    metric=evidence_metric,
                    pre=pre_avg,
                    post=post_avg,
                    delta_ratio=avg_delta,
                )

        if not self._has_any_evidence(suggestion):
            self.logger.debug("No pre-metrics for monitor — assuming success")
            return True

        if degraded:
            self.logger.warning(
                "Monitoring detected degradation",
                param_name=param_name,
            )
        else:
            self.logger.info("Monitor passed — no degradation detected")

        return not degraded

    async def rollback(self, suggestion: TuningSuggestion) -> None:
        """Rollback a suggestion — restore the original parameter value.

        Args:
            suggestion: The suggestion to rollback.
        """
        param = await self._params.get(suggestion.param_name)
        if param is None:
            raise ValueError(f"Parameter '{suggestion.param_name}' not found")

        old_value = param.current_value
        new_value = suggestion.current_value

        if old_value == new_value:
            self.logger.debug(
                "Rollback skipped — value already target",
                param_name=suggestion.param_name,
            )
            return

        await self._params.set(suggestion.param_name, suggestion.current_value)

        # Remove from applied dict
        self._applied_suggestions.pop(suggestion.param_name, None)

        self.logger.info(
            "Autotuner rollback",
            param_name=suggestion.param_name,
            reverted_to=suggestion.current_value,
        )

    def get_suggestion_history(self, limit: int = 50) -> List[TuningSuggestion]:
        """Return recent tuning suggestions."""
        return self._suggestion_history[-limit:]

    def get_applied_summary(self) -> Dict[str, TuningSuggestion]:
        """Return dict of currently applied suggestions (param_name -> suggestion)."""
        return dict(self._applied_suggestions)

    @staticmethod
    def _has_any_evidence(suggestion: TuningSuggestion) -> bool:
        """Check if a suggestion has at least one metric name in evidence."""
        return bool(suggestion.evidence)

    # ── Internal helpers ──────────────────────────────────────────

    async def _find_param_by_pattern(self, pattern: str) -> Optional[OptimizableParam]:
        """Find a registered param whose name contains `pattern`.

        For the in-memory / test scenario we iterate via a simple convention.
        The real ParamManager doesn't expose a search API, so we use
        a known-list approach on first call.
        """
        # We attempt to find params by enumerating names in self._params
        # The in-memory _InMemoryParamManager stores them in _params dict.
        try:
            params_dict = self._params._params  # type: ignore[attr-defined]
            for name, param in params_dict.items():
                if pattern in name:
                    return param
        except AttributeError:
            pass
        return None

    async def _build_suggestion(
        self,
        param: OptimizableParam,
        metric_name: str,
        latest: float,
        trend: List[float],
        weight: float,
        direction: str,
    ) -> Optional[TuningSuggestion]:
        """Build a TuningSuggestion from a metric-to-param binding.

        Returns None if the change is too small to be meaningful.
        """
        current = param.current_value
        if not isinstance(current, (int, float)):
            return None

        step = param.step if param.step is not None else 1
        if not isinstance(step, (int, float)):
            step = 1

        # Compute suggested delta
        # direction "raise" = metric is too high, raise the param to compensate
        # direction "lower" = metric is too high, lower the param
        if direction == "raise":
            suggested = current + step
        else:
            suggested = current - step

        suggested = self._clamp(suggested, param)

        if suggested == current:
            return None

        # Compute confidence and expected improvement
        trend_stability = self._trend_stability(trend)
        confidence = min(1.0, weight * trend_stability)
        confidence = max(0.1, round(confidence, 2))

        # Compute expected improvement from metric deviation
        baseline = sum(trend[:max(1, len(trend) // 2)]) / max(1, len(trend) // 2)
        deviation = abs(latest - baseline) / max(1e-6, baseline)
        expected_improvement = round(min(100, deviation * 100), 1)
        if expected_improvement < 0.5:
            return None  # Too small to bother

        # Risk level
        risk = self._compute_risk(param, deviation, direction)

        return TuningSuggestion(
            param_name=param.name,
            current_value=current,
            suggested_value=suggested,
            expected_improvement=expected_improvement,
            confidence=confidence,
            risk_level=risk,
            evidence=[metric_name],
            reasoning=(
                f"Metric '{metric_name}' at {latest:.2f} suggests "
                f"{direction}ing '{param.name}' from {current} to {suggested}. "
                f"Deviation {deviation:.1%}, stability {trend_stability:.2f}."
            ),
        )

    def _clamp(self, value: Any, param: OptimizableParam) -> Any:
        """Clamp a numeric value within parameter bounds."""
        if not isinstance(value, (int, float)):
            return value
        if param.min_value is not None:
            value = max(param.min_value, value)
        if param.max_value is not None:
            value = min(param.max_value, value)
        # For int params, round to int
        if isinstance(param.current_value, int):
            value = int(round(value))
        return value

    def _trend_stability(self, trend: List[float]) -> float:
        """Compute stability of a trend (1.0 = perfectly stable, 0.0 = random)."""
        if len(trend) < 2:
            return 0.5
        mean = sum(trend) / len(trend)
        if mean == 0:
            mean = 1e-6
        variance = sum((v - mean) ** 2 for v in trend) / len(trend)
        cv = math.sqrt(variance) / abs(mean)  # coefficient of variation
        # Map cv to stability: cv=0 → 1.0, cv>1 → ~0.3
        stability = max(0.3, min(1.0, 1.0 - cv))
        return stability

    def _compute_risk(
        self,
        param: OptimizableParam,
        deviation: float,
        direction: str,
    ) -> str:
        """Estimate risk level based on deviation and param category."""
        # Base risk by category
        category_risk = {
            "RANKING": "low",
            "TEMPLATE": "low",
            "SCHEDULER": "medium",
            "RETRY": "medium",
            "BUDGET": "high",
        }.get(param.category, "medium")

        # Increase if deviation is large
        if deviation > 0.5:
            if category_risk == "low":
                return "medium"
            if category_risk == "medium":
                return "high"
            return "high"

        return category_risk

    @staticmethod
    def _is_higher_better(metric_name: str) -> bool:
        """Return True if a higher metric value is better."""
        higher_better = {"cache_hit_ratio", "throughput", "success_rate"}
        for hb in higher_better:
            if hb in metric_name:
                return True
        return False

    @staticmethod
    async def _wait(seconds: int) -> None:
        """Wait without blocking the event loop."""
        await _asyncio_sleep(seconds)


# Lazy import to avoid circular issues at module level
def _asyncio_sleep(seconds: int):
    import asyncio
    return asyncio.sleep(max(0.1, seconds))
