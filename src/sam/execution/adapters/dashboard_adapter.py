# OP-437 — Dashboard Adapter
# Python 3.8, frozen DTO, synchronous, presentation only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .adapter_registry import AdapterRegistry
from .adapter_preview import PreviewAdapter, PreviewResult


@dataclass(frozen=True)
class AdapterCard:
    total: int = 0
    healthy: int = 0
    unhealthy: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class EnvelopeCard:
    total_items: int = 0
    requires_approval: bool = True
    estimated_duration_seconds: int = 0


@dataclass(frozen=True)
class CapabilityCardDTO2:
    total_types: int = 0
    total_actions: int = 0
    types: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PreviewCardDTO2:
    operations: int = 0
    total_duration: int = 0
    impact: str = ""
    rollback_possible: bool = True


@dataclass(frozen=True)
class ValidationCardDTO2:
    passed: bool = True
    errors: int = 0
    warnings: int = 0


@dataclass(frozen=True)
class HealthCardDTO2:
    overall_healthy: bool = True
    total: int = 0
    healthy: int = 0
    unhealthy: int = 0


@dataclass(frozen=True)
class AdapterDashboard:
    adapters: AdapterCard = field(default_factory=AdapterCard)
    envelope: EnvelopeCard = field(default_factory=EnvelopeCard)
    capability: CapabilityCardDTO2 = field(default_factory=CapabilityCardDTO2)
    preview: PreviewCardDTO2 = field(default_factory=PreviewCardDTO2)
    validation: ValidationCardDTO2 = field(default_factory=ValidationCardDTO2)
    health: HealthCardDTO2 = field(default_factory=HealthCardDTO2)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AdapterDashboardBuilder:
    """Builds adapter dashboard DTOs — pure composition."""

    @staticmethod
    def build(
        registry: AdapterRegistry,
        preview_result: Optional[PreviewResult] = None,
        validation_passed: bool = True,
        validation_errors: int = 0,
        validation_warnings: int = 0,
    ) -> AdapterDashboard:
        stats = registry.get_statistics()

        adapter_card = AdapterCard(
            total=stats.total, healthy=stats.healthy,
            unhealthy=stats.unhealthy, by_type=stats.by_type,
        )

        entries = registry.list()
        cap_types = tuple(e.adapter_type for e in entries)
        cap_actions = sum(len(e.capability_names) for e in entries)
        cap_card = CapabilityCardDTO2(
            total_types=len(set(cap_types)),
            total_actions=cap_actions,
            types=cap_types,
        )

        if preview_result:
            preview_card = PreviewCardDTO2(
                operations=preview_result.total_operations,
                total_duration=preview_result.estimated_total_duration,
                impact=preview_result.overall_impact,
                rollback_possible=preview_result.rollback_possible,
            )
        else:
            preview_card = PreviewCardDTO2()

        validation_card = ValidationCardDTO2(
            passed=validation_passed,
            errors=validation_errors,
            warnings=validation_warnings,
        )

        health_card = HealthCardDTO2(
            overall_healthy=stats.unhealthy == 0,
            total=stats.total, healthy=stats.healthy,
            unhealthy=stats.unhealthy,
        )

        return AdapterDashboard(
            adapters=adapter_card,
            capability=cap_card,
            preview=preview_card,
            validation=validation_card,
            health=health_card,
        )
