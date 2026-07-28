"""RichAdapter — Thin wrapper around the Rich library.

All Rich API calls are isolated here. Renderers must NOT import Rich directly.
If Rich is unavailable, every method falls back to plain text output.

This ensures:
1. Rich is optional — console works without it
2. All Rich imports are in ONE place
3. Renderers stay clean and testable
4. Future UI libraries (Textual, etc.) can add their own adapter
"""

from __future__ import annotations
from typing import Optional, Any

# ── Lazy Rich import ──────────────────────────────────────────────

_HAS_RICH: bool = False
try:
    from rich.console import Console as RichConsole
    from rich.table import Table as RichTable
    from rich.panel import Panel as RichPanel
    from rich.text import Text as RichText
    from rich.columns import Columns as RichColumns
    from rich.layout import Layout as RichLayout
    from rich.progress import Progress as RichProgress, BarColumn, TextColumn, SpinnerColumn
    from rich.style import Style as RichStyle
    from rich.theme import Theme as RichTheme
    from rich.box import MINIMAL, ROUNDED, SIMPLE, HEAVY
    from rich.align import Align as RichAlign
    from rich.spinner import Spinner as RichSpinner
    from rich.live import Live as RichLive
    from rich.console import Group as RichGroup
    _HAS_RICH = True
except ImportError:  # pragma: no cover
    RichConsole = object  # type: ignore
    RichTable = object  # type: ignore
    RichPanel = object  # type: ignore
    RichText = object  # type: ignore
    RichColumns = object  # type: ignore
    RichLayout = object  # type: ignore
    RichProgress = object  # type: ignore
    BarColumn = None
    TextColumn = None
    SpinnerColumn = None
    RichStyle = object  # type: ignore
    RichTheme = object  # type: ignore
    MINIMAL = None
    ROUNDED = None
    SIMPLE = None
    HEAVY = None
    RichAlign = object  # type: ignore
    RichSpinner = object  # type: ignore
    RichLive = object  # type: ignore
    RichGroup = object  # type: ignore

_BOX_MAP = {
    "minimal": "MINIMAL",
    "rounded": "ROUNDED",
    "simple": "SIMPLE",
    "heavy": "HEAVY",
}

