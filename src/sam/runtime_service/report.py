"""RuntimeReport (Sprint 269).

Program D - Runtime Services & Deployment.
Laporan runtime (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class RuntimeReport:
    """Laporan runtime (immutable)."""
    title: str
    services: List[str] = field(default_factory=list)
    sections: Dict[str, Any] = field(default_factory=dict)
    version: str = "27.0.0"

    def add(self, **sections: Any) -> "RuntimeReport":  # type: ignore
        merged = dict(self.sections)
        merged.update(sections)
        return RuntimeReport(
            title=self.title, services=list(self.services),
            sections=merged, version=self.version,
        )

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "services": list(self.services),
            "sections": dict(self.sections),
            "version": self.version,
        }
