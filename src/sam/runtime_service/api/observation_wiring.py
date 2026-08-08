"""Observation Wiring — C-Phase 2 Composition Root.

Mendaftarkan semua PublicationAdapter ke PublicationRegistry
dan membuat ObservationGateway + GapResolutionCoordinator yang siap di-inject.

WP-C1.1: publication adapters
WP-C1.3: health aggregation
WP-C2.1-6: gap resolution coordinator
"""
from __future__ import annotations
from typing import Optional

from sam.observation.adapters import (
    ApprovalPublicationAdapter,
    ArtifactPublicationAdapter,
    AuditPublicationAdapter,
    ExecutionPublicationAdapter,
    KnowledgePublicationAdapter,
    MemoryPublicationAdapter,
    MissionPublicationAdapter,
    PolicyPublicationAdapter,
    RuntimeServicePublicationAdapter,
    WorkflowPublicationAdapter,
)
from sam.observation.gaps import GapResolutionCoordinator, GapResolutionReport
from sam.observation.publication import PublicationRegistry
from sam.observation.recommendation import (
    ObservationRecommendationEngine,
    OperationalRecommendationReport,
)
from sam.runtime_service.api.observation_endpoint import ObservationGateway

# C-Phase 3 (Workstream C1-C5) observers
from sam.observation.mission_intelligence import (
    MissionIntelligenceObserver,
    MissionIntelligenceReport,
)
from sam.observation.workflow_intelligence import (
    WorkflowIntelligenceObserver,
    WorkflowIntelligenceReport,
)
from sam.observation.approval_intelligence import (
    ApprovalIntelligenceObserver,
    ApprovalIntelligenceReport,
)
from sam.observation.execution_intelligence import (
    ExecutionIntelligenceObserver,
    ExecutionIntelligenceReport,
)
from sam.observation.audit_intelligence import (
    AuditIntelligenceObserver,
    AuditIntelligenceReport,
)

# C-Phase 4 (Workstream C6) Capability Intelligence observer
from sam.observation.capability_intelligence import (
    CapabilityAggregation,
    CapabilityDependencyView,
    CapabilityHealthReport,
    CapabilityIntelligenceObserver,
    CapabilityReadinessReport,
)

# C-Phase 4 (Workstream C7) Provider Intelligence observer
from sam.observation.provider_intelligence import (
    ProviderAvailabilityReport,
    ProviderConnectivityReport,
    ProviderHealthReport,
    ProviderIntelligenceObserver,
    ProviderMetrics,
    ProviderReadinessReport,
)

# C-Phase 4 (Workstream C8) Runtime Intelligence observer
from sam.observation.runtime_intelligence import (
    RuntimeDependencyView,
    RuntimeHealthMatrix,
    RuntimeIntelligenceObserver,
    RuntimeLifecycleView,
    RuntimeStatusMatrix,
)

# C-Phase 4 (Workstream C9) Platform Health Intelligence observer
from sam.observation.platform_health import (
    CrossRuntimeHealthView,
    PlatformHealthObserver,
    PlatformHealthReport,
    PlatformMetrics,
    PlatformStatusSummary,
)


# ── Singleton (module-level, immutable after wiring) ──

_registry: Optional[PublicationRegistry] = None
_gateway: Optional[ObservationGateway] = None
_gap_coordinator: Optional[GapResolutionCoordinator] = None
_recommendation_engine: Optional[ObservationRecommendationEngine] = None
_capability_intel: Optional[CapabilityIntelligenceObserver] = None
_provider_intel: Optional[ProviderIntelligenceObserver] = None
_runtime_intel: Optional[RuntimeIntelligenceObserver] = None
_platform_observer: Optional[PlatformHealthObserver] = None


def create_publication_registry() -> PublicationRegistry:
    """Factory: buat registry dengan semua adapter terdaftar."""
    registry = PublicationRegistry()
    registry.register(MissionPublicationAdapter())
    registry.register(WorkflowPublicationAdapter())
    registry.register(PolicyPublicationAdapter())
    registry.register(ExecutionPublicationAdapter())
    registry.register(AuditPublicationAdapter())
    registry.register(KnowledgePublicationAdapter())
    registry.register(MemoryPublicationAdapter())
    registry.register(ArtifactPublicationAdapter())
    registry.register(ApprovalPublicationAdapter())
    registry.register(RuntimeServicePublicationAdapter())
    return registry


def get_publication_registry() -> PublicationRegistry:
    """Dapatkan singleton registry (lazy init)."""
    global _registry
    if _registry is None:
        _registry = create_publication_registry()
    return _registry


