"""Policy Engine — info engine policy (Sprint 207)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyEngineInfo:
    """Info engine policy (immutable)."""
    name: str = "policy_engine"
    no_inference: bool = True
    is_llm: bool = False
    is_ai: bool = False
    deterministic: bool = True
    preview_only: bool = True


class PolicyEngine:
    """Engine policy. Hanya menyusun DTO, tidak mengevaluasi keputusan."""

    def info(self) -> PolicyEngineInfo:
        return PolicyEngineInfo()
