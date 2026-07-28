"""ConsoleConfig — Immutable configuration model for the SAM Console.

All config values are immutable after loading.
Supports serialization/deserialization for persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class ConsoleConfig:
    """Console configuration (fully immutable).

    Theme: dark | light | minimal
    Refresh rate: How often auto-refresh triggers (seconds).
    Default screen: Screen shown on startup.
    Unicode mode: Use Unicode box-drawing (True) or ASCII-safe (False).
    Colors: Enable ANSI colors.
    Page size: Max items per page in list views.
    History size: Max command history entries.
    Log level: Console log verbosity.
    Key bindings: Quick mapping for common keys.
    """

    theme: str = "dark"
    refresh_rate: float = 10.0
    default_screen: str = "dashboard"
    unicode_mode: bool = False
    colors: bool = True
    page_size: int = 20
    history_size: int = 100
    log_level: str = "INFO"
    key_bindings: Tuple[str, ...] = (
        "1-8: Navigate", "R: Refresh", "Q: Quit",
        "?: Help", "ESC: Back", "F5: Refresh",
    )

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values."""
        valid_themes = ("dark", "light", "minimal")
        if self.theme not in valid_themes:
            raise ValueError(
                f"Invalid theme '{self.theme}'. Must be one of: "
                f"{', '.join(valid_themes)}"
            )
        valid_screens = (
            "dashboard", "missions", "approvals", "timeline",
            "trust", "history", "settings", "help", "status",
        )
        if self.default_screen not in valid_screens:
            raise ValueError(
                f"Invalid default_screen '{self.default_screen}'. Must be one of: "
                f"{', '.join(valid_screens)}"
            )
        if self.refresh_rate < 0.5:
            raise ValueError(f"refresh_rate too low: {self.refresh_rate}. Min: 0.5s")
        if self.page_size < 1:
            raise ValueError(f"page_size must be >= 1, got: {self.page_size}")
        if self.history_size < 1:
            raise ValueError(f"history_size must be >= 1, got: {self.history_size}")

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to plain dict (JSON-safe)."""
        return {
            "theme": self.theme,
            "refresh_rate": self.refresh_rate,
            "default_screen": self.default_screen,
            "unicode_mode": self.unicode_mode,
            "colors": self.colors,
            "page_size": self.page_size,
            "history_size": self.history_size,
            "log_level": self.log_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConsoleConfig:
        """Deserialize from a plain dict.

        Unknown keys are silently ignored.
        Missing keys use defaults.
        """
        filtered = {k: v for k, v in data.items()
                    if k in CONSOLE_DEFAULTS}
        return cls(**filtered)

    @classmethod
    def merge(cls, base: ConsoleConfig,
              overrides: Dict[str, Any]) -> ConsoleConfig:
        """Create a new config by applying overrides to a base config."""
        current = base.to_dict()
        current.update(overrides)
        return cls(**current)


CONSOLE_DEFAULTS: Dict[str, Any] = {
    "theme": "dark",
    "refresh_rate": 10.0,
    "default_screen": "dashboard",
    "unicode_mode": False,
    "colors": True,
    "page_size": 20,
    "history_size": 100,
    "log_level": "INFO",
}