_STYLE_MAP: dict = {}
if _HAS_RICH:
    _STYLE_MAP = {
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


def has_rich() -> bool:
    """Check if Rich is available."""
    return _HAS_RICH


def create_console() -> Any:
    """Create a Rich Console using ASCII-safe fallback on legacy Windows.

    Uses SIMPLE box style to avoid Unicode box-drawing chars that
    fail on cp1252 (Windows legacy terminal).
    """
    if _HAS_RICH:
        try:
            return RichConsole(color_system="auto")
        except Exception:
            # Fallback to basic terminal
            return RichConsole(color_system=None, safe_box=True)
    return None


# ── Style helpers ──────────────────────────────────────────────────

def make_style(foreground: str = "", bold: bool = False, italic: bool = False,
               underline: bool = False) -> Any:
    """Create a Rich Style from semantic params."""
    if _HAS_RICH:
        parts = []
        if foreground:
            parts.append(foreground)
        if bold:
            parts.append("bold")
        if italic:
            parts.append("italic")
        if underline:
            parts.append("underline")
        return RichStyle(" ".join(parts))
    return None


def token_style(token: str) -> Any:
    """Get a Rich Style for a semantic token."""
    if _HAS_RICH:
        color = _STYLE_MAP.get(token, "white")
        return RichStyle(color)
    return None


def styled_text(text: str, token: str = "foreground") -> Any:
    """Wrap text in a Rich Text with semantic styling."""
    if _HAS_RICH:
        color = _STYLE_MAP.get(token, "white")
        return RichText(text, style=color)
    return text


# ── Table helpers ──────────────────────────────────────────────────

def create_table(title: str = "", box_style: str = "simple",
                 show_header: bool = True) -> Any:
    """Create a Rich Table using SIMPLE (ASCII-safe) box by default."""
    if _HAS_RICH:
        box = {"minimal": MINIMAL, "rounded": ROUNDED,
               "simple": SIMPLE, "heavy": HEAVY}.get(box_style, SIMPLE)
        return RichTable(title=title, box=box,
                         show_header=show_header, header_style="bold cyan")
    return None


def add_table_column(table: Any, name: str, style: str = "",
                     width: Optional[int] = None) -> None:
    """Add a column to a Rich table."""
    if _HAS_RICH and table is not None:
        kwargs = {"header": name, "style": style}
        if width is not None:
            kwargs["width"] = width
        table.add_column(**kwargs)


def add_table_row(table: Any, *cells: str, styles: Optional[list[str]] = None) -> None:
    """Add a row to a Rich table with per-cell styles."""
    if _HAS_RICH and table is not None:
        styled_cells = []
        for i, cell in enumerate(cells):
            style = (styles[i] if styles and i < len(styles) else "")
            if style:
                styled_cells.append(RichText(cell, style=RichStyle(style)))
            else:
                styled_cells.append(cell)
        table.add_row(*styled_cells)
    elif table is not None:
        table.add_row(*cells)


# ── Panel helpers ─────────────────────────────────────────────────

def make_panel(content: Any, title: str = "", border_token: str = "primary",
               subtitle: str = "") -> Any:
    """Wrap content in a Rich Panel (SIMPLE ASCII-safe box)."""
    if _HAS_RICH:
        border_style = _STYLE_MAP.get(border_token, "white")
        return RichPanel(
            content,
            title=title,
            subtitle=subtitle,
            border_style=border_style,
            box=SIMPLE,
        )
    return content


# ── Progress helpers ───────────────────────────────────────────────

def create_progress() -> Any:
    """Create a Rich Progress context."""
    if _HAS_RICH:
        return RichProgress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
    return None


def add_progress_task(progress: Any, description: str, total: int = 100) -> int:
    """Add a task to a progress bar. Returns task_id."""
    if _HAS_RICH and progress is not None:
        return progress.add_task(description, total=total)
    return 0


def update_progress(progress: Any, task_id: int, completed: int = 0,
                    advance: int = 0) -> None:
    """Update a progress task."""
    if _HAS_RICH and progress is not None:
        kwargs: dict = {"task_id": task_id}
        if advance:
            kwargs["advance"] = advance
        else:
            kwargs["completed"] = completed
        progress.update(**kwargs)


# ── Column / layout helpers ────────────────────────────────────────

def make_columns(*items: Any, equal: bool = True) -> Any:
    """Arrange items in columns."""
    if _HAS_RICH:
        return RichColumns(items, equal=equal)
    return items


def make_layout() -> Any:
    """Create a Rich Layout."""
    if _HAS_RICH:
        return RichLayout()
    return None


# ── Spinner helpers ────────────────────────────────────────────────

def spinner(name: str = "dots", text: str = "") -> Any:
    """Create a spinner for status indicators."""
    if _HAS_RICH:
        if text:
            return RichSpinner(name, text=text)
        return RichSpinner(name)
    return text or name


# ── Align helpers ──────────────────────────────────────────────────

def center(text: str) -> Any:
    """Center-align text."""
    if _HAS_RICH:
        return RichAlign.center(text)
    return text


# ── Group / Live helpers ───────────────────────────────────────────

def make_group(*renderables: Any) -> Any:
    """Group multiple renderables together."""
    if _HAS_RICH:
        return RichGroup(*renderables)
    return "\n".join(str(r) for r in renderables)


# ── Plain text helpers (fallback when Rich unavailable) ────────────

def boxed(text: str, width: int = 60) -> str:
    """Wrap text in a simple box using ASCII-safe characters."""
    horiz = "-" * (width - 2)
    top = "+" + horiz + "+"
    bottom = "+" + horiz + "+"
    lines = text.split("\n")
    padded = []
    for line in lines:
        stripped = line[:width - 4]
        padded.append("| " + stripped.ljust(width - 4) + " |")
    return "\n".join([top] + padded + [bottom])


def separator(char: str = "-", width: int = 60) -> str:
    """Draw a horizontal separator line."""
    return char * width


def plain_table(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> str:
    """Render a plain text table without Rich."""
    if not headers:
        return ""

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Header
    parts = []
    header_cells = []
    for i, h in enumerate(headers):
        header_cells.append(h.ljust(col_widths[i]))
    parts.append(" | ".join(header_cells))
    parts.append("-+-".join(["-" * w for w in col_widths]))

    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                cells.append(str(cell).ljust(col_widths[i]))
        parts.append(" | ".join(cells))

    return "\n".join(parts)
