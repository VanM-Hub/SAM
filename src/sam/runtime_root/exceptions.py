"""Composition exceptions for the Reference Runtime layer (E1-001).

All composition errors derive from RuntimeCompositionError so callers can
catch a single base type. The hierarchy mirrors the validation domains:

    RuntimeCompositionError      -- base; raised by build/validation failures
      - CompositionValidationError -- validate() found a composition fault
      - DependencyGraphError       -- cycle or invalid dependency edge
      - LifecycleCompositionError  -- invalid lifecycle transition

Authority: E1-001 COMPOSITION ROOT | R5-001 | I0-001
"""


class RuntimeCompositionError(Exception):
    """Base exception for the runtime composition layer (E1-001).

    Raised when the composition root cannot build a valid runtime or when a
    lifecycle/hardening invariant is violated (missing/duplicate unit, cycle,
    invalid pipeline or health, illegal state transition).
    """


class CompositionValidationError(RuntimeCompositionError):
    """Raised when composition validation detects a fault."""


class DependencyGraphError(RuntimeCompositionError):
    """Raised when the dependency graph is invalid (cycle or bad edge)."""


class LifecycleCompositionError(RuntimeCompositionError):
    """Raised when a runtime lifecycle transition is invalid."""


# Backwards-compatible alias so callers migrating from the exploration layout
# keep working: CompositionException == RuntimeCompositionError.
CompositionException = RuntimeCompositionError
CompositionDefinitionError = RuntimeCompositionError
