"""RuntimeReport (Sprint 271).

Program D - Runtime Services & Deployment.
Laporan akhir runtime (immutable). Entry point resmi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class RuntimeReport:
    """Laporan runtime (immutable)."""
    status: str = "ready"
    services: List[str] = field(default_factory=list)
    certified: bool = False
    entry_point: str = "sam.runtime_service"
    metrics: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "services": list(self.services),
            "certified": self.certified,
            "entry_point": self.entry_point,
            "metrics": dict(self.metrics),
        }
