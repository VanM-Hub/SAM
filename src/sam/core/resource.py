"""
Runtime Resource Model — resource types, ownership, and lifecycle.

Defines:
- ResourceType enum (JOB, WORKFLOW, SERVICE, PLUGIN, KNOWLEDGE)
- ResourceStatus enum (CREATED, LOADED, ACTIVE, PAUSED, FAILED, RETIRED)
- ResourceOwner model (node_id, lease, heartbeat)
- RuntimeResource Pydantic model with optimistic locking version
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────

class ResourceType(str, Enum):
    """Categories of runtime resources managed by the ResourceManager."""
    JOB = "JOB"
    WORKFLOW = "WORKFLOW"
    SERVICE = "SERVICE"
    PLUGIN = "PLUGIN"
    KNOWLEDGE = "KNOWLEDGE"


class ResourceStatus(str, Enum):
    """Lifecycle states for a runtime resource."""
    CREATED = "CREATED"
    LOADED = "LOADED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    RETIRED = "RETIRED"


# ── Owner Model ───────────────────────────────────────────────────────

class ResourceOwner(BaseModel):
    """Ownership lease for a runtime resource bound to a node."""

    node_id: str
    lease_expires_at: datetime
    heartbeat_interval: int = Field(default=30, ge=1)

    class Config:
        frozen = True  # immutable once created
        use_enum_values = True

    @property
    def is_expired(self) -> bool:
        """Check if the lease has expired."""
        return datetime.utcnow() > self.lease_expires_at

    @property
    def remaining_seconds(self) -> float:
        """Seconds until lease expires."""
        remaining = (self.lease_expires_at - datetime.utcnow()).total_seconds()
        return max(0.0, remaining)


# ── Resource Model ────────────────────────────────────────────────────

class RuntimeResource(BaseModel):
    """A managed runtime resource with ownership and versioned state."""

    id: str
    type: ResourceType
    name: str
    status: ResourceStatus = Field(default=ResourceStatus.CREATED)
    owner: Optional[ResourceOwner] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = False  # mutable for status/owner updates
        use_enum_values = True  # store enum values as str

    @property
    def is_owned(self) -> bool:
        """Check if resource has an owner."""
        return self.owner is not None

    @property
    def is_orphaned(self) -> bool:
        """Check if resource's lease has expired."""
        return self.owner is not None and self.owner.is_expired


# ── Errors ────────────────────────────────────────────────────────────

class ResourceError(RuntimeError):
    """Base error for resource operations."""
    pass


class ResourceNotFoundError(ResourceError):
    """Resource not found."""
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"Resource not found: {resource_id}")


class ResourceVersionConflictError(ResourceError):
    """Optimistic lock version conflict."""
    def __init__(self, resource_id: str, expected: int, actual: int):
        self.resource_id = resource_id
        self.expected_version = expected
        self.actual_version = actual
        super().__init__(
            f"Version conflict for {resource_id}: expected v{expected}, actual v{actual}"
        )


class ResourceNotOwnedError(ResourceError):
    """Operation requires an owner."""
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"Resource has no owner: {resource_id}")


class ResourceOwnershipConflictError(ResourceError):
    """Resource already owned by a different node."""
    def __init__(self, resource_id: str, current_node: str, requested_node: str):
        self.resource_id = resource_id
        self.current_node = current_node
        self.requested_node = requested_node
        super().__init__(
            f"Resource {resource_id} already owned by {current_node}, "
            f"cannot claim for {requested_node}"
        )
