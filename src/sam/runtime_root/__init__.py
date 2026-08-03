"""Reference Runtime Composition package (E1-001).

Connects the seven Reference Runtime Units into a single live runtime via a
composition root (RuntimeBuilder). This is Product Engineering — it adds no
features, changes no Architecture, and changes no ADR. It only composes.

Public API (E1-001):
    RuntimeBuilder            -- composition root; creates exactly one instance
                                 of each Runtime Unit and wires the chain.
    RuntimeContainer          -- public facade (start/stop/health/validate).
    RuntimeComposition        -- wired assembly (registry, graph, health,
                                 lifecycle, validation).

Supporting types:
    RuntimeLifecycle, RuntimeState
    RuntimeHealth, HealthStatus
    RuntimeRegistry
    DependencyGraph (UNIT_CHAIN)
    CompositionValidator
    CompositionException and subclasses

Authority chain: Constitution -> Governance -> Specification -> ADR-000..007
    -> R4-001 -> R4-002 -> R5-001 -> I0-001 -> I1-001 -> I2-001..007
    -> P0-001 -> P1-001..P1-008 -> E1-001.
"""

from .builder import RuntimeBuilder
from .composition import RuntimeComposition
from .container import RuntimeContainer
from .exceptions import (
    CompositionException,
    CompositionDefinitionError,
    CompositionValidationError,
    DependencyGraphError,
    LifecycleCompositionError,
)
from .graph import UNIT_CHAIN, DependencyGraph
from .health import HealthStatus, RuntimeHealth
from .lifecycle import RuntimeLifecycle, RuntimeState
from .registry import RuntimeRegistry
from .validator import CompositionValidator

__all__ = [
    "RuntimeBuilder",
    "RuntimeComposition",
    "RuntimeContainer",
    "CompositionException",
    "CompositionDefinitionError",
    "CompositionValidationError",
    "DependencyGraphError",
    "LifecycleCompositionError",
    "UNIT_CHAIN",
    "DependencyGraph",
    "HealthStatus",
    "RuntimeHealth",
    "RuntimeLifecycle",
    "RuntimeState",
    "RuntimeRegistry",
    "CompositionValidator",
]
