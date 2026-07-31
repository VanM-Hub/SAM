"""Transition Rule — aturan transisi (Sprint 158).

Agent Runtime — aturan transisi sejalan dengan StateMachine.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TransitionRule:
    """Aturan transisi (immutable)."""
    from_state: str
    to_state: str
    auto: bool = False  # false -> tidak ada auto transition/retry
    reason: str = ""
