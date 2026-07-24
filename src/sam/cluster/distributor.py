"""Job & Workflow Distributor — mendistribusikan job/workflow dari leader ke node cluster.

Hanya leader yang menjalankan distributor. Distributor memilih node target
berdasarkan strategy: ROUND_ROBIN, LEAST_LOADED, CAPABILITY_AWARE, AFFINITY.

Integrasi:
- NodeRegistry: query node yang ONLINE dan capability-nya
- JobQueue: ambil pending job untuk didistribusikan
- LeaderElection: hanya leader yang boleh menjalankan distributor
- Daemon: periodik memanggil distribute_jobs() dan distribute_workflows()
"""

from __future__ import annotations

import asyncio
import json
import math
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog

from .node import RuntimeNode, NodeStatus, NodeCapabilities
from .node_registry import NodeRegistry
from .leader import LeaderElection
from ..core.job import Job, JobRecord, JobStatus
from ..core.job_queue import JobQueue

# ── Constants ──────────────────────────────────────────────────────────

_DEFAULT_DB_POLL_INTERVAL = 5.0

# ── Enums ──────────────────────────────────────────────────────────────


class AssignmentStatus(str, Enum):
    """Status lifecycle untuk assignment job/workflow."""

    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AssignmentStrategy(str, Enum):
    """Strategy pemilihan node untuk assignment."""

    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_LOADED = "LEAST_LOADED"
    CAPABILITY_AWARE = "CAPABILITY_AWARE"
    AFFINITY = "AFFINITY"


# ── Models ─────────────────────────────────────────────────────────────


class JobAssignment:
    """Assignment sebuah job ke node.

    Attributes:
        job_id: ID job yang di-assign.
        assigned_node_id: Node tempat job dijalankan.
        assigned_at: Waktu assignment (UTC).
        status: Status assignment.
        attempts: Jumlah percobaan.
        error: Pesan error jika FAILED.
        completed_at: Waktu selesai.
    """

    def __init__(
        self,
        job_id: str,
        assigned_node_id: str,
        assigned_at: Optional[datetime] = None,
        status: str = "ASSIGNED",
        attempts: int = 0,
        error: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ):
        self.job_id = job_id
        self.assigned_node_id = assigned_node_id
        self.assigned_at = assigned_at or datetime.utcnow()
        self.status = status
        self.attempts = attempts
        self.error = error
        self.completed_at = completed_at


class WorkflowAssignment:
    """Assignment sebuah workflow ke node. Struktur sama dengan JobAssignment."""

    def __init__(
        self,
        workflow_id: str,
        assigned_node_id: str,
        assigned_at: Optional[datetime] = None,
        status: str = "ASSIGNED",
        attempts: int = 0,
        error: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ):
        self.workflow_id = workflow_id
        self.assigned_node_id = assigned_node_id
        self.assigned_at = assigned_at or datetime.utcnow()
        self.status = status
        self.attempts = attempts
        self.error = error
        self.completed_at = completed_at


# ── Error classes ──────────────────────────────────────────────────────


class DistributorError(Exception):
    """Base error untuk Cluster Distributor."""


class NotLeaderError(DistributorError):
    """Distributor hanya boleh berjalan di leader node."""


class NoSuitableNodeError(DistributorError):
    """Tidak ada node yang cocok untuk assignment."""


class MaxRetriesExceededError(DistributorError):
    """Job/workflow telah mencapai batas maksimum percobaan."""


# ── Cluster Distributor ────────────────────────────────────────────────


