"""DockPersistence — Save/restore dock layout, geometry, splitter, theme.

Uses Qt QSettings. No SAM repository access.
Data-only. No business logic. No domain imports.
"""

from __future__ import annotations

import json
from typing import Dict, Optional, Any, List

try:
    from PySide6.QtCore import QSettings, QByteArray, Qt
    from PySide6.QtWidgets import QMainWindow, QApplication
    HAS_QT = True
except ImportError:
    HAS_QT = False


# ── Constants ────────────────────────────────────────────────────────

ORGANIZATION = "SAM-Project"
APPLICATION = "SAM-Desktop"

SETTINGS_KEYS = {
    "geometry": "desktop/geometry",
    "dock_state": "desktop/dock_state",
    "splitter_sizes": "desktop/splitter_sizes",
    "active_profile": "desktop/active_profile",
    "theme": "desktop/theme",
    "refresh_interval": "desktop/refresh_interval",
    "selected_page": "desktop/selected_page",
    "navigation_width": "desktop/navigation_width",
    "window_maximized": "desktop/window_maximized",
    "profiles": "desktop/saved_profiles",
}


# ── DockPersistence ──────────────────────────────────────────────────

class DockPersistence:
    """Save and restore desktop layout using QSettings.

    Stores:
    - Window geometry & maximized state
    - Dock widget layout (QMainWindow.saveState/restoreState)
    - Splitter sizes
    - Active workspace profile
    - Theme
    - Refresh interval
    - Selected page
    - Navigation panel width
    - Custom profile definitions (optional)
    """

    def __init__(self):
        if not HAS_QT:
            return
        self._settings = QSettings(ORGANIZATION, APPLICATION)

    # ── Save ─────────────────────────────────────────────────────────

    def save_geometry(self, main_window: QMainWindow) -> None:
        """Save window geometry and maximized state."""
        self._settings.setValue(
            SETTINGS_KEYS["geometry"],
            main_window.saveGeometry(),
        )
        self._settings.setValue(
            SETTINGS_KEYS["window_maximized"],
            main_window.isMaximized(),
        )

    def save_dock_state(self, main_window: QMainWindow) -> None:
        """Save dock widget layout state."""
        state = main_window.saveState()
        self._settings.setValue(SETTINGS_KEYS["dock_state"], state)

    def save_splitter_sizes(self, sizes: List[int]) -> None:
        """Save splitter sizes as JSON list."""
        self._settings.setValue(
            SETTINGS_KEYS["splitter_sizes"],
            json.dumps(sizes),
        )

    def save_active_profile(self, profile_name: str) -> None:
        self._settings.setValue(
            SETTINGS_KEYS["active_profile"], profile_name)

    def save_theme(self, theme_name: str) -> None:
        self._settings.setValue(SETTINGS_KEYS["theme"], theme_name)

    def save_refresh_interval(self, seconds: int) -> None:
        self._settings.setValue(
            SETTINGS_KEYS["refresh_interval"], seconds)

    def save_selected_page(self, page: str) -> None:
        self._settings.setValue(SETTINGS_KEYS["selected_page"], page)

    def save_navigation_width(self, width: int) -> None:
        self._settings.setValue(
            SETTINGS_KEYS["navigation_width"], width)

    def save_all(self, main_window: QMainWindow,
                 profile: str = "monitoring",
                 theme: str = "default",
                 refresh_interval: int = 5,
                 selected_page: str = "dashboard",
                 navigation_width: int = 200,
                 splitter_sizes: Optional[List[int]] = None) -> None:
        """Save all layout settings at once."""
        self.save_geometry(main_window)
        self.save_dock_state(main_window)
        self.save_active_profile(profile)
        self.save_theme(theme)
        self.save_refresh_interval(refresh_interval)
        self.save_selected_page(selected_page)
        self.save_navigation_width(navigation_width)
        if splitter_sizes:
            self.save_splitter_sizes(splitter_sizes)

    # ── Restore ──────────────────────────────────────────────────────

    def restore_geometry(self, main_window: QMainWindow) -> bool:
        """Restore window geometry. Returns True if restored."""
        geo = self._settings.value(SETTINGS_KEYS["geometry"])
        if geo is not None and isinstance(geo, QByteArray):
            restored = main_window.restoreGeometry(geo)
            # Re-apply maximized if saved
            maximized = self._settings.value(
                SETTINGS_KEYS["window_maximized"], False, type=bool)
            if maximized:
                main_window.showMaximized()
            return restored
        return False

    def restore_dock_state(self, main_window: QMainWindow) -> bool:
        """Restore dock layout. Returns True if restored."""
        state = self._settings.value(SETTINGS_KEYS["dock_state"])
        if state is not None and isinstance(state, QByteArray):
            return main_window.restoreState(state)
        return False

    def restore_splitter_sizes(self) -> List[int]:
        """Restore splitter sizes. Returns empty list if not saved."""
        raw = self._settings.value(SETTINGS_KEYS["splitter_sizes"])
        if raw:
            try:
                return json.loads(str(raw))
            except (json.JSONDecodeError, TypeError):
                pass
        return []

    def restore_active_profile(self, default: str = "monitoring") -> str:
        return self._settings.value(
            SETTINGS_KEYS["active_profile"], default, type=str)

    def restore_theme(self, default: str = "default") -> str:
        return self._settings.value(
            SETTINGS_KEYS["theme"], default, type=str)

    def restore_refresh_interval(self, default: int = 5) -> int:
        return self._settings.value(
            SETTINGS_KEYS["refresh_interval"], default, type=int)

    def restore_selected_page(self, default: str = "dashboard") -> str:
        return self._settings.value(
            SETTINGS_KEYS["selected_page"], default, type=str)

    def restore_navigation_width(self, default: int = 200) -> int:
        return self._settings.value(
            SETTINGS_KEYS["navigation_width"], default, type=int)

    def restore_all(self, main_window: QMainWindow,
                    default_profile: str = "monitoring",
                    default_theme: str = "default") -> dict:
        """Restore all saved layout settings.

        Returns a dict of restored values for caller to apply.
        """
        geo_ok = self.restore_geometry(main_window)
        dock_ok = self.restore_dock_state(main_window)
        return {
            "geometry_restored": geo_ok,
            "dock_restored": dock_ok,
            "profile": self.restore_active_profile(default_profile),
            "theme": self.restore_theme(default_theme),
            "refresh_interval": self.restore_refresh_interval(),
            "selected_page": self.restore_selected_page(),
            "navigation_width": self.restore_navigation_width(),
            "splitter_sizes": self.restore_splitter_sizes(),
        }

    # ── Custom profiles ──────────────────────────────────────────────

    def save_custom_profiles(self, profiles: Dict) -> None:
        """Save custom workspace profile definitions as JSON."""
        self._settings.setValue(
            SETTINGS_KEYS["profiles"],
            json.dumps(profiles),
        )

    def restore_custom_profiles(self) -> Dict:
        """Restore custom profile definitions."""
        raw = self._settings.value(SETTINGS_KEYS["profiles"])
        if raw:
            try:
                return json.loads(str(raw))
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

    # ── Clear ────────────────────────────────────────────────────────

    def clear_all(self) -> None:
        """Clear all saved layout settings."""
        self._settings.clear()

    def clear_key(self, key: str) -> None:
        """Clear a specific settings key."""
        settings_key = SETTINGS_KEYS.get(key)
        if settings_key:
            self._settings.remove(settings_key)

    # ── Info ─────────────────────────────────────────────────────────

    def list_saved_keys(self) -> List[str]:
        """List which keys have saved values."""
        result = []
        for name, key in SETTINGS_KEYS.items():
            if self._settings.contains(key):
                result.append(name)
        return result

    def summary(self) -> str:
        saved = self.list_saved_keys()
        return (
            f"DockPersistence: {len(saved)} keys saved "
            f"({', '.join(saved)})"
        )
