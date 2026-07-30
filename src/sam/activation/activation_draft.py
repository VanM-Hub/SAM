"""Activation Draft — output akhir builder untuk Sprint 82."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sam.activation.activation_candidate import ActivationCandidate


@dataclass(frozen=True)
class ActivationDraft:
    """Draft aktivasi — hasil bangunan builder."""
    draft_id: str
    context_id: str
    candidates: int = 0
    types_used: List[str] = field(default_factory=list)
    top_candidate: str = ""
    summary: str = ""
