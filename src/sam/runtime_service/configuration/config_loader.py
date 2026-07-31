"""ConfigLoader (Sprint 262).

Program D - Runtime Services & Deployment.
Memuat konfigurasi dari environment, json, yaml, atau dict.
Tidak membaca provider secara langsung.
"""
from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:  # pragma: no cover
    _HAS_YAML = False


class ConfigLoader:
    """Loader konfigurasi dari berbagai sumber (sync, deterministic)."""

    def from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return dict(data)

    def from_env(self, prefix: str = "SAM_",
                 env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        env = env if env is not None else os.environ
        result: Dict[str, Any] = {}
        for key, value in env.items():
            if key.startswith(prefix):
                result[key[len(prefix):].lower()] = value
        return result

    def from_json(self, raw: str) -> Dict[str, Any]:
        return json.loads(raw)

    def from_yaml(self, raw: str) -> Dict[str, Any]:
        if not _HAS_YAML:
            raise RuntimeError("PyYAML tidak tersedia; install untuk dukung yaml")
        parsed = yaml.safe_load(raw)
        return parsed if isinstance(parsed, dict) else {}

    def load(self, source: Any = None, format: str = "dict") -> Dict[str, Any]:
        if format == "dict":
            return self.from_dict(source if isinstance(source, dict) else {})
        if format == "json":
            return self.from_json(str(source))
        if format == "yaml":
            return self.from_yaml(str(source))
        if format == "env":
            return self.from_env()
        raise ValueError(f"unsupported format: {format}")
