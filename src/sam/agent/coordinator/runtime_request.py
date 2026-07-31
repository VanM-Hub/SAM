"""Runtime Request — request runtime (Sprint 160).

Agent Runtime — coordinator hanya menentukan runtime berikutnya. Preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RuntimeRequest:
    """Request ke runtime (immutable, preview-only)."""
    request_id: str
    mission_id: str
    runtime_name: str
    operation: str = "advance"
    params: Dict[str, Any] = field(default_factory=dict)
    external_calls: int = 0
