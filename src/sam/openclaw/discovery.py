"""
OpenClaw Discovery — Phase 1

Menemukan OpenClaw workspace secara otomatis melalui:
  - Lokasi yang diketahui (known locations)
  - Workspace explicit
  - Scan direktori untuk openclaw.json
"""

import os
import json
import structlog
import platform
from pathlib import Path
from typing import List, Optional
from .models import OpenClawWorkspace

logger = structlog.get_logger()


class OpenClawDiscovery:
    """Mendeteksi dan menemukan OpenClaw workspace."""

    KNOWN_LOCATIONS = [
        "./openclaw",
        "../openclaw",
        "workspace/openclaw",
        "/opt/openclaw",
        "/etc/openclaw",
        "/home/",
    ]

    def __init__(self, workspace_path: Optional[str] = None):
        self._explicit_path = workspace_path

    async def discover(self) -> List[OpenClawWorkspace]:
        found: List[OpenClawWorkspace] = []
        scanned_paths = set()

        if self._explicit_path:
            ws = await self._scan_directory(Path(self._explicit_path))
            if ws and str(ws.path) not in scanned_paths:
                found.append(ws)
                scanned_paths.add(str(ws.path))

        openclaw_config = os.environ.get("OPENCLAW_CONFIG")
        if openclaw_config:
            ws = await self._scan_directory(Path(openclaw_config))
            if ws and str(ws.path) not in scanned_paths:
                found.append(ws)
                scanned_paths.add(str(ws.path))

        if platform.system() == "Windows":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                oc_path = Path(appdata) / "openclaw"
                ws = await self._scan_directory(oc_path)
                if ws and str(ws.path) not in scanned_paths:
                    found.append(ws)
                    scanned_paths.add(str(ws.path))

        for loc in self.KNOWN_LOCATIONS:
            expanded = os.path.expanduser(loc)
            path = Path(expanded)
            if path.exists() and str(path) not in scanned_paths:
                ws = await self._scan_directory(path)
                if ws:
                    found.append(ws)
                    scanned_paths.add(str(ws.path))

        for pattern in ["**/openclaw.json", "**/.openclaw/config.json"]:
            for config_path in Path(".").glob(pattern):
                parent = config_path.parent
                if str(parent) not in scanned_paths:
                    ws = await self._scan_directory(parent)
                    if ws:
                        found.append(ws)
                        scanned_paths.add(str(ws.path))

        logger.info("openclaw_discovery_completed", count=len(found))
        return found

    async def _scan_directory(self, path: Path) -> Optional[OpenClawWorkspace]:
        if not path.exists():
            return None
        try:
            config_file = path / "openclaw.json"
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                version = config.get("version", "unknown")
                logger.info("openclaw_found", path=str(path), version=version)
                return OpenClawWorkspace(
                    path=str(path),
                    version=str(version)[:32],
                    detected=True,
                )
            dot_path = path / ".openclaw"
            if dot_path.exists():
                dot_config = dot_path / "config.json"
                if dot_config.exists():
                    with open(dot_config, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    version = config.get("version", "unknown")
                    return OpenClawWorkspace(
                        path=str(path),
                        version=version,
                        detected=True,
                    )
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("openclaw_scan_failed", path=str(path), error=str(e))
        return None


# Backward-compat alias
TelemetryDiscovery = OpenClawDiscovery

# Manky-patch: add broker_state property after class definition
_disc_orig_init = OpenClawDiscovery.__init__


def _disc_patched_init(self, workspace_path=None):
    _disc_orig_init(self, workspace_path)
    self._broker_state = "active" if workspace_path else "scanning"


OpenClawDiscovery.__init__ = _disc_patched_init


@property
def _disc_broker_state(self):
    return getattr(self, "_broker_state", "scanning")


OpenClawDiscovery.broker_state = _disc_broker_state
