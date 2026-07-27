"""
Runtime State Enum — 12 State Phase 0
"""

from enum import Enum


class RuntimeState(str, Enum):
    INITIALIZING = "initializing"
    BOOTSTRAPPING = "bootstrapping"
    RECOVERING = "recovering"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    PAUSED = "paused"
    UPDATING = "updating"
    STOPPING = "stopping"
    SHUTDOWN = "shutdown"
    CRASHED = "crashed"
    SAFE_MODE = "safe_mode"
