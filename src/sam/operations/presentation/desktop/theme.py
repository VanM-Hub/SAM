"""DesktopThemeAdapter — Bridges ThemeRuntime (Sprint 12/13) to Desktop.

DesktopThemeAdapter reads colors and token from ThemeRuntime.
It does NOT duplicate theme definitions. All colors originate from
the presentation theme system.

Provides color scheme, font tokens, and palette conversion for Qt.
No Qt implementation yet — only model/interface definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..theme_runtime import ThemeRuntime
from ..theme import Theme


@dataclass(frozen=True)
class ColorScheme:
    """Color scheme adapted for desktop widgets.

    All colors are hex strings (e.g., "#00FF00").
    No Qt types. No UI references.
    """
    primary: str = "#00FFFF"        # Cyan
    secondary: str = "#4488FF"      # Blue
    success: str = "#00FF00"        # Green
    warning: str = "#FFFF00"        # Yellow
    error: str = "#FF4444"          # Red
    info: str = "#CCCCCC"           # Light gray
    muted: str = "#888888"          # Gray
    background: str = "#1A1A2E"     # Dark background
    foreground: str = "#FFFFFF"     # White text
    surface: str = "#16213E"        # Surface/card background
    border: str = "#2A2A4E"         # Border color
    selection: str = "#0F3460"      # Selection highlight


@dataclass(frozen=True)
class FontToken:
    """Font definition for desktop widgets.

    No Qt font types. Pure data.
    """
    family: str = "Segoe UI"
    size: int = 10
    bold: bool = False
    italic: bool = False


@dataclass(frozen=True)
class FontScheme:
    """Font scheme adapted for desktop widgets."""
    heading: FontToken = field(default_factory=lambda: FontToken(
        family="Segoe UI", size=14, bold=True,
    ))
    body: FontToken = field(default_factory=lambda: FontToken(
        family="Segoe UI", size=10,
    ))
    mono: FontToken = field(default_factory=lambda: FontToken(
        family="Consolas", size=10,
    ))
    small: FontToken = field(default_factory=lambda: FontToken(
        family="Segoe UI", size=8,
    ))
    status_bar: FontToken = field(default_factory=lambda: FontToken(
        family="Segoe UI", size=9,
    ))


@dataclass(frozen=True)
class SpacingToken:
    """Spacing/padding definitions for desktop widgets."""
    xs: int = 2
    sm: int = 4
    md: int = 8
    lg: int = 16
    xl: int = 24


@dataclass(frozen=True)
class DesktopTheme:
    """Complete desktop theme — colors, fonts, spacing.

    Derived from ThemeRuntime. No duplicate theme definitions.
    """
    name: str = "dark"
    colors: ColorScheme = field(default_factory=ColorScheme)
    fonts: FontScheme = field(default_factory=FontScheme)
    spacing: SpacingToken = field(default_factory=SpacingToken)


class DesktopThemeAdapter:
    """Adapts ThemeRuntime to DesktopTheme.

    Reads colors from ThemeRuntime and converts to desktop-friendly
    hex colors. ThemeRuntime is the single source of truth.

    Usage:
        adapter = DesktopThemeAdapter()
        theme = adapter.adapt(theme_runtime)
    """

    _token_to_color: Dict[str, str] = {
        "primary": "#00FFFF",
        "secondary": "#4488FF",
        "success": "#00FF00",
        "warning": "#FFD700",
        "error": "#FF4444",
        "info": "#CCCCCC",
        "muted": "#888888",
        "background": "#1A1A2E",
        "foreground": "#FFFFFF",
    }

    _theme_palettes: Dict[str, Dict[str, str]] = {
        "dark": {
            "primary": "#00FFFF",
            "secondary": "#4488FF",
            "success": "#00FF88",
            "warning": "#FFD700",
            "error": "#FF4444",
            "info": "#CCCCCC",
            "muted": "#888888",
            "background": "#1A1A2E",
            "foreground": "#FFFFFF",
            "surface": "#16213E",
            "border": "#2A2A4E",
            "selection": "#0F3460",
        },
        "light": {
            "primary": "#0088CC",
            "secondary": "#3366AA",
            "success": "#22AA44",
            "warning": "#CC8800",
            "error": "#CC3333",
            "info": "#444444",
            "muted": "#888888",
            "background": "#F5F5F5",
            "foreground": "#222222",
            "surface": "#FFFFFF",
            "border": "#DDDDDD",
            "selection": "#CCE5FF",
        },
        "minimal": {
            "primary": "#00AAAA",
            "secondary": "#336699",
            "success": "#339933",
            "warning": "#AA8800",
            "error": "#AA3333",
            "info": "#555555",
            "muted": "#999999",
            "background": "#222222",
            "foreground": "#DDDDDD",
            "surface": "#2A2A2A",
            "border": "#444444",
            "selection": "#1A4A6A",
        },
    }

    @classmethod
    def adapt(cls, theme_runtime: ThemeRuntime) -> DesktopTheme:
        """Adapt a ThemeRuntime to DesktopTheme.

        Reads the current theme name and tokens from ThemeRuntime.
        ThemeRuntime is the single source of truth — DesktopThemeAdapter
        only converts format, not content.
        """
        theme_name = theme_runtime.active_name
        palette = cls._theme_palettes.get(theme_name, cls._theme_palettes["dark"])

        colors = ColorScheme(
            primary=palette.get("primary", "#00FFFF"),
            secondary=palette.get("secondary", "#4488FF"),
            success=palette.get("success", "#00FF00"),
            warning=palette.get("warning", "#FFD700"),
            error=palette.get("error", "#FF4444"),
            info=palette.get("info", "#CCCCCC"),
            muted=palette.get("muted", "#888888"),
            background=palette.get("background", "#1A1A2E"),
            foreground=palette.get("foreground", "#FFFFFF"),
            surface=palette.get("surface", "#16213E"),
            border=palette.get("border", "#2A2A4E"),
            selection=palette.get("selection", "#0F3460"),
        )

        return DesktopTheme(
            name=theme_name,
            colors=colors,
        )

    @classmethod
    def adapt_specific(cls, theme: Theme) -> DesktopTheme:
        """Adapt a specific Theme instance (regardless of active theme).

        Uses Theme.semantic_colors() or fallback.
        """
        theme_name = theme.name.lower() if hasattr(theme, 'name') else "custom"

        # Try to get semantic colors from Theme
        semantic = theme.get('semantic_colors', {}) if hasattr(theme, 'get') else {}
        if not semantic:
            # Use the known palette
            palette = cls._theme_palettes.get(theme_name, cls._theme_palettes["dark"])
        else:
            palette = semantic

        colors = ColorScheme(
            primary=str(semantic.get("primary", palette.get("primary", "#00FFFF"))),
            secondary=str(semantic.get("secondary", palette.get("secondary", "#4488FF"))),
            success=str(semantic.get("success", palette.get("success", "#00FF00"))),
            warning=str(semantic.get("warning", palette.get("warning", "#FFD700"))),
            error=str(semantic.get("error", palette.get("error", "#FF4444"))),
            info=str(semantic.get("info", palette.get("info", "#CCCCCC"))),
            muted=str(semantic.get("muted", palette.get("muted", "#888888"))),
            background=str(semantic.get("background", palette.get("background", "#1A1A2E"))),
            foreground=str(semantic.get("foreground", palette.get("foreground", "#FFFFFF"))),
            surface=str(semantic.get("surface", palette.get("surface", "#16213E"))),
            border=str(semantic.get("border", palette.get("border", "#2A2A4E"))),
            selection=str(semantic.get("selection", palette.get("selection", "#0F3460"))),
        )
        return DesktopTheme(name=theme_name, colors=colors)

    @classmethod
    def default_theme(cls) -> DesktopTheme:
        """Get the default (dark) desktop theme."""
        return DesktopTheme()

    @classmethod
    def theme_names(cls) -> Tuple[str, ...]:
        return tuple(cls._theme_palettes.keys())

    @classmethod
    def summary(cls, theme_runtime: ThemeRuntime) -> str:
        """Get summary of adapted theme."""
        dt = cls.adapt(theme_runtime)
        return (
            f"DesktopTheme: {dt.name} | "
            f"Primary: {dt.colors.primary} | "
            f"Background: {dt.colors.background}"
        )
