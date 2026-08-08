"""Capability Status Integration — WP-C1.4.

Menyajikan status capability seluruh runtime:
- capability availability (apa yang tersedia)
- readiness level (operational | activated | planned)
- operational state (running | degraded | stopped)

READ-ONLY. Membaca dari metadata runtime yang sudah dipublikasikan.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple


@dataclass(frozen=True)
class CapabilityStatus:
    """Status capability satu runtime (immutable)."""
    runtime_id: str
    availability: str = "available"   # available | partial | unavailable
    readiness: str = "unknown"        # operational | activated | planned
    operational: str = "unknown"      # running | degraded | stopped
    has_dashboard: bool = False
    has_health: bool = False
    has_metrics: bool = False
    has_preview: bool = False
    has_timeline: bool = False
    has_lifecycle: bool = False
    has_metadata: bool = False
    has_snapshot: bool = False

    def capability_count(self) -> int:
        """Hitung capability yang tersedia."""
        caps = [
            self.has_dashboard, self.has_health, self.has_metrics,
            self.has_preview, self.has_timeline, self.has_lifecycle,
            self.has_metadata, self.has_snapshot,
        ]
        return sum(1 for c in caps if c)

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "availability": self.availability,
            "readiness": self.readiness,
            "operational": self.operational,
            "capability_count": self.capability_count(),
            "capabilities": {
                "dashboard": self.has_dashboard,
                "health": self.has_health,
                "metrics": self.has_metrics,
                "preview": self.has_preview,
                "timeline": self.has_timeline,
                "lifecycle": self.has_lifecycle,
                "metadata": self.has_metadata,
                "snapshot": self.has_snapshot,
            },
        }


@dataclass(frozen=True)
class CapabilityMatrix:
    """Matriks status capability seluruh runtime (immutable)."""
    statuses: Tuple[CapabilityStatus, ...] = field(default_factory=tuple)
    total_runtime: int = 0
    operational_count: int = 0
    activated_count: int = 0
    planned_count: int = 0

    def as_dict(self) -> dict:
        return {
            "total_runtime": self.total_runtime,
            "operational_count": self.operational_count,
            "activated_count": self.activated_count,
            "planned_count": self.planned_count,
            "statuses": [s.as_dict() for s in self.statuses],
        }


class CapabilityStatusReader:
    """Membaca status capability dari runtime (read-only).

    Menggunakan data yang sudah dipublikasikan — tidak membaca internal runtime.
    """

    _RUNTIME_CAPABILITIES: Dict[str, Dict[str, bool]] = {
        "mission":    {"dashboard": True, "health": True, "metrics": True, "preview": True, "timeline": True,  "lifecycle": False, "metadata": True, "snapshot": True},
        "workflow":   {"dashboard": True, "health": True, "metrics": True, "preview": True, "timeline": False, "lifecycle": False, "metadata": True, "snapshot": True},
        "policy":     {"dashboard": True, "health": True, "metrics": True, "preview": True, "timeline": False, "lifecycle": False, "metadata": True, "snapshot": True},
        "execution":  {"dashboard": True, "health": True, "metrics": True, "preview": True, "timeline": True,  "lifecycle": False, "metadata": True, "snapshot": True},
        "approval":   {"dashboard": True, "health": False,"metrics": False,"preview": False,"timeline": False, "lifecycle": True,  "metadata": False,"snapshot": False},
        "audit":      {"dashboard": True, "health": True, "metrics": True, "preview": True, "timeline": False, "lifecycle": False, "metadata": True, "snapshot": True},
        "knowledge":  {"dashboard": True, "health": True, "metrics": True, "preview": True, "timeline": False, "lifecycle": False, "metadata": True, "snapshot": True},
        "memory":     {"dashboard": True, "health": True, "metrics": True, "preview": True, "timeline": False, "lifecycle": False, "metadata": True, "snapshot": True},
        "artifact":   {"dashboard": True, "health": True, "metrics": True, "preview": True, "timeline": False, "lifecycle": False, "metadata": True, "snapshot": True},
        "runtime_service": {"dashboard": True, "health": True, "metrics": True, "preview": True, "timeline": False, "lifecycle": True,  "metadata": True, "snapshot": True},
    }

    _RUNTIME_READINESS: Dict[str, str] = {
        "mission": "operational", "workflow": "operational", "policy": "operational",
        "execution": "operational", "audit": "operational", "knowledge": "operational",
        "memory": "operational", "artifact": "operational", "approval": "operational",
        "runtime_service": "operational",
    }

    def read_all(self) -> CapabilityMatrix:
        statuses: List[CapabilityStatus] = []
        op, ac, pl = 0, 0, 0

        for runtime_id, caps in self._RUNTIME_CAPABILITIES.items():
            readiness = self._RUNTIME_READINESS.get(runtime_id, "planned")
            if readiness == "operational":
                op += 1
            elif readiness == "activated":
                ac += 1
            else:
                pl += 1

            status = CapabilityStatus(
                runtime_id=runtime_id,
                availability="available",
                readiness=readiness,
                operational="running",
                has_dashboard=caps.get("dashboard", False),
                has_health=caps.get("health", False),
                has_metrics=caps.get("metrics", False),
                has_preview=caps.get("preview", False),
                has_timeline=caps.get("timeline", False),
                has_lifecycle=caps.get("lifecycle", False),
                has_metadata=caps.get("metadata", False),
                has_snapshot=caps.get("snapshot", False),
            )
            statuses.append(status)

        return CapabilityMatrix(
            statuses=tuple(statuses),
            total_runtime=len(statuses),
            operational_count=op,
            activated_count=ac,
            planned_count=pl,
        )
