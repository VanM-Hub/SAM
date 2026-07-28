"""Refresh — Refresh coordinator for presentation layer.

State model only. No threads. No timers.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class RefreshMode(Enum):
    MANUAL = "manual"
    EVENT = "event"
    FIVE_SECOND = "5s"
    TEN_SECOND = "10s"
    THIRTY_SECOND = "30s"


@dataclass(frozen=True)
class RefreshState:
    """Immutable snapshot of refresh state."""
    mode: RefreshMode = RefreshMode.TEN_SECOND
    is_paused: bool = False
    is_dirty: bool = False
    last_full_refresh: Optional[str] = None
    last_partial_refresh: Optional[str] = None
    dirty_sections: tuple[str, ...] = field(default_factory=tuple)
    mode_changed_at: str = ""

    @property
    def needs_any_refresh(self) -> bool:
        return self.is_dirty or self.last_full_refresh is None

    @property
    def interval_seconds(self) -> int:
        mapping = {
            RefreshMode.MANUAL: 0,
            RefreshMode.EVENT: 0,
            RefreshMode.FIVE_SECOND: 5,
            RefreshMode.TEN_SECOND: 10,
            RefreshMode.THIRTY_SECOND: 30,
        }
        return mapping.get(self.mode, 10)


class RefreshController:
    """Refresh controller — stateful but no threads/timers."""

    def __init__(self) -> None:
        self._state = RefreshState()

    @property
    def state(self) -> RefreshState:
        return self._state

    def pause(self) -> RefreshState:
        self._state = RefreshState(
            mode=self._state.mode,
            is_paused=True,
            is_dirty=self._state.is_dirty,
            last_full_refresh=self._state.last_full_refresh,
            last_partial_refresh=self._state.last_partial_refresh,
            dirty_sections=self._state.dirty_sections,
            mode_changed_at=datetime.now().isoformat(),
        )
        return self._state

    def resume(self) -> RefreshState:
        self._state = RefreshState(
            mode=self._state.mode,
            is_paused=False,
            is_dirty=self._state.is_dirty,
            last_full_refresh=self._state.last_full_refresh,
            last_partial_refresh=self._state.last_partial_refresh,
            dirty_sections=self._state.dirty_sections,
            mode_changed_at=datetime.now().isoformat(),
        )
        return self._state

    def set_mode(self, mode: RefreshMode) -> RefreshState:
        self._state = RefreshState(
            mode=mode,
            is_paused=self._state.is_paused,
            is_dirty=True,
            last_full_refresh=self._state.last_full_refresh,
            last_partial_refresh=self._state.last_partial_refresh,
            dirty_sections=self._state.dirty_sections,
            mode_changed_at=datetime.now().isoformat(),
        )
        return self._state

    def mark_dirty(self, *sections: str) -> RefreshState:
        current = set(self._state.dirty_sections)
        current.update(sections)
        self._state = RefreshState(
            mode=self._state.mode,
            is_paused=self._state.is_paused,
            is_dirty=True,
            last_full_refresh=self._state.last_full_refresh,
            last_partial_refresh=self._state.last_partial_refresh,
            dirty_sections=tuple(sorted(current)),
            mode_changed_at=self._state.mode_changed_at,
        )
        return self._state

    def needs_refresh(self) -> bool:
        return self._state.needs_any_refresh and not self._state.is_paused

    def full_refresh(self) -> RefreshState:
        self._state = RefreshState(
            mode=self._state.mode,
            is_paused=self._state.is_paused,
            is_dirty=False,
            last_full_refresh=datetime.now().isoformat(),
            last_partial_refresh=self._state.last_partial_refresh,
            dirty_sections=(),
            mode_changed_at=self._state.mode_changed_at,
        )
        return self._state

    def partial_refresh(self, *sections: str) -> RefreshState:
        current = set(self._state.dirty_sections)
        for s in sections:
            current.discard(s)
        self._state = RefreshState(
            mode=self._state.mode,
            is_paused=self._state.is_paused,
            is_dirty=bool(current),
            last_full_refresh=self._state.last_full_refresh,
            last_partial_refresh=datetime.now().isoformat(),
            dirty_sections=tuple(sorted(current)),
            mode_changed_at=self._state.mode_changed_at,
        )
        return self._state
