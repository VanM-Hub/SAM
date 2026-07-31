"""Preview Builder — membangun preview DTO policy (Sprint 206).

TIDAK mengevaluasi, TIDAK mengambil keputusan, TIDAK inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..model.policy import Policy


@dataclass(frozen=True)
class PolicyPreviewDTO:
    """Preview policy (immutable)."""
    label: str = ""
    policy: Policy = None
    composed: bool = True
    decided: bool = False
    external_calls: int = 0

    def __post_init__(self) -> None:
        if self.policy is None:
            object.__setattr__(self, "policy", Policy(""))
        if self.decided:
            raise ValueError("preview must not decide")
        if self.external_calls != 0:
            raise ValueError("preview must have 0 external calls")


class PreviewBuilder:
    """Builder preview. Menyusun DTO — tidak pernah mengevaluasi/keputusan."""

    def build(self, label: str, policy: Policy) -> PolicyPreviewDTO:
        return PolicyPreviewDTO(label=label, policy=policy)
