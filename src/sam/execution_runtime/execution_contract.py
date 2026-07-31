"""Execution Contract (Sprint 250).

Program C - Real Execution Runtime.
Immutable contract of what an execution may and may not do.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ExecutionContract:
    """Kontrak eksekusi (immutable). Menegakkan batasan eksekusi."""
    contract_id: str
    owner_id: str
    allowed_modes: List[str] = field(default_factory=lambda: ["preview", "execute", "rollback"])
    requires_approval: bool = True
    allow_network: bool = True  # network diizinkan saat execute
    max_retries: int = 2
    timeout_seconds: int = 60
    external_calls: int = 0  # execution tidak boleh saat preview

    def as_dict(self) -> dict:
        return {
            "contract_id": self.contract_id,
            "owner_id": self.owner_id,
            "allowed_modes": list(self.allowed_modes),
            "requires_approval": self.requires_approval,
            "allow_network": self.allow_network,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "external_calls": self.external_calls,
        }
