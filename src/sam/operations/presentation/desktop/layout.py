"""DesktopLayout — Layout model for the SAM Desktop.

Defines layout regions: navigation panel, content area, right panel,
log panel, and status bar. All regions are model/data only — no Qt
widget implementations.

Supports DTO-driven layout configuration.
No business logic. No rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple


class RegionPosition(Enum):
    """Layout region position within the window."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    BOTTOM = "bottom"
    TOP = "top"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class LayoutRegion:
    """A single layout region in the desktop window.

    Each region is a positioned area that will host widgets.
    The widget implementation belongs in Qt layer (Sprint 17+).
    """

    id: str
    position: RegionPosition
    title: str = ""
    visible: bool = True
    collapsible: bool = False
    collapsed: bool = False
    resizable: bool = False
    default_size: int = 0  # Width for left/right, height for bottom
    min_size: int = 0
    max_size: int = 0  # 0 = no limit


@dataclass(frozen=True)
class DesktopLayout:
    """Layout model for the SAM Desktop window.

    Immutable layout description. Defines regions and their dimensions.
    No Qt widget references. No business logic.

    Layout structure:
    ┌─────────────────────────────────────────────────────┐
    │ Menu Bar (not a region, part of window frame)       │
    ├─────────────────────────────────────────────────────┤
    │ Tool Bar (not a region, part of window frame)       │
    ├──────────┬────────────────────────┬──────────────────┤
    │          │                        │                  │
    │  LEFT    │       CENTER           │     RIGHT        │
    │  Nav     │       Content          │     Panel        │
    │          │                        │                  │
    ├──────────┴────────────────────────┴──────────────────┤
    │                   BOTTOM (Log Panel)                  │
    ├─────────────────────────────────────────────────────┤
    │ Status Bar (not a region, part of window frame)      │
    └─────────────────────────────────────────────────────┘
    """

    # Regions
    left_panel: LayoutRegion = field(default_factory=lambda: LayoutRegion(
        id="navigation", position=RegionPosition.LEFT,
        title="Navigation", collapsible=True,
        default_size=220, min_size=150, max_size=350,
    ))
    center_content: LayoutRegion = field(default_factory=lambda: LayoutRegion(
        id="content", position=RegionPosition.CENTER,
        title="Content", resizable=False,
    ))
    right_panel: LayoutRegion = field(default_factory=lambda: LayoutRegion(
        id="detail", position=RegionPosition.RIGHT,
        title="Detail Panel", collapsible=True, collapsed=True,
        resizable=True,
        default_size=300, min_size=200, max_size=500,
    ))
    bottom_panel: LayoutRegion = field(default_factory=lambda: LayoutRegion(
        id="log", position=RegionPosition.BOTTOM,
        title="Log Panel", collapsible=True, collapsed=True,
        resizable=True,
        default_size=200, min_size=100, max_size=400,
    ))

    # ── Queries ──────────────────────────────────────────────────────

    @property
    def regions(self) -> Tuple[LayoutRegion, ...]:
        return (self.left_panel, self.center_content,
                self.right_panel, self.bottom_panel)

    def get_region(self, region_id: str) -> Optional[LayoutRegion]:
        """Find a region by ID."""
        for r in self.regions:
            if r.id == region_id:
                return r
        return None

    def toggle_collapse(self, region_id: str) -> DesktopLayout:
        """Return a new layout with toggled collapsed state for a region."""
        new_regions = {}
        for r in self.regions:
            if r.id == region_id and r.collapsible:
                new_regions[r.id] = LayoutRegion(
                    id=r.id, position=r.position, title=r.title,
                    visible=r.visible, collapsible=r.collapsible,
                    collapsed=not r.collapsed,
                    resizable=r.resizable,
                    default_size=r.default_size,
                    min_size=r.min_size, max_size=r.max_size,
                )
            else:
                new_regions[r.id] = r

        return DesktopLayout(
            left_panel=new_regions.get("navigation", self.left_panel),
            center_content=new_regions.get("content", self.center_content),
            right_panel=new_regions.get("detail", self.right_panel),
            bottom_panel=new_regions.get("log", self.bottom_panel),
        )

    def set_visibility(self, region_id: str, visible: bool) -> DesktopLayout:
        """Return a new layout with updated visibility."""
        new_regions = {}
        for r in self.regions:
            if r.id == region_id:
                new_regions[r.id] = LayoutRegion(
                    id=r.id, position=r.position, title=r.title,
                    visible=visible, collapsible=r.collapsible,
                    collapsed=r.collapsed,
                    resizable=r.resizable,
                    default_size=r.default_size,
                    min_size=r.min_size, max_size=r.max_size,
                )
            else:
                new_regions[r.id] = r

        return DesktopLayout(
            left_panel=new_regions.get("navigation", self.left_panel),
            center_content=new_regions.get("content", self.center_content),
            right_panel=new_regions.get("detail", self.right_panel),
            bottom_panel=new_regions.get("log", self.bottom_panel),
        )

    def set_size(self, region_id: str, size: int) -> DesktopLayout:
        """Return a new layout with updated region size."""
        new_regions = {}
        for r in self.regions:
            if r.id == region_id and r.resizable:
                clamped = max(r.min_size, min(r.max_size or size, size))
                new_regions[r.id] = LayoutRegion(
                    id=r.id, position=r.position, title=r.title,
                    visible=r.visible, collapsible=r.collapsible,
                    collapsed=r.collapsed,
                    resizable=r.resizable,
                    default_size=clamped,
                    min_size=r.min_size, max_size=r.max_size,
                )
            else:
                new_regions[r.id] = r

        return DesktopLayout(
            left_panel=new_regions.get("navigation", self.left_panel),
            center_content=new_regions.get("content", self.center_content),
            right_panel=new_regions.get("detail", self.right_panel),
            bottom_panel=new_regions.get("log", self.bottom_panel),
        )

    @property
    def summary(self) -> str:
        parts = []
        for r in self.regions:
            state = "visible" if r.visible else "hidden"
            if r.collapsible:
                state = f"collapsed" if r.collapsed else "expanded"
            parts.append(f"{r.id}: {state}")
        return " | ".join(parts)
