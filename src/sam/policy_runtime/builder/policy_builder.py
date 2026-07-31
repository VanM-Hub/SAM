"""Policy Builder — builder DTO policy (Sprint 206).

Builder HANYA menyusun DTO. TIDAK mengevaluasi, TIDAK mengambil keputusan.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..model.policy import Policy


@dataclass(frozen=True)
class PolicyBuildResult:
    """Hasil build (immutable)."""
    ok: bool = True
    policy: Policy = field(default_factory=lambda: Policy(""))
    detail: str = ""


class PolicyBuilder:
    """Builder utama policy. Deterministik."""

    def build(self, policy_id: str, name: str = "", rules: list = None) -> PolicyBuildResult:
        return PolicyBuildResult(
            ok=True,
            policy=Policy(policy_id=policy_id, name=name, rules=list(rules or [])),
            detail="built",
        )
