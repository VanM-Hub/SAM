"""Runtime Configuration — config engine."""
from __future__ import annotations
from typing import Any, Dict
from sam.runtime_kernel.runtime_context import RuntimeConfiguration


class ConfigurationEngine:
    """Engine konfigurasi — preview-only."""

    def create(self, config_id: str, settings: Dict[str, Any] = None,
               enabled: bool = True, timeout: float = 30.0) -> RuntimeConfiguration:
        return RuntimeConfiguration(
            config_id=config_id,
            settings=settings or {},
            enabled=enabled,
            timeout_seconds=timeout,
        )

    def merge(self, base: RuntimeConfiguration, overlay: Dict[str, Any]) -> RuntimeConfiguration:
        merged = dict(base.settings)
        merged.update(overlay)
        return RuntimeConfiguration(
            config_id=base.config_id,
            settings=merged,
            enabled=base.enabled,
            timeout_seconds=base.timeout_seconds,
        )

    def has_setting(self, config: RuntimeConfiguration, key: str) -> bool:
        return key in config.settings

    def get_setting(self, config: RuntimeConfiguration, key: str, default: Any = None) -> Any:
        return config.settings.get(key, default)
