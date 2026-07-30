"""Risk — frozen DTO risiko eksekusi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class RiskFactor:
    name: str
    score: float
    description: str = ""


@dataclass(frozen=True)
class RiskAssessment:
    assessment_id: str
    candidate_id: str = ""
    overall_score: float = 0.0
    factors: Tuple[RiskFactor, ...] = field(default_factory=tuple)
    level: str = "low"


@dataclass(frozen=True)
class RiskReport:
    report_id: str
    execution_plan_id: str
    assessments: Tuple[RiskAssessment, ...] = field(default_factory=tuple)
    total_assessments: int = 0
    highest_risk: float = 0.0
    avg_risk: float = 0.0
    critical_count: int = 0


@dataclass(frozen=True)
class RiskSummary:
    total_assessments: int = 0
    avg_score: float = 0.0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    status: str = "low_risk"
