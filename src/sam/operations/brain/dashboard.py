"""
OP-247 — Brain Dashboard DTO.

DTOs consumed by Console and Desktop renderers.
No Qt imports — pure data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BrainDashboardData:
    """Dashboard data for operational brain.

    Console and Desktop only read this DTO.
    """

    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    observation_summary: Dict[str, Any] = field(default_factory=dict)
    triggered_rules: List[Dict[str, Any]] = field(default_factory=list)
    health_score: float = 1.0
    health_state: str = "healthy"
    generated_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to plain dict for renderers."""
        return {
            "findings": self.findings,
            "recommendations": self.recommendations,
            "observation_summary": self.observation_summary,
            "triggered_rules": self.triggered_rules,
            "health_score": self.health_score,
            "health_state": self.health_state,
            "generated_at": self.generated_at,
        }

    @classmethod
    def empty(cls) -> BrainDashboardData:
        return cls()

    @property
    def has_issues(self) -> bool:
        return any(
            f.get("severity") in ("critical", "warning")
            for f in self.findings
        )

    @property
    def critical_count(self) -> int:
        return sum(
            1 for f in self.findings
            if f.get("severity") == "critical"
        )

    @property
    def warning_count(self) -> int:
        return sum(
            1 for f in self.findings
            if f.get("severity") == "warning"
        )


def build_dashboard_data(
    findings: List[Any],
    recommendations: List[Any],
    observation: Any,
    rules: List[Any],
) -> BrainDashboardData:
    """Build dashboard DTO from brain pipeline outputs."""
    import time

    # Convert dataclass objects to dicts
    finding_dicts = []
    for f in findings:
        if hasattr(f, "__dataclass_fields__"):
            d = {k: getattr(f, k) for k in f.__dataclass_fields__}
            if hasattr(f, "severity") and hasattr(f.severity, "value"):
                d["severity"] = f.severity.value
            finding_dicts.append(d)
        elif isinstance(f, dict):
            finding_dicts.append(f)

    rec_dicts = []
    for r in recommendations:
        if hasattr(r, "__dataclass_fields__"):
            rec_dicts.append({k: getattr(r, k) for k in r.__dataclass_fields__})
        elif isinstance(r, dict):
            rec_dicts.append(r)

    rule_dicts = []
    for r in rules:
        if hasattr(r, "__dataclass_fields__"):
            rule_dicts.append({k: getattr(r, k) for k in r.__dataclass_fields__})
        elif isinstance(r, dict):
            rule_dicts.append(r)

    obs_dict = {}
    if observation is not None:
        if hasattr(observation, "__dataclass_fields__"):
            obs_dict = {k: _serialize(getattr(observation, k)) for k in observation.__dataclass_fields__}
        elif isinstance(observation, dict):
            obs_dict = observation

    # Compute health score
    critical = sum(1 for f in finding_dicts if f.get("severity") == "critical")
    warning = sum(1 for f in finding_dicts if f.get("severity") == "warning")
    health_score = max(0.0, 1.0 - (critical * 0.3) - (warning * 0.1))
    health_state = "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "unhealthy"

    return BrainDashboardData(
        findings=finding_dicts,
        recommendations=rec_dicts,
        observation_summary=obs_dict,
        triggered_rules=rule_dicts,
        health_score=round(health_score, 2),
        health_state=health_state,
        generated_at=time.time(),
    )


def _serialize(value: Any) -> Any:
    """Recursively serialize a value for dict output."""
    if hasattr(value, "__dataclass_fields__"):
        return {k: _serialize(getattr(value, k)) for k in value.__dataclass_fields__}
    elif isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    elif isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    elif hasattr(value, "value"):  # Enum
        return value.value
    return value
