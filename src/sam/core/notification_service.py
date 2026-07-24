from __future__ import annotations

import structlog
import uuid
from typing import Optional, Dict, Any

from .service import RuntimeService
from .health import ServiceHealth, HealthStatus
from .event_bus import EventBus
from .clock import TimeProvider, SystemClock
from .events import (
    JobFailed,
    JobCompleted,
    PluginInstalled,
    PluginEnabled,
    PluginDisabled,
    PluginUninstalled,
    ServiceHealthChanged,
    HealthCheckCompleted,
    NotificationCreated,
)
from .notification import Notification, NotificationSeverity


class NotificationService(RuntimeService):
    """Notification service that listens to events and creates notifications."""

    def __init__(
        self,
        event_bus: EventBus,
        clock: Optional[TimeProvider] = None,
        console_channel: bool = True,
    ):
        self._event_bus = event_bus
        self._clock = clock or SystemClock()
        self._logger = structlog.get_logger()
        self._console_channel = console_channel
        self._notifications: list[Notification] = []
        self._subscribed = False
        self._initialized = False
        self._started = False

    @property
    def name(self) -> str:
        return "notification_service"

    async def initialize(self) -> None:
        """Subscribe to events."""
        if not self._subscribed:
            self._event_bus.subscribe("job.failed", self._on_job_failed)
            self._event_bus.subscribe("job.completed", self._on_job_completed)
            self._event_bus.subscribe("plugin.installed", self._on_plugin_installed)
            self._event_bus.subscribe("plugin.enabled", self._on_plugin_enabled)
            self._event_bus.subscribe("plugin.disabled", self._on_plugin_disabled)
            self._event_bus.subscribe("plugin.uninstalled", self._on_plugin_uninstalled)
            self._event_bus.subscribe("service.health_changed", self._on_service_health_changed)
            self._event_bus.subscribe("health.check_completed", self._on_health_check_completed)
            self._subscribed = True
            self._logger.info("notification_service_subscribed")

        self._initialized = True
        self._logger.info("notification_service_initialized")

    async def start(self) -> None:
        """Start the notification service."""
        if not self._initialized:
            raise RuntimeError("Notification service not initialized")
        self._started = True
        self._logger.info("notification_service_started")

    async def stop(self) -> None:
        """Stop the notification service."""
        self._started = False
        self._logger.info("notification_service_stopped")

    async def health(self) -> ServiceHealth:
        """Return service health."""
        return ServiceHealth(
            status=HealthStatus.HEALTHY,
            message=f"Notification service running, {len(self._notifications)} notifications",
            metrics={
                "subscribed": self._subscribed,
                "notifications": len(self._notifications),
                "console_channel": self._console_channel,
            },
            last_check=self._clock.now(),
        )

    async def _publish_notification(
        self,
        event_type: str,
        severity: NotificationSeverity,
        title: str,
        message: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create and publish a notification."""
        notification = Notification(
            type=event_type,
            severity=severity,
            title=title,
            message=message,
            source=source,
            timestamp=self._clock.now(),
            metadata=metadata or {},
        )

        self._notifications.append(notification)

        # Publish notification event
        await self._event_bus.publish(
            NotificationCreated(
                id=str(uuid.uuid4()),
                source="notification_service",
                payload=notification.model_dump(),
            )
        )

        # Console channel
        if self._console_channel:
            emoji = {
                NotificationSeverity.INFO: "\u2139\ufe0f",
                NotificationSeverity.WARNING: "\u26a0\ufe0f",
                NotificationSeverity.ERROR: "\u274c",
                NotificationSeverity.CRITICAL: "\ud83d\udea8",
            }.get(severity, "\ud83d\udce2")
            print(f"{emoji} [{severity.value.upper()}] {title}: {message}")

        self._logger.info(
            "notification_created",
            type=event_type,
            severity=severity.value,
            title=title,
        )

    # --- Event Handlers ---

    async def _on_job_failed(self, event: JobFailed) -> None:
        await self._publish_notification(
            event_type="job.failed",
            severity=NotificationSeverity.ERROR,
            title="Job Failed",
            message=f"Job {event.payload.get('job_id')} failed: {event.payload.get('error', 'Unknown error')}",
            source="job_queue",
            metadata=dict(event.payload),
        )

    async def _on_job_completed(self, event: JobCompleted) -> None:
        await self._publish_notification(
            event_type="job.completed",
            severity=NotificationSeverity.INFO,
            title="Job Completed",
            message=f"Job {event.payload.get('job_id')} completed successfully",
            source="job_queue",
            metadata=dict(event.payload),
        )

    async def _on_plugin_installed(self, event: PluginInstalled) -> None:
        await self._publish_notification(
            event_type="plugin.installed",
            severity=NotificationSeverity.INFO,
            title="Plugin Installed",
            message=f"Plugin {event.payload.get('plugin_id')} installed",
            source="plugin_manager",
            metadata=dict(event.payload),
        )

    async def _on_plugin_enabled(self, event: PluginEnabled) -> None:
        await self._publish_notification(
            event_type="plugin.enabled",
            severity=NotificationSeverity.INFO,
            title="Plugin Enabled",
            message=f"Plugin {event.payload.get('plugin_id')} enabled",
            source="plugin_manager",
            metadata=dict(event.payload),
        )

    async def _on_plugin_disabled(self, event: PluginDisabled) -> None:
        await self._publish_notification(
            event_type="plugin.disabled",
            severity=NotificationSeverity.WARNING,
            title="Plugin Disabled",
            message=f"Plugin {event.payload.get('plugin_id')} disabled",
            source="plugin_manager",
            metadata=dict(event.payload),
        )

    async def _on_plugin_uninstalled(self, event: PluginUninstalled) -> None:
        await self._publish_notification(
            event_type="plugin.uninstalled",
            severity=NotificationSeverity.INFO,
            title="Plugin Uninstalled",
            message=f"Plugin {event.payload.get('plugin_id')} uninstalled",
            source="plugin_manager",
            metadata=dict(event.payload),
        )

    async def _on_service_health_changed(self, event: ServiceHealthChanged) -> None:
        severity = (
            NotificationSeverity.WARNING
            if event.payload.get("status") == "degraded"
            else NotificationSeverity.INFO
        )
        await self._publish_notification(
            event_type="service.health_changed",
            severity=severity,
            title="Service Health Changed",
            message=f"Service {event.payload.get('service_name')} health changed to {event.payload.get('status')}",
            source="service_manager",
            metadata=dict(event.payload),
        )

    async def _on_health_check_completed(self, event: HealthCheckCompleted) -> None:
        await self._publish_notification(
            event_type="health.check_completed",
            severity=NotificationSeverity.INFO,
            title="Health Check Completed",
            message=f"Health check completed: {event.payload.get('status', 'unknown')}",
            source="health_checker",
            metadata=dict(event.payload),
        )

    def get_notifications(self, limit: int = 100) -> list[Notification]:
        """Get recent notifications."""
        return self._notifications[-limit:]
