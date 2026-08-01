"""Sprint 273 - Desktop Workspace: layout (immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

LayoutSpec = Tuple[str, int]  # (region, size)


@dataclass(frozen=True)
class WorkspaceLayout:
    """Layout workspace sebagai peta region immutabel."""

    name: str = "default"
    regions: Dict[str, LayoutSpec] = field(default_factory=dict)

    def with_region(self, region: str, size: int = 1) -> "WorkspaceLayout":
        regions = dict(self.regions)
        regions[region] = (region, size)
        return WorkspaceLayout(name=self.name, regions=regions)

    @property
    def region_names(self) -> Tuple[str, ...]:
        return tuple(self.regions.keys())

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "regions": {
                k: {"name": v[0], "size": v[1]}
                for k, v in self.regions.items()
            },
        }
