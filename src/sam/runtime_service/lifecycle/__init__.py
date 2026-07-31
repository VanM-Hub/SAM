"""Runtime Lifecycle (Sprint 264).

Program D - Runtime Services & Deployment.
Created -> Initializing -> Ready -> Running -> Stopping -> Stopped | Failed
"""
from __future__ import annotations

LIFECYCLE_VERSION = "27.0.0"

STATES = (
    "created",
    "initializing",
    "ready",
    "running",
    "stopping",
    "stopped",
    "failed",
)
