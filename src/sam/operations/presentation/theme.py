"""Theme — Semantic color system for presentation layer.

Uses semantic tokens, NOT terminal color codes.
Renderer determines final color — Theme only defines mapping.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


PRIMARY = "primary"
SECONDARY = "secondary"
SUCCESS = "success"
WARNING = "warning"
ERROR = "error"
INFO = "info"
MUTED = "muted"
BACKGROUND = "background"
FOREGROUND = "foreground"

ALL_TOKENS = frozenset({
    PRIMARY, SECONDARY, SUCCESS, WARNING, ERROR, INFO,
    MUTED, BACKGROUND, FOREGROUND,
})


@dataclass(frozen=True)
class Theme:
    """Immutable semantic theme mapping."""
    name: str = "dark"
    colors: dict = None  # type: ignore
    border: str = "\u2500"
    separator: str = "\u2022"
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.colors is None:
            object.__setattr__(self, "colors", {})

    def get(self, token: str, default: Optional[str] = None) -> str:
        if default is not None:
            return self.colors.get(token, default)
        return self.colors.get(token, token)

    def with_override(self, token: str, value: str) -> Theme:
        new_colors = dict(self.colors)
        new_colors[token] = value
        return Theme(name=self.name, colors=new_colors, border=self.border, enabled=self.enabled)


@dataclass(frozen=True)
class DarkTheme(Theme):
    name: str = "dark"

    def __post_init__(self) -> None:
        object.__setattr__(self, "colors", {
            PRIMARY: "cyan",
            SECONDARY: "blue",
            SUCCESS: "green",
            WARNING: "yellow",
            ERROR: "red",
            INFO: "white",
            MUTED: "gray",
            BACKGROUND: "black",
            FOREGROUND: "white",
        })


@dataclass(frozen=True)
class LightTheme(Theme):
    name: str = "light"

    def __post_init__(self) -> None:
        object.__setattr__(self, "colors", {
            PRIMARY: "blue",
            SECONDARY: "indigo",
            SUCCESS: "green",
            WARNING: "orange",
            ERROR: "red",
            INFO: "black",
            MUTED: "gray",
            BACKGROUND: "white",
            FOREGROUND: "black",
        })


@dataclass(frozen=True)
class CompactTheme(Theme):
    name: str = "compact"
    border: str = "\u00b7"

    def __post_init__(self) -> None:
        object.__setattr__(self, "colors", {
            PRIMARY: "blue",
            SECONDARY: "teal",
            SUCCESS: "green",
            WARNING: "amber",
            ERROR: "red",
            INFO: "white",
            MUTED: "gray",
            BACKGROUND: "black",
            FOREGROUND: "white",
        })
