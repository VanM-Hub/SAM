"""
Health Endpoint — HTTP server untuk health checks.

Digunakan oleh OpenClaw, k8s, atau monitoring eksternal.
Berjalan di port 8181 secara default.
Endpoint:
- GET /health — {"status": "ok/healthy/degraded", "version": "3.1.0", "uptime": "...", "cpu": "...", "memory": "..."}
- GET /ready — {"ready": true, "telemetry": "ok", "experience": "ok"}
"""

import asyncio
import json
import structlog
from datetime import datetime
from typing import Optional

logger = structlog.get_logger()

VERSION = "3.1.0"


class HealthServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8181):
        self.host = host
        self.port = port
        self._start_time = datetime.now()
        self._server: Optional[asyncio.AbstractServer] = None
        self._telemetry_ready = False
        self._experience_ready = False

    def mark_ready(self, telemetry: bool = True, experience: bool = True):
        self._telemetry_ready = telemetry
        self._experience_ready = experience

    async def start(self):
        self._server = await asyncio.start_server(
            self._handle, self.host, self.port
        )
        addr = self._server.sockets[0].getsockname()
        logger.info(
            "health.server.started",
            host=addr[0],
            port=addr[1],
        )

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("health.server.stopped")

    async def _handle(self, reader, writer):
        try:
            request_line = await reader.readline()
            path = request_line.decode("utf-8").strip().split(" ")[1]
        except Exception:
            writer.close()
            return

        if path == "/health":
            body = self._health()
        elif path == "/ready":
            body = self._ready()
        else:
            body = {"error": "not found"}

        data = json.dumps(body).encode("utf-8")
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: " + str(len(data)).encode() + b"\r\n"
            b"Connection: close\r\n"
            b"\r\n"
            + data
        )
        writer.write(response)
        await writer.drain()
        writer.close()

    def _health(self) -> dict:
        uptime = (datetime.now() - self._start_time).total_seconds()
        return {
            "status": "ok",
            "version": VERSION,
            "uptime_seconds": round(uptime, 1),
            "started_at": self._start_time.isoformat(),
            "timestamp": datetime.now().isoformat(),
        }

    def _ready(self) -> dict:
        return {
            "ready": self._telemetry_ready and self._experience_ready,
            "telemetry": "ok" if self._telemetry_ready else "pending",
            "experience": "ok" if self._experience_ready else "pending",
        }
