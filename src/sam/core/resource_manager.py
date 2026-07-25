"""
Resource Manager — central registry for all runtime resources with ownership.

Provides:
- Register, get, list, update_status for RuntimeResource
- Claim, renew_lease, release for ownership management
- recover_orphaned for finding stale/expired leases
- transfer for moving ownership between nodes

All operations persist to the runtime_resources table (migration 015)
via the Database API.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

from .resource import (
    RuntimeResource,
    ResourceType,
    ResourceStatus,
    ResourceOwner,
    ResourceNotFoundError,
    ResourceVersionConflictError,
    ResourceNotOwnedError,
    ResourceOwnershipConflictError,
)


class ResourceManager:
    """Central registry managing all runtime resources with ownership leases.

    Designed to be injected via ServiceManager as a shared service.
    """

    _TABLE = "runtime_resources"

    def __init__(self, db):
        self._db = db
        self._logger = structlog.get_logger()

    # ── CRUD ─────────────────────────────────────────────────────────

    async def register(self, resource: RuntimeResource) -> None:
        """Register a new runtime resource (INSERT)."""
        sql = (
            f"INSERT INTO {self._TABLE} "
            "(id, type, name, status, owner_node_id, lease_expires_at, "
            " heartbeat_interval, data, version, created_at, updated_at, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        params = [
            resource.id,
            resource.type.value if isinstance(resource.type, ResourceType) else resource.type,
            resource.name,
            resource.status.value if isinstance(resource.status, ResourceStatus) else resource.status,
            resource.owner.node_id if resource.owner else None,
            resource.owner.lease_expires_at.isoformat() if resource.owner else None,
            resource.owner.heartbeat_interval if resource.owner else 30,
            json.dumps(resource.data, default=str),
            resource.version,
            resource.created_at.isoformat(),
            resource.updated_at.isoformat(),
            json.dumps(resource.metadata, default=str),
        ]
        await self._db_execute(sql, params)
        self._logger.debug("resource_registered", id=resource.id, type=resource.type, name=resource.name)

    async def get(self, resource_id: str) -> Optional[RuntimeResource]:
        """Get a resource by ID."""
        row = await self._db_fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE id=?", [resource_id]
        )
        if not row:
            return None
        return self._row_to_resource(row)

    async def list(
        self, type: Optional[ResourceType] = None
    ) -> List[RuntimeResource]:
        """List all resources, optionally filtered by type."""
        if type:
            type_str = type.value if isinstance(type, ResourceType) else type
            rows = await self._db_fetch_all(
                f"SELECT * FROM {self._TABLE} WHERE type=? ORDER BY updated_at DESC",
                [type_str],
            )
        else:
            rows = await self._db_fetch_all(
                f"SELECT * FROM {self._TABLE} ORDER BY type, name"
            )
        return [self._row_to_resource(r) for r in rows]

    async def update_status(
        self, resource_id: str, status: ResourceStatus
    ) -> RuntimeResource:
        """Update the status of a resource. Returns updated resource."""
        row = await self._get_row(resource_id)
        if not row:
            raise ResourceNotFoundError(resource_id)

        new_version = row["version"] + 1
        now = datetime.utcnow().isoformat()
        status_str = status.value if isinstance(status, ResourceStatus) else status

        await self._db_execute(
            f"UPDATE {self._TABLE} SET status=?, version=?, updated_at=? WHERE id=?",
            [status_str, new_version, now, resource_id],
        )

        self._logger.debug("resource_status_updated", id=resource_id, status=status_str)
        new_row = await self._get_row(resource_id)
        return self._row_to_resource(new_row)

    async def update_data(
        self, resource_id: str, data: Dict[str, Any], version: int
    ) -> RuntimeResource:
        """Update resource data with optimistic locking. Returns updated resource."""
        row = await self._get_row(resource_id)
        if not row:
            raise ResourceNotFoundError(resource_id)

        if version != row["version"]:
            raise ResourceVersionConflictError(resource_id, version, row["version"])

        new_version = version + 1
        now = datetime.utcnow().isoformat()

        await self._db_execute(
            f"UPDATE {self._TABLE} SET data=?, version=?, updated_at=? WHERE id=?",
            [json.dumps(data, default=str), new_version, now, resource_id],
        )

        new_row = await self._get_row(resource_id)
        return self._row_to_resource(new_row)

    # ── Ownership ────────────────────────────────────────────────────

    async def claim(
        self, resource_id: str, node_id: str, lease_seconds: int
    ) -> bool:
        """Claim ownership of a resource with a lease.

        If resource is unowned or lease expired, claim succeeds.
        If resource is owned by a different node with active lease, fails.

        Returns True if claimed, False if already owned by another node.
        """
        row = await self._get_row(resource_id)
        if not row:
            raise ResourceNotFoundError(resource_id)

        # Check existing ownership
        owner_node = row["owner_node_id"]
        lease_expires = row["lease_expires_at"]

        if owner_node and owner_node != node_id:
            if lease_expires:
                try:
                    expires_dt = datetime.fromisoformat(lease_expires)
                    if not datetime.utcnow() > expires_dt:
                        raise ResourceOwnershipConflictError(resource_id, owner_node, node_id)
                except (ValueError, TypeError):
                    pass  # invalid timestamp -> treat as expired

        # Claim it
        now = datetime.utcnow()
        lease_exp = now + timedelta(seconds=lease_seconds)
        new_version = row["version"] + 1

        await self._db_execute(
            f"UPDATE {self._TABLE} SET owner_node_id=?, lease_expires_at=?, "
            f"heartbeat_interval=?, version=?, updated_at=? WHERE id=?",
            [node_id, lease_exp.isoformat(), lease_seconds, new_version, now.isoformat(), resource_id],
        )

        self._logger.debug("resource_claimed", id=resource_id, node=node_id, lease_seconds=lease_seconds)
        return True

    async def renew_lease(
        self, resource_id: str, node_id: str, lease_seconds: int
    ) -> bool:
        """Renew the lease on a resource owned by this node.

        Returns True if renewed, False if not the current owner.
        """
        row = await self._get_row(resource_id)
        if not row:
            raise ResourceNotFoundError(resource_id)

        if row["owner_node_id"] != node_id:
            return False

        now = datetime.utcnow()
        lease_exp = now + timedelta(seconds=lease_seconds)
        new_version = row["version"] + 1

        await self._db_execute(
            f"UPDATE {self._TABLE} SET lease_expires_at=?, "
            f"heartbeat_interval=?, version=?, updated_at=? WHERE id=?",
            [lease_exp.isoformat(), lease_seconds, new_version, now.isoformat(), resource_id],
        )

        self._logger.debug("lease_renewed", id=resource_id, node=node_id, lease_seconds=lease_seconds)
        return True

    async def release(self, resource_id: str, node_id: str) -> None:
        """Release ownership of a resource. Only the current owner can release."""
        row = await self._get_row(resource_id)
        if not row:
            raise ResourceNotFoundError(resource_id)

        if not row["owner_node_id"]:
            raise ResourceNotOwnedError(resource_id)

        if row["owner_node_id"] != node_id:
            raise ResourceOwnershipConflictError(resource_id, row["owner_node_id"], node_id)

        new_version = row["version"] + 1
        now = datetime.utcnow().isoformat()

        await self._db_execute(
            f"UPDATE {self._TABLE} SET owner_node_id=NULL, lease_expires_at=NULL, "
            f"version=?, updated_at=? WHERE id=?",
            [new_version, now, resource_id],
        )

        self._logger.debug("resource_released", id=resource_id, node=node_id)

    async def transfer(
        self, resource_id: str, from_node: str, to_node: str, lease_seconds: int = 60
    ) -> bool:
        """Transfer ownership from one node to another.

        Only the current owner (from_node) can transfer.
        Returns True if transferred.
        """
        row = await self._get_row(resource_id)
        if not row:
            raise ResourceNotFoundError(resource_id)

        if row["owner_node_id"] != from_node:
            if row["owner_node_id"]:
                raise ResourceOwnershipConflictError(resource_id, row["owner_node_id"], from_node)
            raise ResourceNotOwnedError(resource_id)

        now = datetime.utcnow()
        lease_exp = now + timedelta(seconds=lease_seconds)
        new_version = row["version"] + 1

        await self._db_execute(
            f"UPDATE {self._TABLE} SET owner_node_id=?, lease_expires_at=?, "
            f"heartbeat_interval=?, version=?, updated_at=? WHERE id=?",
            [to_node, lease_exp.isoformat(), lease_seconds, new_version, now.isoformat(), resource_id],
        )

        self._logger.debug("resource_transferred", id=resource_id, from_node=from_node, to_node=to_node)
        return True

    async def recover_orphaned(
        self, timeout_seconds: int = 60
    ) -> List[RuntimeResource]:
        """Find all resources whose leases have expired (orphaned).

        Args:
            timeout_seconds: Lease expiration threshold (resources with
                             lease_expires_at older than now are orphaned).

        Returns:
            List of orphaned RuntimeResources (ownership cleared in DB).
        """
        now = datetime.utcnow().isoformat()
        rows = await self._db_fetch_all(
            f"SELECT * FROM {self._TABLE} "
            f"WHERE owner_node_id IS NOT NULL "
            f"AND lease_expires_at IS NOT NULL "
            f"AND lease_expires_at < ?",
            [now],
        )

        orphaned = [self._row_to_resource(r) for r in rows]

        # Clear ownership in DB
        for r in rows:
            rid = r["id"]
            new_version = r["version"] + 1
            await self._db_execute(
                f"UPDATE {self._TABLE} SET owner_node_id=NULL, lease_expires_at=NULL, "
                f"version=?, updated_at=? WHERE id=?",
                [new_version, now, rid],
            )

        self._logger.info("orphaned_resources_recovered", count=len(orphaned))
        return orphaned

    # ── Helpers ──────────────────────────────────────────────────────

    async def _get_row(self, resource_id: str) -> Optional[dict]:
        return await self._db_fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE id=?", [resource_id]
        )

    def _row_to_resource(self, row: dict) -> RuntimeResource:
        """Convert a DB row to a RuntimeResource object."""
        owner = None
        if row["owner_node_id"]:
            try:
                lease_dt = datetime.fromisoformat(row["lease_expires_at"]) if row["lease_expires_at"] else datetime.utcnow()
            except (ValueError, TypeError):
                lease_dt = datetime.utcnow()
            owner = ResourceOwner(
                node_id=row["owner_node_id"],
                lease_expires_at=lease_dt,
                heartbeat_interval=row["heartbeat_interval"] if row["heartbeat_interval"] is not None else 30,
            )

        return RuntimeResource(
            id=row["id"],
            type=ResourceType(row["type"]),
            name=row["name"],
            status=ResourceStatus(row["status"]),
            owner=owner,
            data=json.loads(row["data"]) if isinstance(row["data"], str) else {},
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else datetime.utcnow(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else datetime.utcnow(),
            metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else {},
        )

    async def _db_execute(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        await self._db.execute(sql, params)

    async def _db_fetch_one(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        return await self._db.fetch_one(sql, params)

    async def _db_fetch_all(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        return await self._db.fetch_all(sql, params)
