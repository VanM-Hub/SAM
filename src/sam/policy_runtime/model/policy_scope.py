"""Policy Scope — lingkup policy (Sprint 205)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


VALID_SCOPES = ["system", "mission", "workflow", "resource", "user"]


@dataclass(frozen=True)
class PolicyScope:
    """Lingkup policy (immutable)."""
    scope: str = "system"
    targets: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.scope not in VALID_SCOPES:
            raise ValueError(f"invalid scope '{self.scope}'")