def get_observation_gateway() -> ObservationGateway:
    """Dapatkan singleton gateway (lazy init)."""
    global _gateway
    if _gateway is None:
        _gateway = ObservationGateway(get_publication_registry())
    return _gateway


def get_gap_coordinator() -> GapResolutionCoordinator:
    """Dapatkan singleton gap resolution coordinator (lazy init)."""
    global _gap_coordinator
    if _gap_coordinator is None:
        _gap_coordinator = GapResolutionCoordinator(get_publication_registry())
    return _gap_coordinator


def get_recommendation_engine() -> ObservationRecommendationEngine:
    """Dapatkan singleton observation recommendation engine (lazy init)."""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = ObservationRecommendationEngine(
            get_publication_registry()
        )
    return _recommendation_engine


def recommend_observations() -> OperationalRecommendationReport:
    """Shortcut: generate operational recommendations dari observasi."""
    return get_recommendation_engine().recommend()


def resolve_all_gaps() -> GapResolutionReport:
    """Shortcut: resolve all 6 gaps."""
    return get_gap_coordinator().resolve_all()


# ══════════════════════════════════════════════════════════════════════
# C-Phase 3: Workstream C1-C5 Operational Intelligence wiring
# ══════════════════════════════════════════════════════════════════════
# Observer dibentuk dgn publication_registry (jalur publikasi read-only).
# Registry runtime (workflow/approval/execution/audit) TIDAK di-inject di
# sini agar wiring tdk menciptakan dependency ke runtime engine (AP-2C-001):
# observer memakai jalur publikasi yg aman dan konsisten.

_mission_intel: Optional[MissionIntelligenceObserver] = None
_workflow_intel: Optional[WorkflowIntelligenceObserver] = None
_approval_intel: Optional[ApprovalIntelligenceObserver] = None
_execution_intel: Optional[ExecutionIntelligenceObserver] = None
_audit_intel: Optional[AuditIntelligenceObserver] = None


def get_mission_intelligence_observer() -> MissionIntelligenceObserver:
    """Singleton observer Mission (read-only, jalur publikasi)."""
    global _mission_intel
    if _mission_intel is None:
        _mission_intel = MissionIntelligenceObserver(get_publication_registry())
    return _mission_intel


def observe_mission(mission_id: str = "mission") -> MissionIntelligenceReport:
    """Shortcut: laporan intelligence Mission."""
    return get_mission_intelligence_observer().dashboard(mission_id)


def get_workflow_intelligence_observer() -> WorkflowIntelligenceObserver:
    """Singleton observer Workflow (read-only, jalur publikasi)."""
    global _workflow_intel
    if _workflow_intel is None:
        _workflow_intel = WorkflowIntelligenceObserver(get_publication_registry())
    return _workflow_intel


def observe_workflows() -> WorkflowIntelligenceReport:
    """Shortcut: laporan intelligence Workflow."""
    return get_workflow_intelligence_observer().report()


def get_approval_intelligence_observer() -> ApprovalIntelligenceObserver:
    """Singleton observer Approval (read-only, jalur publikasi)."""
    global _approval_intel
    if _approval_intel is None:
        _approval_intel = ApprovalIntelligenceObserver(get_publication_registry())
    return _approval_intel


def observe_approvals() -> ApprovalIntelligenceReport:
    """Shortcut: laporan intelligence Approval."""
    return get_approval_intelligence_observer().report()


def get_execution_intelligence_observer() -> ExecutionIntelligenceObserver:
    """Singleton observer Execution (read-only, jalur publikasi)."""
    global _execution_intel
    if _execution_intel is None:
        _execution_intel = ExecutionIntelligenceObserver(get_publication_registry())
    return _execution_intel


def observe_executions() -> ExecutionIntelligenceReport:
    """Shortcut: laporan intelligence Execution."""
    return get_execution_intelligence_observer().report()


def get_audit_intelligence_observer() -> AuditIntelligenceObserver:
    """Singleton observer Audit (read-only, jalur publikasi)."""
    global _audit_intel
    if _audit_intel is None:
        _audit_intel = AuditIntelligenceObserver(get_publication_registry())
    return _audit_intel


def observe_audits(search_query: str = "") -> AuditIntelligenceReport:
    """Shortcut: laporan intelligence Audit (opsional search)."""
    return get_audit_intelligence_observer().report(search_query)


# ══════════════════════════════════════════════════════════════════════
# C-Phase 4: Workstream C6 Capability Operational Intelligence wiring
# ══════════════════════════════════════════════════════════════════════

def get_capability_intelligence_observer() -> CapabilityIntelligenceObserver:
    """Singleton observer Capability (read-only, jalur publikasi)."""
    global _capability_intel
    if _capability_intel is None:
        _capability_intel = CapabilityIntelligenceObserver(get_publication_registry())
    return _capability_intel


