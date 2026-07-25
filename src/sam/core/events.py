from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, Dict, Mapping
from types import MappingProxyType


class Event(BaseModel):
    """Base event model (immutable payload)."""
    id: str
    type: str
    source: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # enforce model-level immutability for fields (prevents reassignment)
        frozen = True

    def model_post_init(self, __context__):
        # Wrap the payload dict in a MappingProxyType so attempts to mutate it fail
        raw = object.__getattribute__(self, "__dict__").get("payload", {})
        object.__getattribute__(self, "__dict__")["payload"] = MappingProxyType(dict(raw))


# --- Service Events ---
class ServiceStarted(Event):
    type: str = "service.started"


class ServiceStopped(Event):
    type: str = "service.stopped"


class ServiceHealthChanged(Event):
    type: str = "service.health_changed"


# --- Job Events ---
class JobEnqueued(Event):
    type: str = "job.enqueued"


class JobStarted(Event):
    type: str = "job.started"


class JobCompleted(Event):
    type: str = "job.completed"


class JobFailed(Event):
    type: str = "job.failed"


# --- Plugin Events ---
class PluginInstalled(Event):
    type: str = "plugin.installed"


class PluginEnabled(Event):
    type: str = "plugin.enabled"


class PluginDisabled(Event):
    type: str = "plugin.disabled"


class PluginUninstalled(Event):
    type: str = "plugin.uninstalled"


# --- Notification Events ---
class NotificationCreated(Event):
    type: str = "notification.created"


# --- Health Events ---
class HealthCheckCompleted(Event):
    type: str = "health.check_completed"
