"""Policy Runtime — engine utama runtime policy (Sprint 207)."""
from __future__ import annotations
from dataclasses import dataclass, field

from ..model.policy import Policy
from ..foundation.policy_registry import PolicyRegistry


@dataclass(frozen=True)
class PolicyRunResult:
    """Hasil run runtime policy (immutable)."""
    ok: bool = True
    policy_id: str = ""
    policy: Policy = field(default_factory=lambda: Policy(""))
    external_calls: int = 0
    decided: bool = False


class PolicyRuntime:
    """Runtime policy. Deterministik, preview-only, tanpa keputusan/inferensi."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def run(self, policy_id: str) -> PolicyRunResult:
        if not self._registry.exists(policy_id):
            return PolicyRunResult(ok=False, policy_id=policy_id, external_calls=0)
        return PolicyRunResult(
            ok=True, policy_id=policy_id,
            policy=Policy(policy_id=policy_id),
            external_calls=0, decided=False,
        )

    def engine_info(self) -> dict:
        return {
            "runtime": "policy_runtime",
            "no_inference": True,
            "preview_only": True,
        }
