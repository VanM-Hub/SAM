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


# ── Singleton (module-level, immutable after wiring) ──

_registry: Optional[PublicationRegistry] = None
_gateway: Optional[ObservationGateway] = None
_gap_coordinator: Optional[GapResolutionCoordinator] = None
_recommendation_engine: Optional[ObservationRecommendationEngine] = None


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
