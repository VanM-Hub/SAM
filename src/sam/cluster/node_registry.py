"""Node Registry — mendaftarkan, menemukan, dan memonitor node dalam cluster."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

from .node import RuntimeNode, NodeStatus

# ── Error classes ───────────────────────────────────────────────────


class NodeRegistryError(Exception):
    """Base error untuk Node Registry."""


class NodeNotFoundError(NodeRegistryError):
    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(f"Node not found: {node_id}")


class NodeAlreadyRegisteredError(NodeRegistryError):
    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(f"Node already registered: {node_id}")


# ── Registry ────────────────────────────────────────────────────────


class NodeRegistry:
    """Registry untuk Runtime Nodes.

    Menggunakan Database API yang sama dengan komponen SAM lain.
    Async methods: execute(sql, params), fetch_one(sql, params), fetch_all(sql, params).
    """

    _TABLE = "cluster_nodes"

    def __init__(self, db: Any):
        self._db = db
        self._logger = structlog.get_logger()

    # ── helpers ──────────────────────────────────────────────────────

    def _row_to_node(self, row: dict) -> RuntimeNode:
        return RuntimeNode(
            node_id=row["node_id"],
            cluster_id=row["cluster_id"],
            hostname=row["hostname"],
            status=NodeStatus(row["status"]),
            capabilities=json.loads(row["capabilities"]),
            version=row["version"],
            started_at=self._parse_dt(row["started_at"]),
            last_heartbeat=self._parse_dt(row["last_heartbeat"]),
            health=json.loads(row["health"]),
            metadata=json.loads(row["metadata"]),
            labels=json.loads(row["labels"]),
        )

    def _parse_dt(self, val: Any) -> datetime:
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            return datetime.fromisoformat(val)
        return datetime.utcnow()

    def _to_json(self, val: Any) -> str:
        return json.dumps(val, default=str)

    # ── API ──────────────────────────────────────────────────────────

    async def register(self, node: RuntimeNode) -> None:
        """Daftarkan node ke registry."""
        existing = await self._db.fetch_one(
            f"SELECT node_id FROM {self._TABLE} WHERE node_id=?",
            [node.node_id],
        )
        if existing:
            raise NodeAlreadyRegisteredError(node.node_id)

        await self._db.execute(
            f"""INSERT INTO {self._TABLE}
                (node_id, cluster_id, hostname, status, capabilities,
                 version, started_at, last_heartbeat, health, metadata, labels)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                node.node_id,
                node.cluster_id,
                node.hostname,
                node.status.value if isinstance(node.status, NodeStatus) else node.status,
                self._to_json([c.value if isinstance(c, NodeCapabilities) else c for c in node.capabilities]),
                node.version,
                node.started_at.isoformat() if isinstance(node.started_at, datetime) else node.started_at,
                node.last_heartbeat.isoformat() if isinstance(node.last_heartbeat, datetime) else node.last_heartbeat,
                self._to_json(node.health),
                self._to_json(node.metadata),
                self._to_json(node.labels),
            ],
        )
        self._logger.info("node_registered", node_id=node.node_id, hostname=node.hostname)

    async def get(self, node_id: str) -> Optional[RuntimeNode]:
        """Dapatkan node by node_id."""
        row = await self._db.fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE node_id=?",
            [node_id],
        )
        if not row:
            return None
        return self._row_to_node(row) if isinstance(row, dict) else self._row_to_node(dict(row))

    async def list(self, status: Optional[NodeStatus] = None) -> List[RuntimeNode]:
        """Daftar semua node, opsional filter berdasarkan status."""
        if status:
            rows = await self._db.fetch_all(
                f"SELECT * FROM {self._TABLE} WHERE status=? ORDER BY hostname",
                [status.value if isinstance(status, NodeStatus) else status],
            )
        else:
            rows = await self._db.fetch_all(
                f"SELECT * FROM {self._TABLE} ORDER BY hostname",
            )
        return [self._row_to_node(dict(r)) if not isinstance(r, dict) else self._row_to_node(r) for r in rows]

    async def update_status(self, node_id: str, status: NodeStatus) -> None:
        """Update status node."""
        existing = await self._db.fetch_one(
            f"SELECT node_id FROM {self._TABLE} WHERE node_id=?",
            [node_id],
        )
        if not existing:
            raise NodeNotFoundError(node_id)

        await self._db.execute(
            f"UPDATE {self._TABLE} SET status=? WHERE node_id=?",
            [status.value if isinstance(status, NodeStatus) else status, node_id],
        )
        self._logger.info("node_status_updated", node_id=node_id, status=status)

    async def heartbeat(self, node_id: str, health: Dict[str, Any]) -> None:
        """Update last_heartbeat dan health node."""
        now = datetime.utcnow().isoformat()
        result = await self._db.execute(
            f"UPDATE {self._TABLE} SET last_heartbeat=?, health=? WHERE node_id=?",
            [now, self._to_json(health), node_id],
        )
        if result is not None and hasattr(result, "rowcount") and result.rowcount == 0:
            raise NodeNotFoundError(node_id)
        self._logger.debug("node_heartbeat", node_id=node_id)

    async def find_orphans(self, timeout_seconds: int = 30) -> List[RuntimeNode]:
        """Temukan node yang heartbeat-nya expired.

        Node dianggap orphan jika status ONLINE/DEGRADED/INITIALIZING tapi
        last_heartbeat lebih lama dari timeout_seconds yang lalu.
        """
        threshold_iso = (datetime.utcnow() - timedelta(seconds=timeout_seconds)).isoformat()
        rows = await self._db.fetch_all(
            f"""SELECT * FROM {self._TABLE}
                WHERE status IN ('ONLINE', 'DEGRADED', 'INITIALIZING')
                AND last_heartbeat < ?""",
            [threshold_iso],
        )
        return [self._row_to_node(dict(r)) if not isinstance(r, dict) else self._row_to_node(r) for r in rows]

    async def unregister(self, node_id: str) -> None:
        """Hapus node dari registry."""
        await self._db.execute(
            f"DELETE FROM {self._TABLE} WHERE node_id=?",
            [node_id],
        )
        self._logger.info("node_unregistered", node_id=node_id)
