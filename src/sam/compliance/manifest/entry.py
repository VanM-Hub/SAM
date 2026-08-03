"""ManifestEntry — per-check execution configuration for P1-005.

Each ManifestEntry binds one catalog check (P1-004) to its
execution configuration. The catalog is the source of truth for
*what* a check is; the manifest entry is the source of truth for
*how* it runs.

Python 3.8 compatible — frozen dataclass, Dict/List from typing.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from ..models.level import ComplianceLevel
from ..models.category import ComplianceCategory
from ..models.severity import Severity
from ..models.evidence_type import EvidenceType


@dataclass(frozen=True)
class ManifestEntry:
    """Single check entry within the ComplianceManifest.

    References a check_id from the P1-004 catalog and declares its
    runtime execution configuration.
    """

    # --- Identity (bound to catalog check) -----------------------------------
    check_id: str
    """Check ID — MUST match a catalog check_id from P1-004."""

    # --- Execution control ---------------------------------------------------
    enabled: bool = True
    """Whether this check participates in execution."""

    execution_order: int = 0
    """Deterministic execution order (lower runs first)."""

    checker_class: str = ""
    """P1-003 checker class name (e.g. 'FileExistsCheck')."""

    configuration: Dict[str, Any] = field(default_factory=dict)
    """Checker-specific configuration passed to the factory."""

    timeout: Optional[float] = None
    """Optional execution timeout in seconds (None = no timeout)."""

    retry_policy: str = "none"
    """Retry policy: 'none', 'once', or 'adaptive'."""

    # --- Overrides (optional, shared with catalog metadata) -------------------
    severity: Optional[Severity] = None
    """Execution-time severity override; None defers to catalog."""

    # --- Dependency graph -----------------------------------------------------
    dependencies: List[str] = field(default_factory=list)
    """Check IDs that must execute before this check."""

    # --- Search / grouping ----------------------------------------------------
    tags: List[str] = field(default_factory=list)
    """Execution-related tags (extends catalog tags)."""

    # -- Convenience -----------------------------------------------------------

    @property
    def is_enabled(self) -> bool:
        """Whether this entry participates in execution."""
        return self.enabled

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict (for JSON / ManifestSerializer)."""
        return {
            "check_id": self.check_id,
            "enabled": self.enabled,
            "execution_order": self.execution_order,
            "checker_class": self.checker_class,
            "configuration": dict(self.configuration),
            "timeout": self.timeout,
            "retry_policy": self.retry_policy,
            "severity": self.severity.value if self.severity else None,
            "dependencies": list(self.dependencies),
            "tags": list(self.tags),
        }

    def __repr__(self) -> str:
        return "ManifestEntry(check_id=%r, enabled=%r, order=%d)" % (
            self.check_id, self.enabled, self.execution_order,
        )
