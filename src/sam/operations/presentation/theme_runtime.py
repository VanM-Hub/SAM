"""ThemeRuntime — Runtime theme manager for Console.

Implements Dark, Light, and Minimal themes using semantic tokens from Sprint 12.
No hardcoded colors in renderers. All colors come from ThemeRuntime.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List

from .theme import Theme, DarkTheme, LightTheme, CompactTheme

THEME_NAMES = ["dark", "light", "minimal"]


@dataclass
class ThemeRuntime:
    """Runtime theme manager.

    Provides current theme, theme cycling, and theme lookup.
    All renderers query themes through this manager.
    """

    _themes: dict = field(default_factory=dict)
    _active: str = "dark"

    def __post_init__(self) -> None:
        self._themes = {
            "dark": DarkTheme(),
            "light": LightTheme(),
            "minimal": CompactTheme(),
        }

    @property
    def current(self) -> Theme:
        """Get the currently active Theme."""
        return self._themes.get(self._active, self._themes["dark"])

    @property
    def active_name(self) -> str:
        return self._active

    @property
    def theme_names(self) -> tuple:
        return tuple(self._themes.keys())

    def get(self, name: str) -> Optional[Theme]:
        """Get a theme by name."""
        return self._themes.get(name)

    def set_theme(self, name: str) -> bool:
        """Switch to a theme by name. Returns True if successful."""
        name = name.lower().strip()
        if name in self._themes:
            self._active = name
            return True
        return False

    def cycle(self) -> str:
        """Cycle to the next theme. Returns the new theme name."""
        names = list(self._themes.keys())
        current_idx = names.index(self._active) if self._active in names else 0
        next_idx = (current_idx + 1) % len(names)
        self._active = names[next_idx]
        return self._active

    def dark(self) -> None:
        """Switch to dark theme."""
        self._active = "dark"

    def light(self) -> None:
        """Switch to light theme."""
        self._active = "light"

    def minimal(self) -> None:
        """Switch to minimal/compact theme."""
        self._active = "minimal"

    # ── Semantic token lookup (convenience) ───────────────────────────

    def color(self, token: str, default: Optional[str] = None) -> str:
        """Get the color for a semantic token from the current theme."""
        return self.current.get(token, default or token)

    def primary(self) -> str:
        return self.current.get("primary", "cyan")

    def secondary(self) -> str:
        return self.current.get("secondary", "blue")

    def success(self) -> str:
        return self.current.get("success", "green")

    def warning(self) -> str:
        return self.current.get("warning", "yellow")

    def error(self) -> str:
        return self.current.get("error", "red")

    def info(self) -> str:
        return self.current.get("info", "white")

    def muted(self) -> str:
        return self.current.get("muted", "gray")

    def background(self) -> str:
        return self.current.get("background", "black")

    def foreground(self) -> str:
        return self.current.get("foreground", "white")

    # ── Render helpers ────────────────────────────────────────────────

    def for_severity(self, severity: str) -> str:
        """Get the appropriate token for a severity level."""
        mapping = {
            "critical": "error",
            "error": "error",
            "warning": "warning",
            "attention": "warning",
            "information": "info",
            "success": "success",
            "healthy": "success",
            "degraded": "warning",
            "unhealthy": "error",
        }
        return self.color(mapping.get(severity, "info"))

    def style_for(self, token: str) -> str:
        """Get the ANSI/style string for a semantic token (for RichAdapter)."""
        token_map = {
            "primary": "bold cyan",
            "secondary": "bold blue",
            "success": "bold green",
            "warning": "bold yellow",
            "error": "bold red",
            "info": "white",
            "muted": "grey62",
            "background": "black",
            "foreground": "white",
        }
        return token_map.get(token, "white")

    def summary(self) -> str:
        """Get a human-readable summary of current theme state."""
        t = self.current
        avail = ", ".join(self.theme_names)
        return (f"Theme: {t.name} | "
                f"Tokens: {len(t.colors) if t.colors else 0} semantic | "
                f"Available: {avail}")
