"""Sprint 275 - Desktop Dashboard: layout (immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class DashboardLayout:
    """Layout dashboard sebagai peta region immutabel."""

    name: str = "default"
    regions: Dict[str, int] = field(default_factory=dict)

    def with_region(self, region: str, size: int = 1) -> "DashboardLayout":
        regions = dict(self.regions)
        regions[region] = size
        return DashboardLayout(name=self.name, regions=regions)

    @property
    def region_names(self) -> Tuple[str, ...]:
        return tuple(self.regions.keys())

    def as_dict(self) -> dict:
        return {"name": self.name, "regions": dict(self.regions)}
