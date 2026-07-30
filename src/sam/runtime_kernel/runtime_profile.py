"""Runtime Profile — profile engine."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.runtime_context import RuntimeProfile, RuntimeConfiguration


class ProfileEngine:
    """Engine profil — preview-only."""

    def build_profile(self, profile_id: str, name: str, mode: str = "normal",
                      capabilities: List[str] = None) -> RuntimeProfile:
        caps = capabilities or []
        return RuntimeProfile(
            profile_id=profile_id,
            name=name,
            mode=mode,
            capabilities=caps,
        )

    def add_defaults(self, profile: RuntimeProfile) -> RuntimeProfile:
        merged = list(set(list(profile.capabilities) + ["observe", "decide", "act"]))
        return RuntimeProfile(
            profile_id=profile.profile_id,
            name=profile.name,
            mode=profile.mode,
            capabilities=merged,
        )
