"""Runtime Compliance Baseline Snapshot (P1-007).

A deterministic baseline inventory that becomes the single source of
the file inventory for all compliance checkers. Checkers read the
baseline instead of hardcoding paths or file lists.

Public API:
    BaselineSnapshot   — immutable inventory
    BaselineEntry      — one indexed file
    BaselineLoader     — scans the SAM tree
    BaselineIndex      — fast lookup index
    BaselineValidator  — integrity validation
    BaselineSerializer — JSON serialization
"""

from .entry import BaselineEntry
from .snapshot import BaselineSnapshot, ManifestError
from .loader import BaselineLoader
from .index import BaselineIndex
from .validator import (
    BaselineValidator, BaselineValidationIssue, BaselineValidationResult,
)
from .serializer import BaselineSerializer

__all__ = [
    "BaselineEntry",
    "BaselineSnapshot",
    "BaselineLoader",
    "BaselineIndex",
    "BaselineValidator",
    "BaselineValidationIssue",
    "BaselineValidationResult",
    "BaselineSerializer",
    "ManifestError",
]
