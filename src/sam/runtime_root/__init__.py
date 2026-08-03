"""Reference Runtime Composition Root (E1-001) + Executable (E1-002).

Composes the seven Reference Runtime Units into a single live Runtime via a
Composition Root (`RuntimeBuilder` -> `RuntimeRoot`). This is Product
Engineering (assembly layer): it adds no features, changes no Architecture,
and changes no ADR. It only composes.

Public API (E1-001):
    RuntimeBuilder        -- composition root (instantiate/wire/validate/build).
    RuntimeContainer      -- immutable holder of exactly seven units.
    RuntimeRoot           -- public API (build/start/stop/restart/health/
                             container/is_running).
    RuntimeLifecycle      -- deterministic lifecycle
                             (CREATED -> BUILT -> STARTED -> STOPPED -> DISPOSED).
    RuntimeHealth         -- aggregate health (Healthy/Degraded/Failed).
    PIPELINE              -- canonical wiring order (no shortcut).

Executable (E1-002):
    create_runtime()      -- build a runtime.
    run_runtime()         -- build + start + report health.
    shutdown_runtime()    -- stop + dispose.

CLI (E1-002):
    python -m sam.runtime_root   -> build, start, health, stop, dispose.

Supporting types:
    HealthStatus, RuntimeState
    UnitRegistry, UnitFactory, HealthProvider (interfaces)
    RuntimeCompositionError and subclasses.

Authority chain: Constitution -> Governance -> Specification -> ADR-000..007
    -> R4-001 -> R4-002 -> R5-001 -> I0-001 -> I1-001 -> I2-001..007
    -> P0-001 -> P1-001..P1-008 -> E1-001 / E1-002.
"""

from .exceptions import (
    RuntimeCompositionError,
    CompositionValidationError,
    DependencyGraphError,
    LifecycleCompositionError,
)
from .health import HealthStatus, RuntimeHealth
from .interfaces import HealthProvider, UnitFactory, UnitRegistry
from .lifecycle import RuntimeLifecycle, RuntimeState
from .runtime_builder import CANONICAL_EDGES, PIPELINE, RuntimeBuilder
from .runtime_container import RuntimeContainer
from .runtime_root import RuntimeRoot

# E1-002 executable API.
from .main import create_runtime, run_runtime, shutdown_runtime

__all__ = [
    "RuntimeBuilder",
    "RuntimeContainer",
    "RuntimeRoot",
    "RuntimeLifecycle",
    "RuntimeState",
    "RuntimeHealth",
    "HealthStatus",
    "PIPELINE",
    "CANONICAL_EDGES",
    "UnitRegistry",
    "UnitFactory",
    "HealthProvider",
    "RuntimeCompositionError",
    "CompositionValidationError",
    "DependencyGraphError",
    "LifecycleCompositionError",
    "create_runtime",
    "run_runtime",
    "shutdown_runtime",
]
