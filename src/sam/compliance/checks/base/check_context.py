"""CheckContext — immutable execution context passed to every check."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CheckContext:
    """Immutable context passed to every compliance check at execution time.

    Carries:
    - target_path: root directory of the project under compliance check
    - options: arbitrary configuration key-value pairs
    - check_id: optional check identifier for traceability
    """

    target_path: str
    """Root directory of the project under compliance check."""

    options: Dict[str, Any] = field(default_factory=dict)
    """Arbitrary configuration key-value pairs."""

    check_id: Optional[str] = None
    """Check identifier for traceability (optional)."""
