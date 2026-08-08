"""Observation Layer — Read-Only Presentation & Observation.

MISSION-2C (C-Phase 1): Operational Intelligence.
Prinsip: Observe, never govern.

Modul ini tidak punya runtime, tidak punya governance, tidak punya orchestration.
Pure read-only: membaca data yang sudah dipublikasikan oleh runtime resmi.

Constraints (AP-2C-001):
- Tidak menambah runtime
- Tidak mengubah governance flow
- Tidak mengubah runtime responsibility
- Tidak mengubah Foundation
- Tidak ada business logic
- Tidak ada execution/approval/workflow/policy mutation
"""
from __future__ import annotations

# C-Phase 2: Gap Resolution exports
from sam.observation.gaps import (
    ApprovalHealthDetail,
    ApprovalHealthInspector,
    EventBusDescriptor,
    EventBusInspector,
    EventBusRegistry,
    GapResolutionCoordinator,
    GapResolutionReport,
    OperationalAnalytics,
    OperationalAnalyticsReport,
    OperationalTrend,
    PerRuntimeHealthDetail,
    PreviewAvailability,
    PreviewAvailabilityIndex,
    PreviewConsumerIndex,
    ReadinessDetail,
    ReadinessReport,
    ReadinessReporter,
    UnifiedHealthReport,
    UnifiedHealthReporter,
)

__all__ = [
    # GAP-001
    "PerRuntimeHealthDetail",
    "UnifiedHealthReport",
    "UnifiedHealthReporter",
    # GAP-002
    "PreviewAvailability",
    "PreviewAvailabilityIndex",
    "PreviewConsumerIndex",
    # GAP-003
    "EventBusDescriptor",
    "EventBusRegistry",
    "EventBusInspector",
    # GAP-004
    "ReadinessDetail",
    "ReadinessReport",
    "ReadinessReporter",
    # GAP-005
    "OperationalTrend",
    "OperationalAnalyticsReport",
    "OperationalAnalytics",
    # GAP-006
    "ApprovalHealthDetail",
    "ApprovalHealthInspector",
    # Coordinator
    "GapResolutionCoordinator",
    "GapResolutionReport",
]
