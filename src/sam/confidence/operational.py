"""Operational Confidence — Sprint 28 Fase 2.

Calculates a 0–100 confidence score based on multiple runtime signals:
health status, success/failure/rollback rates, pending approvals,
stability metrics, knowledge freshness, and reasoning confidence.

The score feeds into EvolutionPolicy for gating proposals and into
SelfHealingLoop for deciding auto-recovery aggressiveness.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict
import structlog

from sam.persistence.database import Database


logger = structlog.get_logger()


# ── Health status weights ──────────────────────────────────────────

_HEALTH_WEIGHTS: Dict[str, float] = {
    "healthy": 1.0,
    "degraded": 0.5,
    "unhealthy": 0.0,
    "unknown": 0.3,
}


# ── Data Classes ───────────────────────────────────────────────────


@dataclass
class ConfidenceInput:
    """All input signals for a confidence calculation.

    Defaults represent a perfectly healthy system.
    """

    health_status: str = "healthy"
    success_rate: float = 1.0
    failure_rate: float = 0.0
    rollback_rate: float = 0.0
    pending_approvals: int = 0
    runtime_stability: float = 1.0
    resource_pressure: float = 0.0
    cluster_stability: float = 1.0
    knowledge_freshness: float = 1.0
    reasoning_confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "health_status": self.health_status,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "rollback_rate": self.rollback_rate,
            "pending_approvals": self.pending_approvals,
            "runtime_stability": self.runtime_stability,
            "resource_pressure": self.resource_pressure,
            "cluster_stability": self.cluster_stability,
            "knowledge_freshness": self.knowledge_freshness,
            "reasoning_confidence": self.reasoning_confidence,
        }


@dataclass
class ConfidenceBreakdown:
    """Detailed breakdown of each component's contribution to the score."""

    health: float
    success_rate: float
    failure_rate: float
    rollback_rate: float
    pending_approvals: float
    runtime_stability: float
    resource_pressure: float
    cluster_stability: float
    knowledge_freshness: float
    reasoning_confidence: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "health": round(self.health, 2),
            "success_rate": round(self.success_rate, 2),
            "failure_rate": round(self.failure_rate, 2),
            "rollback_rate": round(self.rollback_rate, 2),
            "pending_approvals": round(self.pending_approvals, 2),
            "runtime_stability": round(self.runtime_stability, 2),
            "resource_pressure": round(self.resource_pressure, 2),
            "cluster_stability": round(self.cluster_stability, 2),
            "knowledge_freshness": round(self.knowledge_freshness, 2),
            "reasoning_confidence": round(self.reasoning_confidence, 2),
        }


# ── Calculator ─────────────────────────────────────────────────────


