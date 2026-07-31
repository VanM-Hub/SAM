"""PluginValidator (Sprint 266).

Program D - Runtime Services & Deployment.
Validator plugin metadata (deterministic).
"""
from __future__ import annotations
from typing import List

from .plugin_descriptor import PluginDescriptor


class PluginValidator:
    """Validator plugin (sync, deterministic)."""

    def validate(self, descriptor: PluginDescriptor) -> List[str]:
        errors: List[str] = []
        if not descriptor.name:
            errors.append("name is required")
        if not descriptor.version:
            errors.append("version is required")
        if descriptor.kind not in ("provider", "tool", "integration"):
            errors.append("kind must be provider|tool|integration")
        return errors

    def is_valid(self, descriptor: PluginDescriptor) -> bool:
        return not self.validate(descriptor)
