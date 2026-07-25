"""Heartbeat Service — heartbeat periodik sebagai RuntimeService."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import structlog

from ..core.health import ServiceHealth, HealthStatus
from ..core.service import RuntimeService
from .node import NodeStatus
from .node_registry import NodeRegistry


class HeartbeatService(RuntimeService):
    """RuntimeService yang mengirim heartbeat periodik ke NodeRegistry.

    Menggantikan loop manual di daemon — dikelola oleh ServiceManager
    seperti service lainnya.
    """

    def __init__(
        self,
        node_registry: NodeRegistry,
        node_id: str,
        interval: int = 15,
    ):
        super().__init__()
        self._node_registry = node_registry
        self._node_id = node_id
        self._interval = interval
        self._task: Optional[asyncio.Task] = None
        self._logger = structlog.get_logger()

    @property
    def name(self) -> str:
        return "heartbeat"

    async def initialize(self) -> None:
        self._initialized = True
        self._logger.info(
            "heartbeat_initialized",
            node_id=self._node_id,
            interval=self._interval,
        )

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._task = asyncio.create_task(self._run_loop())
        self._logger.info("heartbeat_started", node_id=self._node_id)

    async def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._logger.info("heartbeat_stopped", node_id=self._node_id)

    async def health(self) -> ServiceHealth:
        if not self._started:
            return ServiceHealth(
                status=HealthStatus.UNHEALTHY,
                message="Heartbeat service not started",
            )
        if self._task and self._task.done() and not self._task.cancelled():
            exc = self._task.exception()
            if exc:
                return ServiceHealth(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Heartbeat loop crashed: {exc}",
                )
        return ServiceHealth(
            status=HealthStatus.HEALTHY,
            message=f"Heartbeat active, interval={self._interval}s",
        )

    def _collect_health(self) -> Dict[str, Any]:
        """Kumpulkan health metrics untuk payload heartbeat."""
        return {
            "load": 0.0,
            "queue_count": 0,
            "workflow_count": 0,
            "plugin_count": 0,
            "memory": 0.0,
            "cpu": 0.0,
        }

    async def _run_loop(self) -> None:
        """Loop utama: kirim heartbeat periodik."""
        while self._started:
            try:
                health_data = self._collect_health()
                await self._node_registry.heartbeat(self._node_id, health_data)
                self._logger.debug("heartbeat_sent", node_id=self._node_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("heartbeat_error", node_id=self._node_id, error=str(e))

            await asyncio.sleep(self._interval)
