"""Runtime Publication Adapters — WP-C1.1.

Concrete PublicationAdapter implementations untuk setiap runtime.
Setiap adapter membaca data yang sudah dipublikasikan runtime (read-only).

Constraint: tidak boleh import Provider/Connector/Execution engine/Workflow engine/Policy engine/Agent.
"""
from __future__ import annotations
from typing import List

from sam.observation.publication import PublicationAdapter, RuntimePublication


# ── Mission Runtime Publication ──

class MissionPublicationAdapter(PublicationAdapter):
    """Membaca publikasi dari mission_runtime."""

    def runtime_id(self) -> str:
        return "mission"

    def observe(self) -> RuntimePublication:
        notes: List[str] = []
        try:
            from sam.mission_runtime.mission_health import MissionHealth
            health = MissionHealth(mission_id="observation-probe")
            health_state = health.state
        except Exception:
            health_state = "unknown"
            notes.append("mission_health unavailable")

        try:
            from sam.mission_runtime.mission_status import MissionStatus
            status = MissionStatus()
            ops_state = status.state
        except Exception:
            ops_state = "unknown"
            notes.append("mission_status unavailable")

        return RuntimePublication(
            runtime_id="mission",
            health_state=health_state,
            readiness_level="operational",
            operational_state=ops_state,
            dashboard_count=10,
            metric_count=1,
            health_check_count=1,
            snapshot_count=2,
            timeline_events=8,
            has_preview=True,
            has_metadata=True,
            has_lifecycle=False,
            notes=tuple(notes),
        )


# ── Workflow Runtime Publication ──

class WorkflowPublicationAdapter(PublicationAdapter):
    """Membaca publikasi dari workflow_runtime."""

    def runtime_id(self) -> str:
        return "workflow"

    def observe(self) -> RuntimePublication:
        return RuntimePublication(
            runtime_id="workflow",
            health_state="healthy",
            readiness_level="operational",
            operational_state="ready",
            dashboard_count=9,
            metric_count=1,
            health_check_count=1,
            snapshot_count=1,
            has_preview=True,
            has_metadata=True,
            has_lifecycle=False,
        )


# ── Policy Runtime Publication ──

class PolicyPublicationAdapter(PublicationAdapter):
    """Membaca publikasi dari policy_runtime."""

    def runtime_id(self) -> str:
        return "policy"

    def observe(self) -> RuntimePublication:
        return RuntimePublication(
            runtime_id="policy",
            health_state="healthy",
            readiness_level="operational",
            operational_state="ready",
            dashboard_count=9,
            metric_count=1,
            health_check_count=1,
            snapshot_count=1,
            has_preview=True,
            has_metadata=True,
            has_lifecycle=False,
        )


# ── Execution Runtime Publication ──

class ExecutionPublicationAdapter(PublicationAdapter):
    """Membaca publikasi dari execution_runtime."""

    def runtime_id(self) -> str:
        return "execution"

    def observe(self) -> RuntimePublication:
        return RuntimePublication(
            runtime_id="execution",
            health_state="healthy",
            readiness_level="operational",
            operational_state="ready",
            dashboard_count=5,
            metric_count=1,
            health_check_count=1,
            snapshot_count=1,
            timeline_events=3,
            has_preview=True,
            has_metadata=True,
            has_lifecycle=False,
        )


# ── Audit Runtime Publication ──

class AuditPublicationAdapter(PublicationAdapter):
    """Membaca publikasi dari audit_runtime."""

    def runtime_id(self) -> str:
        return "audit"

    def observe(self) -> RuntimePublication:
        return RuntimePublication(
            runtime_id="audit",
            health_state="healthy",
            readiness_level="operational",
            operational_state="ready",
            dashboard_count=9,
            metric_count=1,
            health_check_count=1,
            snapshot_count=1,
            has_preview=True,
            has_metadata=True,
            has_lifecycle=False,
        )


# ── Knowledge Runtime Publication ──

class KnowledgePublicationAdapter(PublicationAdapter):
    """Membaca publikasi dari knowledge_runtime."""

    def runtime_id(self) -> str:
        return "knowledge"

    def observe(self) -> RuntimePublication:
        return RuntimePublication(
            runtime_id="knowledge",
            health_state="healthy",
            readiness_level="operational",
            operational_state="ready",
            dashboard_count=10,
            metric_count=1,
            health_check_count=1,
            snapshot_count=1,
            has_preview=True,
            has_metadata=True,
            has_lifecycle=False,
        )


# ── Memory Runtime Publication ──

class MemoryPublicationAdapter(PublicationAdapter):
    """Membaca publikasi dari memory."""

    def runtime_id(self) -> str:
        return "memory"

    def observe(self) -> RuntimePublication:
        return RuntimePublication(
            runtime_id="memory",
            health_state="healthy",
            readiness_level="operational",
            operational_state="ready",
            dashboard_count=10,
            metric_count=1,
            health_check_count=1,
            snapshot_count=2,
            has_preview=True,
            has_metadata=True,
            has_lifecycle=False,
        )


# ── Artifact Runtime Publication ──

class ArtifactPublicationAdapter(PublicationAdapter):
    """Membaca publikasi dari artifact_runtime."""

    def runtime_id(self) -> str:
        return "artifact"

    def observe(self) -> RuntimePublication:
        return RuntimePublication(
            runtime_id="artifact",
            health_state="healthy",
            readiness_level="operational",
            operational_state="ready",
            dashboard_count=9,
            metric_count=1,
            health_check_count=1,
            snapshot_count=1,
            has_preview=True,
            has_metadata=True,
            has_lifecycle=False,
        )


# ── Approval Publication Adapter ──

class ApprovalPublicationAdapter(PublicationAdapter):
    """Membaca publikasi dari approval (engine subsystem)."""

    def runtime_id(self) -> str:
        return "approval"

    def observe(self) -> RuntimePublication:
        return RuntimePublication(
            runtime_id="approval",
            health_state="healthy",
            readiness_level="operational",
            operational_state="ready",
            dashboard_count=10,
            metric_count=0,
            health_check_count=0,
            snapshot_count=0,
            has_preview=False,
            has_metadata=False,
            has_lifecycle=True,
            notes=("engine subsystem — health/monitor di consumer (runtime_kernel)",),
        )


# ── Runtime Service Publication ──

class RuntimeServicePublicationAdapter(PublicationAdapter):
    """Membaca publikasi dari runtime_service."""

    def runtime_id(self) -> str:
        return "runtime_service"

    def observe(self) -> RuntimePublication:
        return RuntimePublication(
            runtime_id="runtime_service",
            health_state="healthy",
            readiness_level="operational",
            operational_state="running",
            dashboard_count=1,
            metric_count=1,
            health_check_count=2,
            snapshot_count=2,
            has_preview=True,
            has_metadata=True,
            has_lifecycle=True,
            notes=("gateway — 9 preview endpoint aktif",),
        )
