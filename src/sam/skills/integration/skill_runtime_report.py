"""Skill Runtime Report — laporan runtime integrasi (Sprint 171).

Read-only, tidak mengubah runtime lain.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.skill_registry import SkillRegistry
from .skill_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class SkillRuntimeReport:
    """Laporan runtime integrasi (immutable)."""
    total_skills: int = 0
    route: List[str] = field(default_factory=list)
    external_calls: int = 0
    ready: bool = False


class SkillRuntimeReporter:
    """Reporter runtime integrasi. Read-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def report(self) -> SkillRuntimeReport:
        return SkillRuntimeReport(
            total_skills=self._registry.count(),
            route=list(INTEGRATION_ROUTE),
            external_calls=0,
            ready=self._registry.count() > 0,
        )
