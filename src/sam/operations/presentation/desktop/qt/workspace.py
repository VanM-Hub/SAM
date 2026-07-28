"""WorkspaceManager — Desktop workspace model for the SAM Desktop.

Manages workspace regions, visibility, active workspace, floating support,
dock position, and persistence-ready state. No QWidget logic.

Data-only — models for QtWorkspace to consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class WorkspaceRegion:
    """A workspace region model (immutable).

    Represents one logical area in the workspace layout.
    Not a widget — metadata for persistence and state restoration.
    """

    region_id: str
    title: str
    default_area: str = "left"  # left, right, top, bottom, center
    visible: bool = True
    floating: bool = False
    floating_geometry: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h
    dock_area: str = "left"
    z_order: int = 0
    state_key: str = ""

    def with_visibility(self, visible: bool) -> WorkspaceRegion:
        return WorkspaceRegion(
            region_id=self.region_id, title=self.title,
            default_area=self.default_area, visible=visible,
            floating=self.floating,
            floating_geometry=self.floating_geometry,
            dock_area=self.dock_area, z_order=self.z_order,
            state_key=self.state_key,
        )

    def with_floating(self, floating: bool,
                      geometry: Optional[Tuple[int, int, int, int]] = None,
                      ) -> WorkspaceRegion:
        return WorkspaceRegion(
            region_id=self.region_id, title=self.title,
            default_area=self.default_area, visible=self.visible,
            floating=floating,
            floating_geometry=geometry if floating else None,
            dock_area="floating" if floating else self.dock_area,
            z_order=self.z_order, state_key=self.state_key,
        )


@dataclass
class WorkspaceState:
    """Mutable workspace state for persistence.

    Tracks active workspace, region visibility, and geometry.
    Can be serialized and restored without affecting domain.
    """

    active_workspace: str = "default"
    regions: Dict[str, WorkspaceRegion] = field(default_factory=dict)
    last_active: str = "default"
    snapshots: List[str] = field(default_factory=list)

    def register_region(self, region: WorkspaceRegion) -> None:
        self.regions[region.region_id] = region

    def set_visible(self, region_id: str, visible: bool) -> None:
        region = self.regions.get(region_id)
        if region:
            self.regions[region_id] = region.with_visibility(visible)

    def set_floating(self, region_id: str, floating: bool,
                     geometry: Optional[Tuple[int, int, int, int]] = None) -> None:
        region = self.regions.get(region_id)
        if region:
            self.regions[region_id] = region.with_floating(floating, geometry)

    def snapshot(self) -> str:
        """Take a state snapshot and return its id."""
        import json
        from datetime import datetime

        snapshot_id = datetime.now().isoformat(timespec="seconds")
        snapshot_data = self._serialize()
        self.snapshots.append(snapshot_id)
        return snapshot_id

    def _serialize(self) -> str:
        data = {
            "active_workspace": self.active_workspace,
            "last_active": self.last_active,
            "regions": {
                rid: {
                    "region_id": r.region_id,
                    "title": r.title,
                    "default_area": r.default_area,
                    "visible": r.visible,
                    "floating": r.floating,
                    "floating_geometry": r.floating_geometry,
                    "dock_area": r.dock_area,
                    "z_order": r.z_order,
                }
                for rid, r in self.regions.items()
            },
        }
        import json
        return json.dumps(data, indent=2, default=str)


class WorkspaceManager:
    """Desktop workspace manager.

    Manages workspace regions, visibility, active workspace state.
    No QWidget logic — pure model.
    """

    DEFAULT_REGIONS = [
        WorkspaceRegion("navigation", "Navigation", "left", True),
        WorkspaceRegion("mission", "Missions", "left", True),
        WorkspaceRegion("timeline", "Timeline", "right", True),
        WorkspaceRegion("notifications", "Notifications", "right", True),
        WorkspaceRegion("logs", "Logs", "bottom", True),
        WorkspaceRegion("dashboard", "Dashboard", "center", True),
    ]

    def __init__(self):
        self._state = WorkspaceState()
        self._workspaces: Dict[str, WorkspaceState] = {"default": self._state}

        # Register default regions
        for region in self.DEFAULT_REGIONS:
            self._state.register_region(region)

    # ── Region management ────────────────────────────────────────────

    def register_region(self, region: WorkspaceRegion) -> None:
        self._state.register_region(region)

    def set_visible(self, region_id: str, visible: bool) -> None:
        self._state.set_visible(region_id, visible)

    def set_floating(self, region_id: str, floating: bool,
                     geometry: Optional[Tuple[int, int, int, int]] = None) -> None:
        self._state.set_floating(region_id, floating, geometry)

    def get_region(self, region_id: str) -> Optional[WorkspaceRegion]:
        return self._state.regions.get(region_id)

    def get_all_regions(self) -> Dict[str, WorkspaceRegion]:
        return dict(self._state.regions)

    # ── Active workspace ─────────────────────────────────────────────

    @property
    def active_workspace(self) -> str:
        return self._state.active_workspace

    def set_active_workspace(self, name: str) -> None:
        if name not in self._workspaces:
            self._workspaces[name] = WorkspaceState(active_workspace=name)
        self._state.last_active = self._state.active_workspace
        self._state = self._workspaces[name]

    def save_workspace(self, name: str) -> None:
        """Save current state as a named workspace."""
        state = WorkspaceState(
            active_workspace=name,
            regions=dict(self._state.regions),
        )
        self._workspaces[name] = state

    def load_workspace(self, name: str) -> bool:
        """Load a saved workspace state."""
        if name not in self._workspaces:
            return False
        self._state.last_active = self._state.active_workspace
        self._state = self._workspaces[name]
        return True

    # ── Persistence-ready ────────────────────────────────────────────

    def snapshot(self) -> str:
        return self._state.snapshot()

    def to_dict(self) -> dict:
        return {
            "active_workspace": self._state.active_workspace,
            "last_active": self._state.last_active,
            "workspaces": list(self._workspaces.keys()),
            "regions": {
                rid: {
                    "region_id": r.region_id,
                    "title": r.title,
                    "default_area": r.default_area,
                    "visible": r.visible,
                    "floating": r.floating,
                    "floating_geometry": r.floating_geometry,
                    "dock_area": r.dock_area,
                    "z_order": r.z_order,
                }
                for rid, r in self._state.regions.items()
            },
        }

    def from_dict(self, data: dict) -> None:
        """Restore workspace state from dict."""
        ws_name = data.get("active_workspace", "default")
        state = WorkspaceState(active_workspace=ws_name)
        for rid, rdata in data.get("regions", {}).items():
            state.register_region(WorkspaceRegion(
                region_id=rdata.get("region_id", rid),
                title=rdata.get("title", rid),
                default_area=rdata.get("default_area", "left"),
                visible=rdata.get("visible", True),
                floating=rdata.get("floating", False),
                floating_geometry=rdata.get("floating_geometry"),
                dock_area=rdata.get("dock_area", "left"),
                z_order=rdata.get("z_order", 0),
                state_key=rdata.get("state_key", ""),
            ))
        self._workspaces[ws_name] = state
        self._state = state

    # ── Properties ───────────────────────────────────────────────────

    @property
    def state(self) -> WorkspaceState:
        return self._state

    @property
    def workspace_names(self) -> List[str]:
        return list(self._workspaces.keys())

    def summary(self) -> str:
        region_count = len(self._state.regions)
        visible = sum(1 for r in self._state.regions.values() if r.visible)
        return (
            f"WorkspaceManager: {region_count} regions, {visible} visible, "
            f"active={self._state.active_workspace}, "
            f"{len(self._workspaces)} workspaces cached"
        )
