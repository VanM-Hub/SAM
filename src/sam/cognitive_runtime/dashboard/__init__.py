"""Dashboard utility shared — ExecutionCard (Sprint 188, dipakai seluruh Phase XIX)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionCard:
    """Card untuk dashboard (immutable)."""
    key: str
    group: str
    verdict: str
    detail: str
    label: str = ""
    status: str = "ready"
