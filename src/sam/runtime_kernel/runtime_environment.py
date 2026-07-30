"""Runtime Environment — engine environment."""
from __future__ import annotations
from sam.runtime_kernel.runtime_context import RuntimeEnvironment, RuntimeProfile, RuntimeConfiguration


class EnvironmentEngine:
    """Engine environment — preview-only."""

    def create_profile(self, profile_id: str, name: str, mode: str = "normal") -> RuntimeProfile:
        return RuntimeProfile(profile_id=profile_id, name=name, mode=mode)

    def create_config(self, config_id: str) -> RuntimeConfiguration:
        return RuntimeConfiguration(config_id=config_id)

    def feature_check(self, env: RuntimeEnvironment, feature: str) -> bool:
        return feature in env.features

    def profile_has_capability(self, profile: RuntimeProfile, cap: str) -> bool:
        return cap in profile.capabilities
