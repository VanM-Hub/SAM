"""Configuration Runtime (Sprint 262).

Program D - Runtime Services & Deployment.

Package ini juga menyediakan RuntimeServiceConfiguration (Sprint 261)
untuk menjaga kompatibilitas import; core di config_runtime.py.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

from .config_loader import ConfigLoader
from .config_profile import ConfigProfile
from .config_runtime import ConfigRuntime
from .config_snapshot import ConfigSnapshot
from .config_validator import ConfigValidator

CONFIG_RUNTIME_VERSION = "27.0.0"


@dataclass(frozen=True)
class RuntimeServiceConfiguration:
    """Konfigurasi service runtime (immutable). (Sprint 261)"""
    service: str
    profile: str = "default"
    options: Dict[str, object] = field(default_factory=dict)
    enabled: bool = True
    auto_start: bool = False
    max_retries: int = 0
    timeout_seconds: int = 30

    def __post_init__(self) -> None:
        if not self.service:
            raise ValueError("service is required")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.timeout_seconds < 0:
            raise ValueError("timeout_seconds cannot be negative")

    def get(self, key: str, default: object = None) -> object:
        return self.options.get(key, default)

    def as_dict(self) -> dict:
        return {
            "service": self.service,
            "profile": self.profile,
            "options": dict(self.options),
            "enabled": self.enabled,
            "auto_start": self.auto_start,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }
