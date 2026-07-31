"""Skill Metrics — metrik skill (Sprint 169).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.skill_registry import SkillRegistry


@dataclass(frozen=True)
class SkillMetricSample:
    """Satu sampel metrik skill (immutable)."""
    skill_id: str
    preview_count: int = 0
    external_calls: int = 0
    healthy: bool = False


@dataclass(frozen=True)
class SkillMetrics:
    """Metrik skill (immutable)."""
    total: int = 0
    external_calls: int = 0
    samples: List[SkillMetricSample] = field(default_factory=list)


class SkillMetricsCollector:
    """Collector metrik skill. Read-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def collect(self) -> SkillMetrics:
        samples = []
        for sid in self._registry.list_ids():
            d = self._registry.find(sid)
            healthy = d is not None and bool(self._registry.get_capabilities(sid))
            samples.append(SkillMetricSample(
                skill_id=sid, preview_count=0, external_calls=0, healthy=healthy,
            ))
        return SkillMetrics(
            total=len(samples), external_calls=0, samples=samples,
        )
