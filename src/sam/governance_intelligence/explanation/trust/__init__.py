"""explanation.trust — WP-06 companion (IP-3.1-001).

Minimal, immutable trust/confidence descriptors used across explanations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrustMarker:
    """A small, deterministic trust attribute attached to a decision."""

    label: str
    evidence_backed: bool
    confidence: float

    def public_dict(self) -> dict:
        return {
            "label": self.label,
            "evidence_backed": self.evidence_backed,
            "confidence": self.confidence,
        }
