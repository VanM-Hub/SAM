"""Policy — model policy (Sprint 205)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Policy:
    """Policy (immutable)."""
    policy_id: str
    name: str = ""
    rules: List[str] = field(default_factory=list)
    scope: str = "system"
    preview_only: bool = True

    def rule_count(self) -> int:
        return len(self.rules)
