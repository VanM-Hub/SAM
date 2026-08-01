"""Sprint 278 - Desktop Certification: dimension (immutable)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CertificationDimension:
    """Satu dimensi sertifikasi desktop (deklaratif)."""

    name: str
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}
