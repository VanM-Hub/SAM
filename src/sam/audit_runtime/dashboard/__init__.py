"""Shared dashboard PolicyCard (Sprint 212)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyCard:
    """Kartu dashboard immutable."""
    key: str
    category: str
    status: str
    message: str = ""
    detail: str = ""
    verdict: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "detail", self.detail or self.message)
        object.__setattr__(self, "verdict", self.verdict or self.status)
