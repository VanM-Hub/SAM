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
    connected: bool
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
            # Buat folder komunikasi
            self._status_dir.mkdir(parents=True, exist_ok=True)
            self._commands_dir.mkdir(parents=True, exist_ok=True)

            # Cek OpenClaw workspace
            workspaces = await self._discovery.discover()
            if workspaces:
                logger.info(
                    "openclaw.workspace.found",
                    count=len(workspaces),
                )

            self._status = ConnectionStatus(
                connected=True,
                last_sync=datetime.now().isoformat(),
            )

            logger.info("openclaw.connected", path=str(self._status_dir))

        except Exception as e:
            logger.error("openclaw.connect.failed", error=str(e))
            self._status = ConnectionStatus(
                connected=False,
                error=str(e),
            )

        return self._status

    async def send_status(self, report: SAMStatusReport) -> bool:
        """Kirim status ke OpenClaw."""
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

            # Write status file
            status_file = self._status_dir / "status.json"
            with open(status_file, "w") as f:
                json.dump(data, f, indent=2)

            # Append to history
            history_file = self._status_dir / "history.ndjson"
            with open(history_file, "a") as f:
                f.write(json.dumps(data) + "\n")

            self._status.status_sent += 1
            self._status.last_sync = report.timestamp
            self._status.error = ""

            if self._telemetry:
                self._telemetry.emit("openclaw.status.sent", {
                    "status": report.status,
                })

            return True

        except Exception as e:
            logger.error("openclaw.send.failed", error=str(e))
            self._status.error = str(e)
            return False

    async def read_commands(self) -> list:
        """Baca perintah dari OpenClaw."""
        commands = []

        try:
            if not self._commands_dir.exists():
                return commands

            for cmd_file in sorted(self._commands_dir.glob("*.json")):
                try:
                    with open(cmd_file) as f:
                        cmd = json.load(f)
                    commands.append(cmd)
                    cmd_file.unlink()  # Hapus setelah dibaca
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(
                        "openclaw.command.read.failed",
                        file=str(cmd_file),
                        error=str(e),
                    )

            if commands:
                self._status.commands_processed += len(commands)
                logger.info(
                    "openclaw.commands.processed",
                    count=len(commands),
                )

        except Exception as e:
            logger.error("openclaw.commands.error", error=str(e))

        return commands

    def get_connection_status(self) -> ConnectionStatus:
        return self._status

    async def cycle(self, experience=None):
        """Satu cycle komunikasi: kirim status + baca perintah."""
        if not self._status.connected:
            await self.connect()

        status = "healthy"
        protection_level = "healthy"

        if experience:
            try:
                home = experience.build_home()
                status = home.health.status.value
                protection_level = home.health.protection_level or status
            except Exception:
                pass

        report = SAMStatusReport(
            status=status,
            protection_level=protection_level,
        )

        await self.send_status(report)
        commands = await self.read_commands()

        return {
            "status_sent": True,
            "commands_processed": len(commands),
        }
