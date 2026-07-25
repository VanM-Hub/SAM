"""Cluster Identity — hierarki identitas dalam cluster SAM.

Struktur identitas:
  Cluster ID → Node ID → Workflow ID → Execution ID → Evidence ID

Setiap entitas di runtime memiliki identitas unik yang terikat dalam
hierarki cluster. Ini memungkinkan tracing end-to-end dari cluster
hingga evidence individual.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


def generate_cluster_id() -> str:
    """Generate UUID untuk cluster identity."""
    return str(uuid.uuid4())


def generate_node_id() -> str:
    """Generate UUID untuk node identity."""
    return str(uuid.uuid4())


def generate_workflow_id() -> str:
    """Generate UUID untuk workflow identity."""
    return str(uuid.uuid4())


def generate_execution_id() -> str:
    """Generate UUID untuk execution identity."""
    return str(uuid.uuid4())


def generate_evidence_id() -> str:
    """Generate UUID untuk evidence identity."""
    return str(uuid.uuid4())


class ClusterIdentity(BaseModel):
    """Hierarki identitas cluster.

    Setiap level identitas bersifat opsional — hanya level yang sudah
    terdaftar yang memiliki nilai. Root selalu cluster_id.
    """

    cluster_id: str = Field(default_factory=generate_cluster_id)
    node_id: Optional[str] = None
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    evidence_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    class Config:
        frozen = True
        extra = "forbid"

    @property
    def path(self) -> str:
        """Hierarchy path string: cluster/node/workflow/execution/evidence."""
        parts = [f"cluster:{self.cluster_id}"]
        if self.node_id:
            parts.append(f"node:{self.node_id}")
        if self.workflow_id:
            parts.append(f"workflow:{self.workflow_id}")
        if self.execution_id:
            parts.append(f"execution:{self.execution_id}")
        if self.evidence_id:
            parts.append(f"evidence:{self.evidence_id}")
        return "/".join(parts)

    @property
    def is_root(self) -> bool:
        """Only cluster_id is set (no child identities)."""
        return (
            self.node_id is None
            and self.workflow_id is None
            and self.execution_id is None
            and self.evidence_id is None
        )

    def with_node(self, node_id: str) -> "ClusterIdentity":
        """Create a new identity with node_id set."""
        return ClusterIdentity(
            cluster_id=self.cluster_id,
            node_id=node_id,
            created_at=self.created_at,
            metadata=self.metadata,
        )

    def with_workflow(self, workflow_id: str) -> "ClusterIdentity":
        """Create a new identity with workflow_id set."""
        return ClusterIdentity(
            cluster_id=self.cluster_id,
            node_id=self.node_id,
            workflow_id=workflow_id,
            created_at=self.created_at,
            metadata=self.metadata,
        )

    def with_execution(self, execution_id: str) -> "ClusterIdentity":
        """Create a new identity with execution_id set."""
        return ClusterIdentity(
            cluster_id=self.cluster_id,
            node_id=self.node_id,
            workflow_id=self.workflow_id,
            execution_id=execution_id,
            created_at=self.created_at,
            metadata=self.metadata,
        )

    def with_evidence(self, evidence_id: str) -> "ClusterIdentity":
        """Create a new identity with evidence_id set."""
        return ClusterIdentity(
            cluster_id=self.cluster_id,
            node_id=self.node_id,
            workflow_id=self.workflow_id,
            execution_id=self.execution_id,
            evidence_id=evidence_id,
            created_at=self.created_at,
            metadata=self.metadata,
        )
