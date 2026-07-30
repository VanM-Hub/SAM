"""Activation Package — paket aktivasi final."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActivationPackage:
    package_id: str = ""
    plan_ref: str = ""
    strategy_ref: str = ""
    sequence_ref: str = ""
    candidate_refs: List[str] = field(default_factory=list)
    total_candidates: int = 0
    estimated_duration: float = 0.0
    confidence: float = 0.0
    status: str = "built"  # built, validated, ready, exported
    metadata: Dict[str, Any] = field(default_factory=dict)
