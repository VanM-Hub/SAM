"""Composition exceptions for the Reference Runtime composition layer (E1-001).

All composition errors derive from CompositionException so callers can catch
a single base type. The hierarchy mirrors the validation domains:

- CompositionException        -- base
  - CompositionDefinitionError -- builder/registry construction problems
  - DependencyGraphError      -- cycle or invalid dependency edge
  - LifecycleCompositionError -- invalid lifecycle transition at runtime level
  - CompositionValidationError-- validator found a composition fault

Authority: E1-001 Reference Runtime Composition | R5-001 | I0-001
"""


class CompositionException(Exception):
    """Base exception for the runtime composition layer."""


class CompositionDefinitionError(CompositionException):
    """Raised when the composition root cannot build the runtime.

    E.g. a required unit is missing, a unit was registered twice, or an
    invalid wire reference was requested.
    """


class DependencyGraphError(CompositionException):
    """Raised when the dependency graph is invalid (cycle or bad edge)."""


class LifecycleCompositionError(CompositionException):
    """Raised when a runtime-level lifecycle transition is invalid."""


class CompositionValidationError(CompositionException):
    """Raised when CompositionValidator detects a composition fault."""
