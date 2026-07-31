"""Routing Summary — engine ringkasan routing.

Sprint 117 — Connector Routing.
Ringkasan hasil routing (read-only).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_router import RoutingResult


@dataclass(frozen=True)
class RoutingSummary:
    """Ringkasan routing."""
    total_routes: int = 0
    routed: int = 0
    failures: int = 0


class RoutingSummarizer:
    """Ringkasan hasil routing."""

    def summarize(self, results: List[RoutingResult]) -> RoutingSummary:
        routed = sum(1 for r in results if r.routed)
        return RoutingSummary(len(results), routed, len(results) - routed)
