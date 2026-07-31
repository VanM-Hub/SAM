"""Audit Scope — lingkup audit (Sprint 213)."""
from __future__ import annotations
from dataclasses import dataclass

VALID_SCOPES = ("mission", "agent", "skill", "workflow", "policy", "memory",
                "knowledge", "cognitive", "orchestrator", "connector",
                "provider", "system")


@dataclass(frozen=True)
class AuditScope:
    """Lingkup audit immutable."""
    scope: str = "system"

    def __post_init__(self) -> None:
        if self.scope not in VALID_SCOPES:
            raise ValueError(f"invalid audit scope: {self.scope}")
