"""Compliance Manifest (P1-005) — single deterministic execution config.

The manifest is the ONE source of execution configuration, connecting:
- Compliance Catalog (P1-004): what checks exist
- Compliance Framework (P1-003): which checker implements each check
- Compliance Engine (P1-002): how checks execute

Manifest is the single source of execution configuration.
No configuration is scattered inside code.
"""

from .entry import ManifestEntry
from .manifest import ComplianceManifest, ManifestError
from .loader import ManifestLoader
from .validator import (
    ManifestValidator,
    ManifestValidationIssue,
    ManifestValidationResult,
)
from .serializer import ManifestSerializer

__all__ = [
    # Model
    "ManifestEntry",
    "ComplianceManifest",
    "ManifestError",
    # Loader
    "ManifestLoader",
    # Validator
    "ManifestValidator",
    "ManifestValidationIssue",
    "ManifestValidationResult",
    # Serializer
    "ManifestSerializer",
]
