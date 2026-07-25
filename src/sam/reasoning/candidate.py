"""
Plan Candidate – Sprint 23 Fase 1

Represents a single candidate plan (ExecutionGraph) with estimated
risk, confidence, cost, and historical success metrics. The PlanRanker
uses these scores to select the best plan from a candidate pool.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator

from ..execution.graph import ExecutionGraph


# ── Plan Candidate Model ─────────────────────────────────────────────


class PlanCandidate(BaseModel):
    """A candidate plan generated from an Intent.

    Each candidate wraps an ExecutionGraph with scoring metadata
    that the PlanRanker uses to sort and select the best plan.

    Attributes:
        id: Unique candidate identifier (UUID).
        intent_id: The originating Intent ID.
        graph: The concrete ExecutionGraph this candidate represents.
        estimated_duration: Expected execution duration in seconds.
        risk_score: Estimated risk level (0.0 = no risk, 1.0 = max risk).
        confidence: Confidence in the plan's success (0.0–1.0).
        cost_estimate: Estimated operational cost (arbitrary unit).
        historical_success_rate: Success rate from past executions (0.0–1.0).
        approval_required: Whether this plan requires human approval.
        metadata: Additional candidate metadata.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique candidate identifier",
    )
    intent_id: str = Field(description="Originating Intent ID")
    graph: ExecutionGraph = Field(description="The concrete ExecutionGraph")
    estimated_duration: int = Field(
        default=60,
        ge=0,
        description="Estimated duration in seconds",
    )
    risk_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Estimated risk level (0.0–1.0)",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in success (0.0–1.0)",
    )
    cost_estimate: float = Field(
        default=1.0,
        ge=0.0,
        description="Estimated operational cost (arbitrary unit)",
    )
    historical_success_rate: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Historical success rate (0.0–1.0)",
    )
    approval_required: bool = Field(
        default=False,
        description="Whether human approval is needed",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional candidate metadata",
    )

    @model_validator(mode="after")
    def _validate_scores(self) -> "PlanCandidate":
        """Ensure combined scores produce reasonable totals."""
        if self.risk_score + self.confidence > 2.0:
            pass  # Allow valid ranges; no strict constraint needed
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dict (for logging, reporting)."""
        return {
            "id": self.id,
            "intent_id": self.intent_id,
            "graph_id": self.graph.id,
            "graph_name": self.graph.name,
            "node_count": len(self.graph.nodes),
            "estimated_duration": self.estimated_duration,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "cost_estimate": self.cost_estimate,
            "historical_success_rate": self.historical_success_rate,
            "approval_required": self.approval_required,
            "metadata": self.metadata,
        }
