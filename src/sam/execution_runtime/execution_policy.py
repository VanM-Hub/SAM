"""Execution Policy (Sprint 257).

Program C - Real Execution Runtime.
Kebijakan eksekusi immutable: batasan yang ditegakkan.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class ExecutionPolicy:
    """Kebijakan eksekusi (immutable)."""
    policy_id: str
    require_approval: bool = True
    max_retries: int = 2
    max_timeout_seconds: int = 300
    allow_network: bool = True
    provider_whitelist: tuple = field(default_factory=tuple)  # kosong = semua

    def allows_provider(self, provider_id: str) -> bool:
        return not self.provider_whitelist or provider_id in self.provider_whitelist
