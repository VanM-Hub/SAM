"""Activation Candidate — kandidat aktivasi dari builder."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ActivationCandidate:
    """Satu kandidat aktivasi yang dihasilkan builder — immutable."""
    candidate_id: str
    name: str
    candidate_type: str  # immediate, scheduled, conditional, manual, batch
    confidence: float = 0.0
    context_id: str = ""
    priority_score: float = 0.0
    estimated_duration: float = 0.0
    prerequisites: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
