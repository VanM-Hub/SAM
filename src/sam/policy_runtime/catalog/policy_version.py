"""Policy Version — versi policy (Sprint 208)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyVersionInfo:
    """Info versi policy (immutable)."""
    version: str = "21.0.0"
    policy_id: str = ""
    runtime: str = "policy_runtime"


class PolicyVersionProvider:
    """Provider versi. Read-only, deterministik."""

    def provide(self, policy_id: str) -> PolicyVersionInfo:
        return PolicyVersionInfo(version="21.0.0", policy_id=policy_id)
