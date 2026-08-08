"""Observation Wiring — C-Phase 1 Composition Root.

Mendaftarkan semua PublicationAdapter ke PublicationRegistry
dan membuat ObservationGateway yang siap di-inject ke API layer.

WP-C1.1: publication adapters
WP-C1.3: health aggregation (via ObservationGateway.health_overview())
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
from sam.observation.publication import PublicationRegistry
from sam.runtime_service.api.observation_endpoint import ObservationGateway


# ── Singleton (module-level, immutable after wiring) ──

_registry: Optional[PublicationRegistry] = None
_gateway: Optional[ObservationGateway] = None


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
