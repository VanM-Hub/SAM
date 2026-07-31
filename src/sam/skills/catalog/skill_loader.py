"""Skill Loader — pemuat skill (Sprint 168).

Phase XVI — Skill Runtime.
Loader membuat katalog dari daftar skill. Tidak mengeksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.skill_registry import SkillRegistry
from ..foundation.skill_descriptor import SkillDescriptor


@dataclass(frozen=True)
class LoadResult:
    """Hasil pemuatan (immutable)."""
    loaded: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)


class SkillLoader:
    """Loader skill. Deterministik, build-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def load(self, descriptors: List[SkillDescriptor]) -> LoadResult:
        loaded = 0
        failed = 0
        errors = []
        for d in descriptors:
            if self._registry.register(d):
                loaded += 1
            else:
                failed += 1
                errors.append(f"duplicate: {d.id}")
        return LoadResult(loaded=loaded, failed=failed, errors=errors)
