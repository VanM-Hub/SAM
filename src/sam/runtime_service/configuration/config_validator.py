"""ConfigValidator (Sprint 262).

Program D - Runtime Services & Deployment.
Memvalidasi konfigurasi runtime. Deterministic.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class ConfigValidator:
    """Validator konfigurasi (sync, deterministic)."""

    REQUIRED_KEYS = ("service",)

    def _validate_value(self, value: Any) -> bool:
        # tidak menerima objek ber-network; hanya primitif & container
        if isinstance(value, (str, int, float, bool)) or value is None:
            return True
        if isinstance(value, (list, tuple, dict, set)):
            return True
        return False

    def validate(self, config: Dict[str, Any],
                 required: Optional[List[str]] = None) -> List[str]:
        errors: List[str] = []
        req = required or self.REQUIRED_KEYS
        for key in req:
            if key not in config:
                errors.append(f"missing required key: {key}")
        for key, value in config.items():
            if not self._validate_value(value):
                errors.append(f"unsupported value type for key: {key}")
        return errors

    def is_valid(self, config: Dict[str, Any]) -> bool:
        return not self.validate(config)
