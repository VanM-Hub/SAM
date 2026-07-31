"""Dashboard utility shared — PolicyCard (Sprint 204, dipakai seluruh Phase XXI)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyCard:
    """Card untuk dashboard policy (immutable)."""
    key: str
    group: str
    verdict: str
    detail: str
    label: str = ""
    status: str = "ready"
