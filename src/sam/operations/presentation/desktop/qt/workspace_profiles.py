"""WorkspaceProfiles — 1-click layout profiles for SAM Desktop.

Built-in profiles:
  - Monitoring   (missions + timeline center)
  - Operations   (mission + approval + terminal)
  - Approval     (approvals + mission detail)
  - Investigation (timeline + logs + audit)

All profiles are data-only. No business logic. No domain access.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QListWidget, QListWidgetItem, QPushButton,
        QWidget, QMessageBox,
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False


@dataclass
class ProfileRegion:
    """A named region with position in a workspace profile."""
    id: str
    visible: bool = True
    floating: bool = False
    x: int = 0
    y: int = 0
    width: int = 400
    height: int = 300
    tab_index: int = 0


@dataclass
class WorkspaceProfile:
    """A named workspace layout profile."""
    name: str
    description: str
    regions: Dict[str, ProfileRegion] = field(default_factory=dict)
    active_main: str = "dashboard"
    refresh_interval: int = 5  # seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "active_main": self.active_main,
            "refresh_interval": self.refresh_interval,
            "regions": {
                rid: {
                    "id": r.id, "visible": r.visible,
                    "floating": r.floating,
                    "x": r.x, "y": r.y,
                    "width": r.width, "height": r.height,
                    "tab_index": r.tab_index,
                }
                for rid, r in self.regions.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkspaceProfile:
        regions = {}
        for rid, rd in data.get("regions", {}).items():
            regions[rid] = ProfileRegion(
                id=rd.get("id", rid),
                visible=rd.get("visible", True),
                floating=rd.get("floating", False),
                x=rd.get("x", 0), y=rd.get("y", 0),
                width=rd.get("width", 400), height=rd.get("height", 300),
                tab_index=rd.get("tab_index", 0),
            )
        return cls(
            name=data.get("name", "unknown"),
            description=data.get("description", ""),
            regions=regions,
            active_main=data.get("active_main", "dashboard"),
            refresh_interval=data.get("refresh_interval", 5),
        )


# ── Built-in profiles ────────────────────────────────────────────────

_BUILTIN_PROFILES: Dict[str, WorkspaceProfile] = {}


def _ensure_builtins() -> None:
    if _BUILTIN_PROFILES:
        return

    _BUILTIN_PROFILES["monitoring"] = WorkspaceProfile(
        name="Monitoring",
        description="Missions + Timeline center, live activity",
        active_main="dashboard",
        refresh_interval=3,
        regions={
            "navigation": ProfileRegion("navigation", visible=True,
                                        width=200, height=600),
            "mission": ProfileRegion("mission", visible=True,
                                     width=500, height=300),
            "timeline": ProfileRegion("timeline", visible=True,
                                      width=500, height=300,
                                      tab_index=0),
            "notifications": ProfileRegion("notifications", visible=True,
                                           floating=True, x=700, y=0,
                                           width=300, height=200),
            "logs": ProfileRegion("logs", visible=False),
        },
    )

    _BUILTIN_PROFILES["operations"] = WorkspaceProfile(
        name="Operations",
        description="Mission control + approval + terminal",
        active_main="missions",
        refresh_interval=2,
        regions={
            "navigation": ProfileRegion("navigation", visible=True,
                                        width=180, height=600),
            "mission": ProfileRegion("mission", visible=True,
                                     width=450, height=350),
            "timeline": ProfileRegion("timeline", visible=True,
                                      width=450, height=250,
                                      tab_index=1),
            "notifications": ProfileRegion("notifications", visible=True,
                                           width=300, height=150),
            "logs": ProfileRegion("logs", visible=True,
                                  width=450, height=200),
        },
    )

    _BUILTIN_PROFILES["approval"] = WorkspaceProfile(
        name="Approval",
        description="Pending approvals + mission detail",
        active_main="approvals",
        refresh_interval=2,
        regions={
            "navigation": ProfileRegion("navigation", visible=False),
            "mission": ProfileRegion("mission", visible=True,
                                     width=400, height=600),
            "timeline": ProfileRegion("timeline", visible=True,
                                      width=400, height=300),
            "notifications": ProfileRegion("notifications", visible=True,
                                           width=300, height=150),
            "logs": ProfileRegion("logs", visible=False),
        },
    )

    _BUILTIN_PROFILES["investigation"] = WorkspaceProfile(
        name="Investigation",
        description="Deep timeline + logs + audit trail",
        active_main="timeline",
        refresh_interval=10,
        regions={
            "navigation": ProfileRegion("navigation", visible=True,
                                        width=160, height=600),
            "mission": ProfileRegion("mission", visible=True,
                                     width=350, height=300),
            "timeline": ProfileRegion("timeline", visible=True,
                                      width=600, height=400),
            "notifications": ProfileRegion("notifications", visible=True,
                                           floating=True, x=800, y=0,
                                           width=280, height=180),
            "logs": ProfileRegion("logs", visible=True,
                                  width=600, height=200),
        },
    )


# ── Profile Selector Dialog ─────────────────────────────────────────

class ProfileSelectorDialog(QDialog):
    """Dialog to select and switch workspace profiles."""

    def __init__(self, current_profile: str = "monitoring",
                 parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")
        super().__init__(parent)

        _ensure_builtins()

        self._selected: Optional[str] = current_profile
        self.setWindowTitle("Workspace Profiles")
        self.setMinimumWidth(400)
        self._build(current_profile)

    def _build(self, current: str) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("<b>Select Workspace Profile</b>")
        layout.addWidget(header)

        desc = QLabel("Switch between layout profiles. All docks will rearrange automatically.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Profile list
        self._list = QListWidget()
        for name, profile in _BUILTIN_PROFILES.items():
            item = QListWidgetItem(f"{profile.name} — {profile.description}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            if name == current:
                item.setSelected(True)
                self._list.setCurrentItem(item)
            self._list.addItem(item)

        self._list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list)

        # Detail
        self._detail = QLabel("")
        self._detail.setWordWrap(True)
        layout.addWidget(self._detail)
        self._update_detail(current)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        apply_btn = QPushButton("Apply Profile")
        apply_btn.clicked.connect(self._apply)
        btn_layout.addWidget(apply_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _on_selection_changed(self, current: Optional[QListWidgetItem],
                              previous: Optional[QListWidgetItem]) -> None:
        if current:
            name = current.data(Qt.ItemDataRole.UserRole)
            self._update_detail(name)

    def _update_detail(self, name: str) -> None:
        profile = _BUILTIN_PROFILES.get(name)
        if not profile:
            self._detail.setText("")
            return
        visible = [rid for rid, r in profile.regions.items() if r.visible]
        lines = [
            f"<b>{profile.name}</b>",
            f"{profile.description}",
            f"Refresh: every {profile.refresh_interval}s",
            f"Visible panels: {', '.join(visible)}",
        ]
        self._detail.setText("<br>".join(lines))

    def _apply(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        self._selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    @property
    def selected_profile(self) -> Optional[str]:
        return self._selected


# ── WorkspaceProfiles Manager ────────────────────────────────────────

class WorkspaceProfiles:
    """Manage workspace layout profiles.

    Provides built-in profiles and allows switching.
    Does not directly modify layout — returns profile data for
    the layout manager to apply.
    """

    def __init__(self):
        _ensure_builtins()
        self._profiles = dict(_BUILTIN_PROFILES)
        self._active = "monitoring"

    # ── Profile access ───────────────────────────────────────────────

    @property
    def active(self) -> str:
        return self._active

    @active.setter
    def active(self, name: str) -> None:
        if name in self._profiles:
            self._active = name

    @property
    def active_profile(self) -> WorkspaceProfile:
        return self._profiles.get(self._active, self._profiles["monitoring"])

    @property
    def profile_names(self) -> List[str]:
        return list(self._profiles.keys())

    @property
    def profiles(self) -> Dict[str, WorkspaceProfile]:
        return dict(self._profiles)

    def get_profile(self, name: str) -> Optional[WorkspaceProfile]:
        return self._profiles.get(name)

    # ── Switching ────────────────────────────────────────────────────

    def switch_to(self, name: str) -> WorkspaceProfile:
        """Switch to a profile. Returns the profile data."""
        if name not in self._profiles:
            name = "monitoring"
        self._active = name
        return self.active_profile

    def show_selector(self, parent: Optional[QWidget] = None) -> Optional[str]:
        """Show the profile selection dialog.

        Returns the selected profile name, or None if cancelled.
        """
        dialog = ProfileSelectorDialog(self._active, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._active = dialog.selected_profile
            return self._active
        return None

    # ── Previews ─────────────────────────────────────────────────────

    def describe(self, name: Optional[str] = None) -> str:
        """Describe a profile as text."""
        profile = self._profiles.get(name or self._active)
        if not profile:
            return "Unknown profile"
        visible = [rid for rid, r in profile.regions.items() if r.visible]
        return (
            f"{profile.name}: {profile.description} | "
            f"Visible: {', '.join(visible)} | "
            f"Refresh: {profile.refresh_interval}s"
        )

    @staticmethod
    def builtin_names() -> List[str]:
        _ensure_builtins()
        return list(_BUILTIN_PROFILES.keys())

    def summary(self) -> str:
        return (
            f"WorkspaceProfiles: {len(self._profiles)} profiles, "
            f"active={self._active}"
        )