class ClusterDistributor:
    """Distributor job & workflow untuk cluster SAM.

    Hanya berjalan di leader node. Strategy pemilihan node:
    - LEAST_LOADED: pilih node dengan jumlah assignment paling sedikit.
    - CAPABILITY_AWARE: filter node berdasarkan capability yang diperlukan.
    - AFFINITY: filter node berdasarkan label match dengan job metadata.

    Args:
        node_registry: Registry node cluster.
        job_queue: Queue job.
        leader_election: Leader election untuk validasi leader.
        db: Database API untuk assignment persistence.
        strategy: Strategy pemilihan node.
        node_id: ID node (self) untuk validasi leader.
    """

    def __init__(
        self,
        node_registry: NodeRegistry,
        job_queue: JobQueue,
        leader_election: LeaderElection,
        db: Any,
        strategy: AssignmentStrategy = AssignmentStrategy.LEAST_LOADED,
        node_id: str = "",
    ):
        self._node_registry = node_registry
        self._job_queue = job_queue
        self._leader_election = leader_election
        self._db = db
        self._strategy = strategy
        self._node_id = node_id
        self._logger = structlog.get_logger()

        # Internal round-robin counter (persisten selama runtime)
        self._rr_index: int = 0

        # Tabel DB
        self._JOB_TABLE = "job_assignments"
        self._WF_TABLE = "workflow_assignments"

    # ── Public API ──────────────────────────────────────────────────────

    async def distribute_jobs(self) -> int:
        """Distribusikan semua pending job ke node yang sesuai.

        Returns:
            Jumlah job yang berhasil di-assign.
        """
        if not await self._is_leader():
            raise NotLeaderError("Only leader can distribute jobs")

        pending = await self._job_queue.list_pending()
        if not pending:
            return 0

        assigned_count = 0
        for record in pending:
            try:
                node = await self.select_node(record.job)
                if node is None:
                    continue

                await self.assign_job(record.job.id, node.node_id)
                assigned_count += 1

                self._logger.info(
                    "job_assigned",
                    job_id=record.job.id,
                    node_id=node.node_id,
                    strategy=self._strategy.value,
                )
            except NoSuitableNodeError:
                continue
            except Exception as e:
                self._logger.error(
                    "job_distribute_error",
                    job_id=record.job.id,
                    error=str(e),
                )

        return assigned_count

    async def distribute_workflows(self, workflow_ids: List[str]) -> int:
        """Distribusikan workflow ke node yang sesuai.

        Args:
            workflow_ids: Daftar ID workflow yang akan didistribusikan.

        Returns:
            Jumlah workflow yang berhasil di-assign.
        """
        if not await self._is_leader():
            raise NotLeaderError("Only leader can distribute workflows")

        assigned_count = 0
        for wf_id in workflow_ids:
            try:
                # Cari node dengan capability SCHEDULER untuk workflow
                node = await self._find_node_for_workflow(wf_id)
                if node is None:
                    continue

                await self._assign_workflow(wf_id, node.node_id)
                assigned_count += 1

                self._logger.info(
                    "workflow_assigned",
                    workflow_id=wf_id,
                    node_id=node.node_id,
                )
            except NoSuitableNodeError:
                continue
            except Exception as e:
                self._logger.error(
                    "workflow_distribute_error",
                    workflow_id=wf_id,
                    error=str(e),
                )

        return assigned_count

    async def select_node(self, job: Job) -> Optional[RuntimeNode]:
        """Pilih node terbaik untuk job berdasarkan strategy.

        Args:
            job: Job yang akan di-assign.

        Returns:
            RuntimeNode terpilih, atau None jika tidak ada node yang cocok.
        """
        # Dapatkan semua node ONLINE
        nodes = await self._node_registry.list(status=NodeStatus.ONLINE)

        if not nodes:
            raise NoSuitableNodeError("No online nodes available")

        # Filter berdasarkan capability (jika job punya requirement)
        required_cap = self._get_required_capability(job)
        if required_cap:
            nodes = [n for n in nodes if n.has_capability(required_cap)]
            if not nodes:
                raise NoSuitableNodeError(
                    f"No nodes with capability {required_cap.value}"
                )

        # Filter berdasarkan affinity (jika job punya node_selector)
        affinity = self._get_affinity(job)
        if affinity:
            matched = []
            for n in nodes:
                if self._matches_affinity(n, affinity):
                    matched.append(n)
            if matched:
                # Prefer matched nodes, tapi fallback ke semua jika tak ada match
                pass  # Gunakan filtered nodes
            else:
                # Fallback — jika affinity strict, raise error
                pass

        # Terapkan strategy selection
        return await self._apply_strategy(nodes, job)

    async def assign_job(self, job_id: str, node_id: str) -> None:
        """Assign job ke node tertentu dan update database.

        Args:
            job_id: ID job yang akan di-assign.
            node_id: Node target.
        """
        now = datetime.utcnow().isoformat()
        existing = await self._db.fetch_one(
            f"SELECT job_id FROM {self._JOB_TABLE} WHERE job_id=?",
            [job_id],
        )

        if existing:
            # Update assignment yang sudah ada (retry)
            await self._db.execute(
                f"""UPDATE {self._JOB_TABLE}
                    SET assigned_node_id=?, assigned_at=?, status=?,
                        attempts=attempts+1
                    WHERE job_id=?""",
                [node_id, now, AssignmentStatus.ASSIGNED.value, job_id],
            )
        else:
            await self._db.execute(
                f"""INSERT INTO {self._JOB_TABLE}
                    (job_id, assigned_node_id, assigned_at, status, attempts)
                    VALUES (?, ?, ?, ?, 0)""",
                [job_id, node_id, now, AssignmentStatus.ASSIGNED.value],
            )

    async def get_assignments(
        self,
        status: Optional[AssignmentStatus] = None,
    ) -> List[JobAssignment]:
        """Dapatkan daftar job assignments.

        Args:
            status: Filter berdasarkan status assignment.

        Returns:
            Daftar JobAssignment.
        """
        if status:
            rows = await self._db.fetch_all(
                f"SELECT * FROM {self._JOB_TABLE} WHERE status=? ORDER BY assigned_at DESC",
                [status.value],
            )
        else:
            rows = await self._db.fetch_all(
                f"SELECT * FROM {self._JOB_TABLE} ORDER BY assigned_at DESC",
            )

        results = []
        for row in rows:
            d = dict(row) if not isinstance(row, dict) else row
            results.append(JobAssignment(
                job_id=d["job_id"],
                assigned_node_id=d["assigned_node_id"],
                assigned_at=datetime.fromisoformat(d["assigned_at"]),
                status=d["status"],
                attempts=d["attempts"],
                error=d.get("error"),
                completed_at=datetime.fromisoformat(d["completed_at"]) if d.get("completed_at") else None,
            ))
        return results

    async def get_workflow_assignments(
        self,
        status: Optional[AssignmentStatus] = None,
    ) -> List[WorkflowAssignment]:
        """Dapatkan daftar workflow assignments."""
        if status:
            rows = await self._db.fetch_all(
                f"SELECT * FROM {self._WF_TABLE} WHERE status=? ORDER BY assigned_at DESC",
                [status.value],
            )
        else:
            rows = await self._db.fetch_all(
                f"SELECT * FROM {self._WF_TABLE} ORDER BY assigned_at DESC",
            )

        results = []
        for row in rows:
            d = dict(row) if not isinstance(row, dict) else row
            results.append(WorkflowAssignment(
                workflow_id=d["workflow_id"],
                assigned_node_id=d["assigned_node_id"],
                assigned_at=datetime.fromisoformat(d["assigned_at"]),
                status=d["status"],
                attempts=d["attempts"],
                error=d.get("error"),
                completed_at=datetime.fromisoformat(d["completed_at"]) if d.get("completed_at") else None,
            ))
        return results

    # ── Internal — Selection Strategies ────────────────────────────────

    async def _apply_strategy(
        self,
        nodes: List[RuntimeNode],
        job: Job,
    ) -> Optional[RuntimeNode]:
        """Apply strategy untuk memilih node terbaik."""
        if not nodes:
            return None

        if len(nodes) == 1:
            return nodes[0]

        if self._strategy == AssignmentStrategy.ROUND_ROBIN:
            return self._round_robin(nodes)

        if self._strategy == AssignmentStrategy.LEAST_LOADED:
            return await self._least_loaded(nodes)

        if self._strategy == AssignmentStrategy.CAPABILITY_AWARE:
            return self._capability_aware(nodes, job)

        if self._strategy == AssignmentStrategy.AFFINITY:
            return self._affinity_aware(nodes, job)

        # Default — LEAST_LOADED
        return await self._least_loaded(nodes)

    def _round_robin(self, nodes: List[RuntimeNode]) -> RuntimeNode:
        """Pilih node secara round-robin."""
        idx = self._rr_index % len(nodes)
        self._rr_index = (self._rr_index + 1) % len(nodes)
        return nodes[idx]

    async def _least_loaded(self, nodes: List[RuntimeNode]) -> Optional[RuntimeNode]:
        """Pilih node dengan jumlah assignment aktif paling sedikit."""
        if not nodes:
            return None

        # Hitung running + assigned jobs per node dari DB
        load_counts: Dict[str, int] = {}
        for node in nodes:
            count = 0
            row = await self._db.fetch_one(
                f"""SELECT COUNT(*) as cnt FROM {self._JOB_TABLE}
                    WHERE assigned_node_id=? AND status IN ('RUNNING', 'ASSIGNED')""",
                [node.node_id],
            )
            if row:
                d = dict(row) if not isinstance(row, dict) else row
                count = d["cnt"]
            load_counts[node.node_id] = count

        # Pilih dengan load terendah
        min_count = min(load_counts.values())
        candidates = [n for n in nodes if load_counts[n.node_id] == min_count]
        # Tie-breaker: prefer later nodes in the provided list to avoid
        # always favoring the first node. This helps distribute when
        # multiple nodes share the same load after incremental assignments.
        return candidates[-1] if candidates else nodes[0]

    def _capability_aware(
        self,
        nodes: List[RuntimeNode],
        job: Job,
    ) -> Optional[RuntimeNode]:
        """Pilih node berdasarkan capability yang cocok dengan job."""
        required = self._get_required_capability(job)
        if not required:
            return nodes[0]  # No specific requirement — pilih pertama

        # Filter nodes dengan capability yang dibutuhkan
        capable = [n for n in nodes if n.has_capability(required)]
        if not capable:
            return None

        # Pilih yang punya most capabilities untuk future flexibility
        capable.sort(key=lambda n: len(n.capabilities), reverse=True)
        return capable[0]

    def _affinity_aware(
        self,
        nodes: List[RuntimeNode],
        job: Job,
    ) -> Optional[RuntimeNode]:
        """Pilih node berdasarkan affinity label match."""
        affinity = self._get_affinity(job)
        if not affinity:
            return nodes[0]

        # Cari node yang labels-nya match semua affinity
        best_match = None
        best_score = -1
        for node in nodes:
            score = self._match_score(node, affinity)
            if score > best_score:
                best_score = score
                best_match = node

        return best_match if best_match else nodes[0]

    # ── Internal — Workflow-specific ───────────────────────────────────

    async def _find_node_for_workflow(
        self,
        workflow_id: str,
    ) -> Optional[RuntimeNode]:
        """Cari node untuk workflow."""
        nodes = await self._node_registry.list(status=NodeStatus.ONLINE)

        # Workflow perlu capability SCHEDULER
        capable = [n for n in nodes if n.has_capability(NodeCapabilities.SCHEDULER)]
        if not capable:
            raise NoSuitableNodeError(
                "No online nodes with SCHEDULER capability for workflow"
            )

        # LEAST_LOADED di antara capable nodes
        return await self._least_loaded(capable)

    async def _assign_workflow(self, workflow_id: str, node_id: str) -> None:
        """Assign workflow dan simpan ke DB."""
        now = datetime.utcnow().isoformat()
        existing = await self._db.fetch_one(
            f"SELECT workflow_id FROM {self._WF_TABLE} WHERE workflow_id=?",
            [workflow_id],
        )

        if existing:
            await self._db.execute(
                f"""UPDATE {self._WF_TABLE}
                    SET assigned_node_id=?, assigned_at=?, status=?,
                        attempts=attempts+1
                    WHERE workflow_id=?""",
                [node_id, now, AssignmentStatus.ASSIGNED.value, workflow_id],
            )
        else:
            await self._db.execute(
                f"""INSERT INTO {self._WF_TABLE}
                    (workflow_id, assigned_node_id, assigned_at, status, attempts)
                    VALUES (?, ?, ?, ?, 0)""",
                [workflow_id, node_id, now, AssignmentStatus.ASSIGNED.value],
            )

    # ── Helpers ────────────────────────────────────────────────────────

    async def _is_leader(self) -> bool:
        """Cek apakah node ini adalah leader yang valid."""
        if not self._node_id:
            return False
        return await self._leader_election.is_leader(self._node_id)

    @staticmethod
    def _get_required_capability(job: Job) -> Optional[NodeCapabilities]:
        """Ambil capability requirement dari job payload."""
        cap = job.payload.get("required_capability", "")
        if not cap:
            return None
        try:
            return NodeCapabilities(cap)
        except ValueError:
            return None

    @staticmethod
    def _get_affinity(job: Job) -> Optional[Dict[str, str]]:
        """Ambil affinity/selector dari job payload."""
        return job.payload.get("node_selector")

    @staticmethod
    def _matches_affinity(node: RuntimeNode, affinity: Dict[str, str]) -> bool:
        """Cek apakah node labels match semua key-value di affinity."""
        for key, val in affinity.items():
            if node.labels.get(key) != val:
                return False
        return True

    @staticmethod
    def _match_score(node: RuntimeNode, affinity: Dict[str, str]) -> int:
        """Hitung berapa banyak label node yang match affinity."""
        score = 0
        for key, val in affinity.items():
            if node.labels.get(key) == val:
                score += 1
        return score