class OperationalConfidenceCalculator:
    """Calculates operational confidence score (0–100) from runtime signals.

    Each component contributes 0–10 points to a total of 100.
    Some components are penalties (failure_rate, resource_pressure,
    rollback_rate, pending_approvals) — high values reduce the score.

    Usage:
        calc = OperationalConfidenceCalculator(db)
        score, breakdown = await calc.calculate(input_data)
        await calc.record(score, input_data, breakdown)
        current = calc.get_current_score()
    """

    # Weights: each component contributes max 10 points
    # Penalty components use (1 - value) * 10
    _COMPONENTS = [
        "health",
        "success_rate",
        "failure_rate",
        "rollback_rate",
        "pending_approvals",
        "runtime_stability",
        "resource_pressure",
        "cluster_stability",
        "knowledge_freshness",
        "reasoning_confidence",
    ]

    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db
        self._current_score: Optional[int] = None
        self._current_breakdown: Optional[ConfidenceBreakdown] = None
        self._logger = logger.bind(component="OperationalConfidence")

    async def calculate(
        self,
        inputs: Optional[ConfidenceInput] = None,
        **kwargs,
    ) -> tuple[int, ConfidenceBreakdown]:
        """Calculate operational confidence score from input signals.

        Args:
            inputs: A ConfidenceInput instance with all signals.
            **kwargs: Override individual signals.

        Returns:
            Tuple of (score: int 0-100, breakdown: ConfidenceBreakdown).
        """
        # Merge inputs with kwargs overrides
        data = ConfidenceInput()
        if inputs is not None:
            data = inputs
        for key, value in kwargs.items():
            if hasattr(data, key):
                setattr(data, key, value)

        # Health score (0–10)
        health_weight = _HEALTH_WEIGHTS.get(data.health_status, 0.3)
        health_score = health_weight * 10.0

        # Success rate (0–10)
        success_score = data.success_rate * 10.0

        # Failure rate penalty (0–10) — inverted: high failure = low score
        failure_penalty = (1.0 - data.failure_rate) * 10.0

        # Rollback rate penalty (0–10) — inverted
        rollback_penalty = (1.0 - data.rollback_rate) * 10.0

        # Pending approvals penalty (0–10) — inverted
        # Scale: 0 pending = 10, 10+ pending = 0
        pending_score = max(0.0, 10.0 - data.pending_approvals)

        # Runtime stability (0–10)
        stability_score = data.runtime_stability * 10.0

        # Resource pressure penalty (0–10) — inverted
        resource_score = (1.0 - data.resource_pressure) * 10.0

        # Cluster stability (0–10)
        cluster_score = data.cluster_stability * 10.0

        # Knowledge freshness (0–10)
        knowledge_score = data.knowledge_freshness * 10.0

        # Reasoning confidence (0–10)
        reasoning_score = data.reasoning_confidence * 10.0

        # Aggregate
        components = [
            health_score, success_score, failure_penalty, rollback_penalty,
            pending_score, stability_score, resource_score, cluster_score,
            knowledge_score, reasoning_score,
        ]
        total = sum(components)
        score = max(0, min(100, round(total)))

        breakdown = ConfidenceBreakdown(
            health=health_score,
            success_rate=success_score,
            failure_rate=failure_penalty,
            rollback_rate=rollback_penalty,
            pending_approvals=pending_score,
            runtime_stability=stability_score,
            resource_pressure=resource_score,
            cluster_stability=cluster_score,
            knowledge_freshness=knowledge_score,
            reasoning_confidence=reasoning_score,
        )

        self._current_score = score
        self._current_breakdown = breakdown

        self._logger.debug(
            "Confidence calculated",
            score=score,
            health=data.health_status,
            success_rate=data.success_rate,
        )
        return score, breakdown

    async def record(
        self,
        score: int,
        inputs: ConfidenceInput,
        breakdown: ConfidenceBreakdown,
    ) -> str:
        """Persist a confidence record to the database.

        Returns:
            The history entry ID.
        """
        record_id = f"conf_{uuid.uuid4().hex[:12]}"

        if self._db:
            await self._db.execute(
                """INSERT INTO operational_confidence_history
                   (id, score, health_status, success_rate, failure_rate,
                    rollback_rate, pending_approvals, runtime_stability,
                    resource_pressure, cluster_stability,
                    knowledge_freshness, reasoning_confidence,
                    component_breakdown)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    record_id,
                    score,
                    inputs.health_status,
                    inputs.success_rate,
                    inputs.failure_rate,
                    inputs.rollback_rate,
                    inputs.pending_approvals,
                    inputs.runtime_stability,
                    inputs.resource_pressure,
                    inputs.cluster_stability,
                    inputs.knowledge_freshness,
                    inputs.reasoning_confidence,
                    json.dumps(breakdown.to_dict()),
                ],
            )

        self._logger.info(
            "Confidence recorded",
            record_id=record_id,
            score=score,
        )
        return record_id

    async def calculate_and_record(
        self,
        inputs: Optional[ConfidenceInput] = None,
        **kwargs,
    ) -> tuple[int, ConfidenceBreakdown]:
        """Convenience: calculate + persist in one call."""
        score, breakdown = await self.calculate(inputs, **kwargs)
        if inputs is None:
            inputs = ConfidenceInput(**kwargs)
        await self.record(score, inputs, breakdown)
        return score, breakdown

    def get_current_score(self) -> Optional[int]:
        """Return the last calculated score (or None if never calculated)."""
        return self._current_score

    def get_current_breakdown(self) -> Optional[ConfidenceBreakdown]:
        """Return the last breakdown (or None if never calculated)."""
        return self._current_breakdown

    async def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Retrieve recorded confidence history."""
        if not self._db:
            return []

        rows = await self._db.fetch_all(
            "SELECT * FROM operational_confidence_history "
            "ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [dict(r) for r in rows]

    async def get_latest(self) -> Optional[Dict[str, Any]]:
        """Get the most recent confidence record."""
        if not self._db:
            if self._current_score is not None:
                return {
                    "score": self._current_score,
                    "source": "in_memory",
                }
            return None

        row = await self._db.fetch_one(
            "SELECT * FROM operational_confidence_history "
            "ORDER BY timestamp DESC LIMIT 1"
        )
        if row is None:
            if self._current_score is not None:
                return {"score": self._current_score, "source": "in_memory"}
            return None
        return dict(row)


__all__ = [
    "ConfidenceInput",
    "ConfidenceBreakdown",
    "OperationalConfidenceCalculator",
]
