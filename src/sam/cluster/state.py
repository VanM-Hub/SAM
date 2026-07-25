"""Cluster State — agregat health & load seluruh cluster secara real-time.

ClusterStateAggregator mengumpulkan state dari:
- NodeRegistry: status node (ONLINE/OFFLINE/DEGRADED), load
- JobQueue: statistik job (pending/running/failed)
- LeaderElection: leader saat ini

Digunakan oleh Daemon leader secara periodik untuk monitoring dan alerting.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from .node import RuntimeNode, NodeStatus
from .node_registry import NodeRegistry
from .leader import LeaderElection
from ..core.job import JobStatus
from ..core.job_queue import JobQueue


# ── Cluster State Model ───────────────────────────────────────────────


class ClusterState:
    """Agregat state seluruh cluster pada satu titik waktu.

    Attributes:
        cluster_id: ID cluster.
        node_count: Total jumlah node.
        online_nodes: Jumlah node ONLINE.
        offline_nodes: Jumlah node OFFLINE.
        degraded_nodes: Jumlah node DEGRADED.
        active_workflows: Jumlah workflow yang sedang berjalan (dari job queue).
        pending_jobs: Jumlah job PENDING.
        running_jobs: Jumlah job RUNNING.
        failed_jobs: Jumlah job FAILED.
        total_load: Beban total cluster (persentase perkiraan, 0.0–100.0).
        leader_id: Node ID leader, None jika tidak ada leader.
        updated_at: Waktu state dikumpulkan (UTC).
        node_details: Dict detail per node (beban, capability, dll).
    """

    def __init__(
        self,
        cluster_id: str,
        node_count: int = 0,
        online_nodes: int = 0,
        offline_nodes: int = 0,
        degraded_nodes: int = 0,
        active_workflows: int = 0,
        pending_jobs: int = 0,
        running_jobs: int = 0,
        failed_jobs: int = 0,
        total_load: float = 0.0,
        leader_id: Optional[str] = None,
        updated_at: Optional[datetime] = None,
        node_details: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.cluster_id = cluster_id
        self.node_count = node_count
        self.online_nodes = online_nodes
        self.offline_nodes = offline_nodes
        self.degraded_nodes = degraded_nodes
        self.active_workflows = active_workflows
        self.pending_jobs = pending_jobs
        self.running_jobs = running_jobs
        self.failed_jobs = failed_jobs
        self.total_load = total_load
        self.leader_id = leader_id
        self.updated_at = updated_at or datetime.utcnow()
        self.node_details = node_details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Konversi ke dictionary untuk serialisasi/resource."""
        return {
            "cluster_id": self.cluster_id,
            "node_count": self.node_count,
            "online_nodes": self.online_nodes,
            "offline_nodes": self.offline_nodes,
            "degraded_nodes": self.degraded_nodes,
            "active_workflows": self.active_workflows,
            "pending_jobs": self.pending_jobs,
            "running_jobs": self.running_jobs,
            "failed_jobs": self.failed_jobs,
            "total_load": self.total_load,
            "leader_id": self.leader_id,
            "updated_at": self.updated_at.isoformat(),
            "node_details": self.node_details,
        }

    def to_summary(self) -> Dict[str, Any]:
        """Ringkasan singkat untuk log/CLI."""
        return {
            "cluster_id": self.cluster_id,
            "nodes": f"{self.online_nodes}/{self.node_count} online",
            "jobs": f"P:{self.pending_jobs} R:{self.running_jobs} F:{self.failed_jobs}",
            "load": f"{self.total_load:.1f}%",
            "leader": self.leader_id or "none",
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return (
            f"ClusterState(cluster={self.cluster_id}, "
            f"nodes={self.online_nodes}/{self.node_count}, "
            f"jobs=P:{self.pending_jobs}/R:{self.running_jobs}, "
            f"load={self.total_load:.1f}%, "
            f"leader={self.leader_id})"
        )


# ── Cluster State Aggregator ───────────────────────────────────────────


class ClusterStateAggregator:
    """Agregat state cluster dari berbagai komponen.

    Mengumpulkan data dari NodeRegistry, JobQueue, dan LeaderElection
    untuk menghasilkan snapshot ClusterState.

    Args:
        node_registry: Registry node untuk informasi node.
        job_queue: Job queue untuk statistik job.
        leader_election: Leader election untuk informasi leader.
        cluster_id: ID cluster.
    """

    def __init__(
        self,
        node_registry: NodeRegistry,
        job_queue: JobQueue,
        leader_election: LeaderElection,
        cluster_id: str = "default-cluster",
    ):
        self._node_registry = node_registry
        self._job_queue = job_queue
        self._leader_election = leader_election
        self._cluster_id = cluster_id
        self._logger = structlog.get_logger()

    async def collect(self) -> ClusterState:
        """Kumpulkan state cluster dari semua sumber.

        Returns:
            ClusterState snapshot pada saat ini.
        """
        now = datetime.utcnow()

        # ── Node info ─────────────────────────────────────────────
        all_nodes = await self._node_registry.list()
        node_count = len(all_nodes)
        online_nodes = 0
        offline_nodes = 0
        degraded_nodes = 0
        node_details: Dict[str, Dict[str, Any]] = {}

        for node in all_nodes:
            status = node.status.value if isinstance(node.status, NodeStatus) else str(node.status)
            if status == "ONLINE":
                online_nodes += 1
            elif status == "OFFLINE":
                offline_nodes += 1
            elif status == "DEGRADED":
                degraded_nodes += 1

            node_details[node.node_id] = {
                "status": status,
                "hostname": node.hostname,
                "version": node.version,
                "capabilities": [
                    c.value if hasattr(c, "value") else str(c)
                    for c in node.capabilities
                ],
                "load": node.health.get("load", 0.0) if node.health else 0.0,
            }

        # ── Job stats ─────────────────────────────────────────────
        stats = await self._job_queue.stats() if self._job_queue else {}
        pending_jobs = stats.get("pending", 0)
        running_jobs = stats.get("running", 0)
        failed_jobs = stats.get("failed", 0)
        active_workflows = stats.get("running", 0)  # proxy: running jobs = active workflows

        # ── Total load estimation ────────────────────────────────
        total_load = self._calculate_load(
            node_details=node_details,
            pending_jobs=pending_jobs,
            running_jobs=running_jobs,
            online_nodes=online_nodes,
        )

        # ── Leader info ───────────────────────────────────────────
        leader_id: Optional[str] = None
        try:
            leader_record = await self._leader_election.get_leader()
            if leader_record:
                leader_id = leader_record.leader_id
        except Exception as e:
            self._logger.debug("leader_query_failed", error=str(e))

        state = ClusterState(
            cluster_id=self._cluster_id,
            node_count=node_count,
            online_nodes=online_nodes,
            offline_nodes=offline_nodes,
            degraded_nodes=degraded_nodes,
            active_workflows=active_workflows,
            pending_jobs=pending_jobs,
            running_jobs=running_jobs,
            failed_jobs=failed_jobs,
            total_load=total_load,
            leader_id=leader_id,
            updated_at=now,
            node_details=node_details,
        )

        self._logger.debug(
            "cluster_state_collected",
            cluster=self._cluster_id,
            nodes=f"{online_nodes}/{node_count}",
            jobs=f"P:{pending_jobs}/R:{running_jobs}/F:{failed_jobs}",
            load=f"{total_load:.1f}%",
        )

        return state

    async def get_summary(self) -> Dict[str, Any]:
        """Ringkasan cepat cluster state.

        Returns:
            Dictionary ringkasan untuk log/CLI/monitoring.
        """
        state = await self.collect()
        return state.to_summary()

    def _calculate_load(
        self,
        node_details: Dict[str, Dict[str, Any]],
        pending_jobs: int,
        running_jobs: int,
        online_nodes: int,
    ) -> float:
        """Hitung estimasi beban cluster dalam persentase (0.0–100.0).

        Beban dihitung dari:
        - Beban per-node (dari health data)
        - Jumlah pending + running jobs relatif terhadap node online
        - Semakin banyak node online, semakin tersebar beban
        """
        if online_nodes == 0:
            return 0.0

        # Average node load from health data
        node_loads = [
            d.get("load", 0.0) for d in node_details.values()
            if d.get("status") == "ONLINE"
        ]
        avg_node_load = sum(node_loads) / len(node_loads) if node_loads else 0.0

        # Job pressure: pending + running per online node
        total_active_jobs = pending_jobs + running_jobs
        job_pressure = min(total_active_jobs / (online_nodes * 5.0), 1.0)  # cap at 100%

        # Combined load: weighted average (60% node load, 40% job pressure)
        combined = (avg_node_load * 0.6 + job_pressure * 40.0)

        return round(min(combined, 100.0), 1)