def observe_capabilities() -> CapabilityAggregation:
    """Shortcut: agregasi status seluruh capability (read-only)."""
    return get_capability_intelligence_observer().aggregation()


def observe_capability_readiness() -> CapabilityReadinessReport:
    """Shortcut: laporan readiness seluruh capability (read-only)."""
    return get_capability_intelligence_observer().readiness()


def observe_capability_health() -> CapabilityHealthReport:
    """Shortcut: laporan health seluruh capability (read-only)."""
    return get_capability_intelligence_observer().health()


def observe_capability_dependencies() -> CapabilityDependencyView:
    """Shortcut: graf dependency capability (read-only)."""
    return get_capability_intelligence_observer().dependency_view()


# ══════════════════════════════════════════════════════════════════════
# C-Phase 4: Workstream C7 Provider Operational Intelligence wiring
# ══════════════════════════════════════════════════════════════════════

def get_provider_intelligence_observer() -> ProviderIntelligenceObserver:
    """Singleton observer Provider (read-only, metadata provider ya tersedia)."""
    global _provider_intel
    if _provider_intel is None:
        _provider_intel = ProviderIntelligenceObserver()
    return _provider_intel


def observe_providers() -> ProviderAvailabilityReport:
    """Shortcut: laporan availability seluruh provider (read-only)."""
    return get_provider_intelligence_observer().availability()


def observe_provider_readiness() -> ProviderReadinessReport:
    """Shortcut: laporan readiness seluruh provider (read-only)."""
    return get_provider_intelligence_observer().readiness()


def observe_provider_connectivity() -> ProviderConnectivityReport:
    """Shortcut: laporan konektivitas provider (read-only)."""
    return get_provider_intelligence_observer().connectivity()


def observe_provider_health() -> ProviderHealthReport:
    """Shortcut: laporan health provider (read-only)."""
    return get_provider_intelligence_observer().health()


def observe_provider_metrics() -> ProviderMetrics:
    """Shortcut: metrik provider agregat (read-only)."""
    return get_provider_intelligence_observer().metrics()


# ══════════════════════════════════════════════════════════════════════
# C-Phase 4: Workstream C8 Runtime Operational Intelligence wiring
# ══════════════════════════════════════════════════════════════════════

def get_runtime_intelligence_observer() -> RuntimeIntelligenceObserver:
    """Singleton observer Runtime (read-only, agregasi publikasi)."""
    global _runtime_intel
    if _runtime_intel is None:
        _runtime_intel = RuntimeIntelligenceObserver(get_publication_registry())
    return _runtime_intel


def observe_runtimes() -> RuntimeStatusMatrix:
    """Shortcut: matriks status operational seluruh runtime (read-only)."""
    return get_runtime_intelligence_observer().status_matrix()


def observe_runtime_dependencies() -> RuntimeDependencyView:
    """Shortcut: graf dependency antar runtime (read-only)."""
    return get_runtime_intelligence_observer().dependency_view()


def observe_runtime_lifecycle() -> RuntimeLifecycleView:
    """Shortcut: view lifecycle capability seluruh runtime (read-only)."""
    return get_runtime_intelligence_observer().lifecycle_view()


def observe_runtime_health() -> RuntimeHealthMatrix:
    """Shortcut: matriks health seluruh runtime (read-only)."""
    return get_runtime_intelligence_observer().health_matrix()


# ══════════════════════════════════════════════════════════════════════
# C-Phase 4: Workstream C9 Platform Health Intelligence wiring
# ══════════════════════════════════════════════════════════════════════

def get_platform_health_observer() -> PlatformHealthObserver:
    """Singleton observer Platform Health (read-only, agregasi publikasi)."""
    global _platform_observer
    if _platform_observer is None:
        _platform_observer = PlatformHealthObserver(
            get_publication_registry(), get_runtime_intelligence_observer()
        )
    return _platform_observer


def observe_platform_health() -> PlatformHealthReport:
    """Shortcut: unified health platform (dihitung, bukan dipaksa)."""
    return get_platform_health_observer().health_report()


def observe_platform_metrics() -> PlatformMetrics:
    """Shortcut: metrik agregat platform (read-only)."""
    return get_platform_health_observer().metrics()


def observe_cross_runtime_health() -> CrossRuntimeHealthView:
    """Shortcut: korelasi health lintas runtime (read-only)."""
    return get_platform_health_observer().cross_runtime_health()


def observe_platform_status() -> PlatformStatusSummary:
    """Shortcut: ringkasan status platform (read-only)."""
    return get_platform_health_observer().status_summary()