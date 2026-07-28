"""LogViewer — Console log viewer for the SAM Console.

Support: follow mode, pause, search, filter, copy selection.
Uses Audit DTO from Sprint 11 for log data. No file I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class LogEntry:
    """A single log entry (immutable)."""
    line_number: int
    timestamp: str
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    source: str
    message: str
    details: str = ""


@dataclass
class LogViewer:
    """Console log viewer.

    Manages a scrolling view into log entries.
    Supports follow mode (auto-scroll to newest) and pause.
    No file I/O — consumes Audit DTO data.

    Usage:
        viewer = LogViewer()
        viewer.add_entries(audit_entries)
        viewer.follow()
        viewer.search("error")
    """

    _entries: List[LogEntry] = field(default_factory=list)
    scroll_position: int = 0
    page_size: int = 50
    _follow_mode: bool = True
    _paused: bool = False
    _search_query: str = ""
    _level_filter: str = "all"
    _source_filter: str = ""
    _on_new_entry: List[Callable[[LogEntry], None]] = field(default_factory=list)
    _selection: Optional[int] = None

    # ── Entry management ─────────────────────────────────────────────

    def add_entry(self, entry: LogEntry) -> None:
        """Add a single log entry."""
        self._entries.append(entry)
        if self._follow_mode and not self._paused:
            self.scroll_position = len(self._entries) - 1
        for cb in self._on_new_entry:
            try:
                cb(entry)
            except Exception:
                pass

    def add_entries(self, entries: Tuple[LogEntry, ...]) -> None:
        """Add multiple log entries at once."""
        for entry in entries:
            self._entries.append(entry)
            for cb in self._on_new_entry:
                try:
                    cb(entry)
                except Exception:
                    pass
        if self._follow_mode and not self._paused:
            self.scroll_position = len(self._entries) - 1

    def clear(self) -> None:
        """Clear all log entries."""
        self._entries.clear()
        self.scroll_position = 0
        self._selection = None

    # ── Follow / Pause ───────────────────────────────────────────────

    @property
    def is_following(self) -> bool:
        return self._follow_mode and not self._paused

    def follow(self) -> None:
        """Enable follow mode: auto-scroll to newest entries."""
        self._follow_mode = True
        self._paused = False
        self.scroll_position = len(self._entries) - 1

    def pause(self) -> None:
        """Pause auto-scroll without disabling follow mode."""
        self._paused = True

    def resume(self) -> None:
        """Resume auto-scroll."""
        self._paused = False
        if self._follow_mode:
            self.scroll_position = len(self._entries) - 1

    def toggle_follow(self) -> None:
        if self._follow_mode:
            self._follow_mode = False
        else:
            self.follow()

    def toggle_pause(self) -> None:
        if self._paused:
            self.resume()
        else:
            self.pause()

    # ── Scroll ───────────────────────────────────────────────────────

    def scroll_up(self, lines: int = 1) -> None:
        self.scroll_position = max(0, self.scroll_position - lines)
        if self.scroll_position < len(self._entries) - 1:
            self._paused = True

    def scroll_down(self, lines: int = 1) -> None:
        max_pos = max(0, len(self._entries) - 1)
        self.scroll_position = min(max_pos, self.scroll_position + lines)
        if self.scroll_position >= len(self._entries) - 1 and self._follow_mode:
            self._paused = False

    def scroll_to_top(self) -> None:
        self.scroll_position = 0
        self._paused = True

    def scroll_to_bottom(self) -> None:
        self.scroll_position = max(0, len(self._entries) - 1)
        if self._follow_mode:
            self._paused = False

    # ── Search ───────────────────────────────────────────────────────

    def search(self, query: str) -> int:
        """Search log entries. Returns count of matches."""
        self._search_query = query
        if not query:
            return len(self._entries)

        q = query.lower()
        count = 0
        for i, entry in enumerate(self._entries):
            if (q in entry.message.lower()
                    or q in entry.source.lower()
                    or q in entry.details.lower()):
                count += 1
                self._selection = i
        return count

    def next_match(self) -> Optional[int]:
        """Move to next search match. Returns index or None."""
        if not self._search_query:
            return None
        q = self._search_query.lower()
        start = (self._selection or 0) + 1
        for i in range(start, len(self._entries)):
            if (q in self._entries[i].message.lower()
                    or q in self._entries[i].source.lower()):
                self._selection = i
                self.scroll_position = i
                return i
        return None

    def prev_match(self) -> Optional[int]:
        """Move to previous search match. Returns index or None."""
        if not self._search_query:
            return None
        q = self._search_query.lower()
        start = (self._selection or len(self._entries)) - 1
        for i in range(start, -1, -1):
            if (q in self._entries[i].message.lower()
                    or q in self._entries[i].source.lower()):
                self._selection = i
                self.scroll_position = i
                return i
        return None

    def clear_search(self) -> None:
        self._search_query = ""
        self._selection = None

    # ── Filter ───────────────────────────────────────────────────────

    def filter_level(self, level: str) -> None:
        self._level_filter = level

    def filter_source(self, source: str) -> None:
        self._source_filter = source

    # ── Copy / Selection ─────────────────────────────────────────────

    def select(self, index: int) -> Optional[LogEntry]:
        """Select a log entry. Returns the entry or None."""
        if 0 <= index < len(self._entries):
            self._selection = index
            return self._entries[index]
        return None

    @property
    def selected_entry(self) -> Optional[LogEntry]:
        if self._selection is not None and 0 <= self._selection < len(self._entries):
            return self._entries[self._selection]
        return None

    def copy_selection(self) -> str:
        """Copy selected entry text."""
        entry = self.selected_entry
        if entry:
            return (
                f"[{entry.timestamp}] [{entry.level}] {entry.source}: "
                f"{entry.message}"
            )
        return ""

    # ── Display ──────────────────────────────────────────────────────

    @property
    def visible_entries(self) -> Tuple[LogEntry, ...]:
        """Get visible log entries based on scroll position and filters."""
        filtered = self._filtered
        start = max(0, self.scroll_position - self.page_size // 2)
        end = min(len(filtered), start + self.page_size)
        return tuple(filtered[start:end])

    @property
    def total_entries(self) -> int:
        return len(self._entries)

    @property
    def filtered_count(self) -> int:
        return len(self._filtered)

    @property
    def _filtered(self) -> List[LogEntry]:
        """Apply active filters."""
        result = self._entries

        if self._level_filter != "all":
            result = [
                e for e in result
                if e.level.upper() == self._level_filter.upper()
            ]

        if self._source_filter:
            sf = self._source_filter.lower()
            result = [
                e for e in result if sf in e.source.lower()
            ]

        if self._search_query:
            sq = self._search_query.lower()
            result = [
                e for e in result
                if sq in e.message.lower()
                or sq in e.source.lower()
            ]

        return result

    @property
    def summary_line(self) -> str:
        return (
            f"Log: {len(self._entries)} entries, "
            f"{self.filtered_count} visible, "
            f"{'FOLLOW' if self.is_following else 'PAUSED'}"
            f"{' | Search: ' + self._search_query if self._search_query else ''}"
        )

    # ── Event hook ───────────────────────────────────────────────────

    def on_new_entry(self, callback: Callable[[LogEntry], None]) -> None:
        """Register callback for new log entries."""
        self._on_new_entry.append(callback)


# ── Factory ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LogViewerFactory:
    """Creates LogViewer entries from Audit DTO data."""

    @staticmethod
    def from_audit_entries(audit_entries: list) -> Tuple[LogEntry, ...]:
        """Build LogEntry tuple from a list of audit log dicts."""
        entries: List[LogEntry] = []
        for i, ae in enumerate(audit_entries):
            if isinstance(ae, dict):
                entries.append(LogEntry(
                    line_number=i + 1,
                    timestamp=str(ae.get('timestamp', ae.get('created_at', ''))),
                    level=str(ae.get('level', ae.get('severity', 'INFO'))).upper(),
                    source=str(ae.get('source', ae.get('component', ''))),
                    message=str(ae.get('message', ae.get('description', ''))),
                    details=str(ae.get('details', '')),
                ))
            else:
                entry_str = str(ae)
                entries.append(LogEntry(
                    line_number=i + 1,
                    timestamp="",
                    level="INFO",
                    source="system",
                    message=entry_str,
                ))
        return tuple(entries)
