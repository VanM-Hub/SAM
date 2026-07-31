"""Dashboard utility shared — WorkflowCard (Sprint 196, dipakai seluruh Phase XX)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowCard:
    """Card untuk dashboard workflow (immutable)."""
    key: str
    group: str
    verdict: str
    detail: str
    label: str = ""
    status: str = "ready"
