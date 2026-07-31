# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 127 - Dependency Resolver: dependency_report.

Report describing a resolved dependency order. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DependencyReport:
    """Immutable result of dependency resolution."""

    order: Tuple[str, ...]
    acyclic: bool = True
    edge_count: int = 0
