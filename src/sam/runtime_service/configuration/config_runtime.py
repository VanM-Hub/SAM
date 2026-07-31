"""ConfigRuntime (Sprint 262).

Program D - Runtime Services & Deployment.
Orkestrasi konfigurasi: load -> validate -> profile -> snapshot.
Tidak membaca provider secara langsung.
"""
from __future__ import annotations
from typing import Any, Dict, Optional

from .config_loader import ConfigLoader
from .config_profile import ConfigProfile
from .config_snapshot import ConfigSnapshot
from .config_validator import ConfigValidator


class ConfigRuntime:
    """Runtime konfigurasi (sync, deterministic)."""

    def __init__(self) -> None:
        self._loader = ConfigLoader()
        self._validator = ConfigValidator()
        self._profiles: Dict[str, ConfigProfile] = {}
        self._revision = 0

    def register_profile(self, profile: ConfigProfile) -> None:
        self._profiles[profile.name] = profile

    def profiles(self) -> list:
        return sorted(self._profiles.keys())

    def resolve(self, raw: Dict[str, Any], profile: str = "default",
                required: Optional[list] = None) -> ConfigSnapshot:
        cfg = self._loader.from_dict(raw)
        base: Dict[str, Any] = {}
        if profile in self._profiles:
            base = dict(self._profiles[profile].values)
        base.update(cfg)
        errors = self._validator.validate(base, required=required)
        if errors:
            raise ValueError("; ".join(errors))
        self._revision += 1
        return ConfigSnapshot(values=base, profile=profile,
                              revision=self._revision)

    @property
    def revision(self) -> int:
        return self._revision
