"""Policy Rule — aturan policy (Sprint 205)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyRule:
    """Aturan policy (immutable). Deklaratif, tidak dievaluasi di sini."""
    rule_id: str
    policy_id: str = ""
    kind: str = "allow"
    condition: str = ""
    preview_only: bool = True
