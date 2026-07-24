"""
RuntimeDaemon – Persistent Runtime Service (Daemon)

Manages all runtime services (ServiceManager, EventBus, JobQueue, Scheduler,
NotificationService) as a background daemon with graceful shutdown,
health aggregation, and cluster node registration/heartbeat.
"""

from __future__ import annotations

import asyncio
import platform
import signal
import uuid
import structlog
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .service import RuntimeService
from .service_manager import ServiceManager
from .event_bus import EventBus
from .clock import TimeProvider, SystemClock
from .health import ServiceHealth, HealthStatus
from .events import ServiceStarted, ServiceStopped, ServiceHealthChanged
from ..cluster.node import RuntimeNode, NodeStatus, NodeCapabilities
from ..cluster.node_registry import NodeRegistry


@dataclass
class DaemonConfig:
    """Configuration for the runtime daemon."""

    poll_interval: float = 5.0
    shutdown_timeout: float = 30.0
    health_check_interval: float = 60.0
    cluster_id: str = "default-cluster"
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_hostname: str = field(default_factory=lambda: platform.node() or "unknown")
    node_version: str = "1.0.0"
    node_capabilities: List[str] = field(default_factory=lambda: ["WORKER"])
    heartbeat_interval: float = 15.0
    orphan_timeout: int = 60


