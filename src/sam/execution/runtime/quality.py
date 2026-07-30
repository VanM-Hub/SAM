"""Quality — frozen DTO kualitas eksekusi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class QualityMetric:
    name: str
    score: float
    weight: float = 1.0
    description: str = ""


@dataclass(frozen=True)
class QualityAssessment:
    assessment_id: str
    execution_plan_id: str
    metrics: Tuple[QualityMetric, ...] = field(default_factory=tuple)
    overall_score: float = 0.0
    total_weight: float = 0.0
    category: str = "execution"


@dataclass(frozen=True)
class QualityGate:
    gate_id: str
    name: str
    threshold: float = 0.8
    passed: bool = False
    score: float = 0.0
    failures: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class QualitySummary:
    total_assessments: int = 0
    avg_score: float = 0.0
    gates_passed: int = 0
    gates_failed: int = 0
    status: str = "unknown"
