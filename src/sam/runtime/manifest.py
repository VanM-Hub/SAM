"""
Runtime Manifest — Phase 1

Represents the current state of the runtime.
Persisted as JSON in workspace/manifest/runtime.json.
"""

import json
import structlog
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logger = structlog.get_logger()


class RuntimeManifest:
    """Runtime Manifest — read/write runtime state to JSON file."""

    def __init__(self, workspace_path: str = "./workspace"):
        self.manifest_path = Path(workspace_path) / "manifest" / "runtime.json"
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load manifest from file. Returns default if not found or corrupt."""
        if not self.manifest_path.exists():
            return self._default()
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("manifest_load_failed", error=str(e))
            return self._default()

    def save(self, data: Dict[str, Any]) -> None:
        """Save manifest to file."""
        data["generated_at"] = datetime.utcnow().isoformat()
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("manifest_saved", path=str(self.manifest_path))

    def _default(self) -> Dict[str, Any]:
        return {
            "runtime_version": "2.0.0",
            "workspace": "default",
            "hosting": "desktop",
            "state": "INITIALIZING",
            "health": "UNKNOWN",
            "uptime": 0,
            "generated_at": datetime.utcnow().isoformat(),
        }