class RuntimeDaemon:
    """Persistent runtime daemon yang mengelola services + cluster node.

    Integrasi dengan NodeRegistry:
    - Saat start: daftarkan node (self) ke registry
    - Heartbeat loop: update last_heartbeat + health periodik
    - Saat stop: set status node ke OFFLINE
    """

    def __init__(
        self,
        config: Optional[DaemonConfig] = None,
        clock: Optional[TimeProvider] = None,
        event_bus: Optional[EventBus] = None,
        services: Optional[List[RuntimeService]] = None,
        node_registry: Optional[NodeRegistry] = None,
    ):
        self.config = config or DaemonConfig()
        self.clock = clock or SystemClock()
        self.event_bus = event_bus or EventBus()
        self._services = services or []
        self._service_manager = ServiceManager(self.event_bus)
        self._node_registry = node_registry
        self._node: Optional[RuntimeNode] = None
        self._logger = structlog.get_logger()
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._health_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    @property
    def service_manager(self) -> ServiceManager:
        return self._service_manager

    @property
    def node_registry(self) -> Optional[NodeRegistry]:
        return self._node_registry

    @property
    def node(self) -> Optional[RuntimeNode]:
        return self._node

    @property
    def running(self) -> bool:
        return self._running

    def add_service(self, service: RuntimeService) -> None:
        """Add a service to the daemon."""
        self._services.append(service)

    def _build_node(self) -> RuntimeNode:
        """Build node identity dari config."""
        return RuntimeNode(
            node_id=self.config.node_id,
            cluster_id=self.config.cluster_id,
            hostname=self.config.node_hostname,
            status=NodeStatus.INITIALIZING,
            capabilities=[
                NodeCapabilities(c) for c in self.config.node_capabilities
            ],
            version=self.config.node_version,
            started_at=self.clock.now(),
            last_heartbeat=self.clock.now(),
            metadata={
                "python_version": platform.python_version(),
                "platform": platform.platform(),
            },
        )

    async def initialize(self) -> None:
        """Initialize all services and register node."""
        for service in self._services:
            self._service_manager.register(service)

        # Register node with registry
        if self._node_registry:
            self._node = self._build_node()
            try:
                await self._node_registry.register(self._node)
                self._logger.info(
                    "node_registered",
                    node_id=self._node.node_id,
                    cluster=self._node.cluster_id,
                )
            except Exception as e:
                self._logger.error("node_register_failed", error=str(e))

        await self._service_manager.initialize_all()
        self._logger.info("daemon_initialized", services=len(self._services))

    async def start(self) -> None:
        """Start the daemon and all services."""
        if self._running:
            return

        await self.initialize()
        await self._service_manager.start_all()
        self._running = True

        # Set node ONLINE
        if self._node_registry and self._node:
            await self._node_registry.update_status(self._node.node_id, NodeStatus.ONLINE)

        # Start health check loop & heartbeat loop
        self._health_task = asyncio.create_task(self._health_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # Publish daemon started event
        await self.event_bus.publish(ServiceStarted(
            id=str(uuid.uuid4()),
            source="daemon",
            payload={
                "services": [s.name for s in self._services],
                "node_id": self._node.node_id if self._node else None,
            },
        ))

        self._logger.info(
            "daemon_started",
            services=len(self._services),
            node_id=self._node.node_id if self._node else None,
        )

    async def stop(self, signal_name: Optional[str] = None) -> None:
        """Stop the daemon gracefully."""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        # Cancel loops
        for task in (self._health_task, self._heartbeat_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._health_task = None
        self._heartbeat_task = None

        # Set node OFFLINE
        if self._node_registry and self._node:
            try:
                await self._node_registry.update_status(
                    self._node.node_id, NodeStatus.OFFLINE
                )
            except Exception as e:
                self._logger.warning("node_offline_failed", error=str(e))

        # Publish daemon stopping event
        await self.event_bus.publish(ServiceStopped(
            id=str(uuid.uuid4()),
            source="daemon",
            payload={
                "signal": signal_name,
                "services": [s.name for s in self._services],
            },
        ))

        # Stop all services (reverse order) with timeout
        try:
            await asyncio.wait_for(
                self._service_manager.stop_all(),
                timeout=self.config.shutdown_timeout,
            )
        except asyncio.TimeoutError:
            self._logger.error(
                "daemon_shutdown_timeout",
                timeout=self.config.shutdown_timeout,
            )

        self._logger.info("daemon_stopped", signal=signal_name)

    async def health(self) -> Dict[str, ServiceHealth]:
        """Aggregate health of all services."""
        if not self._running:
            return {
                "daemon": ServiceHealth(
                    status=HealthStatus.UNHEALTHY,
                    message="Daemon not running",
                    last_check=self.clock.now(),
                )
            }

        health = await self._service_manager.health_all()
        # Prepend daemon-level health
        overall = HealthStatus.HEALTHY
        messages = []
        for name, h in health.items():
            if h.status == HealthStatus.UNHEALTHY:
                overall = HealthStatus.UNHEALTHY
                messages.append(f"{name}: {h.message}")
            elif h.status == HealthStatus.DEGRADED and overall != HealthStatus.UNHEALTHY:
                overall = HealthStatus.DEGRADED
                messages.append(f"{name}: {h.message}")

        daemon_health = ServiceHealth(
            status=overall,
            message="; ".join(messages) if messages else "All services healthy",
            metrics={"service_count": len(health)},
            last_check=self.clock.now(),
        )
        result: Dict[str, ServiceHealth] = {"daemon": daemon_health}
        result.update(health)
        return result

    async def run_forever(self) -> None:
        """Run the daemon indefinitely with signal handling."""
        loop = asyncio.get_running_loop()

        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._handle_signal(s)),
                )
            except (NotImplementedError, ValueError):
                # Windows doesn't support add_signal_handler fully
                self._logger.warning("signal_handler_not_supported", signal=sig.name)

        await self.start()

        # Wait for shutdown signal
        await self._shutdown_event.wait()

        # Perform shutdown
        await self.stop()

    async def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle shutdown signals."""
        sig_name = sig.name if hasattr(sig, "name") else str(sig)
        self._logger.info("signal_received", signal=sig_name)
        self._shutdown_event.set()

    async def _health_loop(self) -> None:
        """Periodic health check loop."""
        while self._running:
            try:
                health = await self.health()
                # Publish health changed events for non-daemon services
                for service_name, service_health in health.items():
                    if service_name == "daemon":
                        continue
                    await self.event_bus.publish(ServiceHealthChanged(
                        id=str(uuid.uuid4()),
                        source="daemon",
                        payload={
                            "service_name": service_name,
                            "status": service_health.status.value,
                            "message": service_health.message or "",
                        },
                    ))
                self._logger.debug("health_check_completed", services=len(health))
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("health_check_error", error=str(e))

            await asyncio.sleep(self.config.health_check_interval)

    async def _heartbeat_loop(self) -> None:
        """Periodic heartbeat — update last_heartbeat + health di NodeRegistry."""
        if not self._node_registry or not self._node:
            return
        while self._running:
            try:
                health_data: Dict[str, Any] = {
                    "service_count": len(self._services),
                    "running": self._running,
                }
                # Collect service health for heartbeat payload
                try:
                    svc_health = await self.health()
                    for name, h in svc_health.items():
                        health_data[f"{name}_status"] = h.status.value
                except Exception:
                    pass

                await self._node_registry.heartbeat(
                    self._node.node_id, health_data
                )
                self._logger.debug("heartbeat_sent", node_id=self._node.node_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("heartbeat_error", error=str(e))

            await asyncio.sleep(self.config.heartbeat_interval)
