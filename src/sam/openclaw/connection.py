"""
OpenClaw Connection — Adaptor komunikasi SAM ↔ OpenClaw.

Tanpa websocket runtime — cukup kirim status periodik dan
membaca file command dari workspace.

Alur:
1. SAM tulis status ke openclaw/status/status.json
2. SAM baca openclaw/commands/ untuk perintah masuk
3. Kirim event ke TelemetryService setiap cycle

Dapat berjalan tanpa internet (file-based).
"""

import asyncio
import json
import os
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .discovery import OpenClawDiscovery

logger = structlog.get_logger()

OPENCLAW_DIR = "openclaw"
STATUS_DIR = "status"
COMMANDS_DIR = "commands"
HISTORY_FILE = "status/history.ndjson"


@dataclass
class ConnectionStatus:
    connected: bool = False
    last_sync: str = ""
    error: str = ""
    status_sent: int = 0
    commands_processed: int = 0


@dataclass
class SAMStatusReport:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "3.1.0"
    status: str = "healthy"
    protection_level: str = "healthy"
    cpu: float = 0.0
    memory: float = 0.0
    error_rate: float = 0.0
    active_work: int = 0
    pending_approvals: int = 0
    uptime_minutes: float = 0.0


class OpenClawAdapter:
    """Adaptor komunikasi SAM → OpenClaw.

    Mode offline: tulis file status.
    Mode online: juga kirim HTTP.
    """

    def __init__(self, workspace_path: str = "."):
        self.workspace = Path(workspace_path).resolve()
        self._status = ConnectionStatus()
        self._status_dir = self.workspace / OPENCLAW_DIR / STATUS_DIR
        self._commands_dir = self.workspace / OPENCLAW_DIR / COMMANDS_DIR
        self._discovery = OpenClawDiscovery()
        self._telemetry = None

    def bind_telemetry(self, telemetry):
        self._telemetry = telemetry

    async def connect(self) -> ConnectionStatus:
        """Coba konek — scan workspace, buat folder."""
        try:
            self._status_dir.mkdir(parents=True, exist_ok=True)
            self._commands_dir.mkdir(parents=True, exist_ok=True)

            workspaces = await self._discovery.discover()
            if workspaces:
                logger.info("openclaw.workspace.found", count=len(workspaces))

            self._status = ConnectionStatus(
                connected=True,
                last_sync=datetime.now().isoformat(),
            )
            logger.info("openclaw.connected", path=str(self._status_dir))
        except Exception as e:
            logger.error("openclaw.connect.failed", error=str(e))
            self._status = ConnectionStatus(connected=False, error=str(e))
        return self._status

    async def send_status(self, report: SAMStatusReport) -> bool:
        try:
            data = {
                "timestamp": report.timestamp,
                "version": report.version,
                "status": report.status,
                "protection_level": report.protection_level,
                "metrics": {
                    "cpu_percent": report.cpu,
                    "memory_percent": report.memory,
                    "error_rate": report.error_rate,
                    "active_work": report.active_work,
                    "pending_approvals": report.pending_approvals,
                    "uptime_minutes": report.uptime_minutes,
                },
            }
            status_file = self._status_dir / "status.json"
            status_file.write_text(json.dumps(data, indent=2))
            self._status.status_sent += 1

            # Append to history
            history_file = self.workspace / OPENCLAW_DIR / HISTORY_FILE
            history_file.parent.mkdir(parents=True, exist_ok=True)
            with history_file.open("a") as f:
                f.write(json.dumps({"type": "status", "data": data, "ts": report.timestamp}) + "\n")

            self._status.last_sync = datetime.now().isoformat()
            return True
        except Exception as e:
            logger.error("openclaw.send_status.failed", error=str(e))
            return False

    async def read_commands(self) -> list:
        try:
            if not self._commands_dir.exists():
                return []
            commands = []
            for f in sorted(self._commands_dir.glob("*.json"), key=lambda p: p.stat().st_mtime):
                try:
                    cmd = json.loads(f.read_text())
                    cmd["_file"] = f.name
                    commands.append(cmd)
                except Exception:
                    pass
            return commands
        except Exception as e:
            logger.error("openclaw.read_commands.failed", error=str(e))
            return []

    async def mark_command_done(self, filename: str) -> bool:
        try:
            cmd_file = self._commands_dir / filename
            if cmd_file.exists():
                done_file = cmd_file.with_suffix(".done.json")
                cmd_file.rename(done_file)
                self._status.commands_processed += 1
                return True
            return False
        except Exception as e:
            logger.error("openclaw.mark_done.failed", error=str(e))
            return False

    @property
    def state(self) -> str:
        return "connected" if self._status.connected else "disconnected"

    @property
    def is_connected(self) -> bool:
        return self._status.connected

    @property
    def status(self) -> ConnectionStatus:
        return self._status


# Backward-compat alias
OpenClawConnection = OpenClawAdapter
