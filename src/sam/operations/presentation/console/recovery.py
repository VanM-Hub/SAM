"""ErrorRecovery — Runtime error recovery for the Console.

If renderer fails: retry, fallback to plain mode, safe mode, restart renderer.
Prevents crashes from taking down the entire application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime


class RecoveryStrategy(Enum):
    """Available recovery strategies (ordered by escalation)."""
    RETRY = "retry"
    FALLBACK = "fallback"
    PLAIN_MODE = "plain_mode"
    SAFE_MODE = "safe_mode"
    RESTART = "restart"


_STRATEGY_ORDER = (
    RecoveryStrategy.RETRY,
    RecoveryStrategy.FALLBACK,
    RecoveryStrategy.PLAIN_MODE,
    RecoveryStrategy.SAFE_MODE,
    RecoveryStrategy.RESTART,
)


@dataclass(frozen=True)
class RecoveryEvent:
    """A single recovery event (immutable)."""
    source: str
    error: str
    strategy: RecoveryStrategy
    success: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ErrorRecovery:
    """Error recovery handler for Console runtime.

    Supports automatic retry, fallback, and escalation.
    Tracks recovery history for telemetry.

    Usage:
        recovery = ErrorRecovery()
        result = recovery.recover(
            source="renderer",
            error="RichConsole failed: UnicodeEncodeError",
            retry_fn=render,
            fallback_fn=render_plain,
        )
        if result:
            print("Recovered with:", recovery.active_strategy)
    """

    def __init__(self, max_retries: int = 3) -> None:
        self._max_retries = max_retries
        self._strategy: RecoveryStrategy = RecoveryStrategy.RETRY
        self._retry_count: int = 0
        self._history: List[RecoveryEvent] = []
        self._in_safe_mode: bool = False
        self._plain_mode_active: bool = False
        self._fallback_active: bool = False

    # ── Recovery execution ────────────────────────────────────────────

    def recover(
        self,
        source: str,
        error: str,
        retry_fn: Optional[Callable[[], Any]] = None,
        fallback_fn: Optional[Callable[[], Any]] = None,
        restart_fn: Optional[Callable[[], Any]] = None,
    ) -> bool:
        """Attempt recovery using escalating strategies.

        Args:
            source: Source of the error (e.g., "renderer", "notification").
            error: Error message.
            retry_fn: Function to retry the failed operation.
            fallback_fn: Function that uses simpler rendering.
            restart_fn: Function that restarts the component.

        Returns True if recovery succeeded.
        """
        # Determine starting strategy based on current state
        if self._in_safe_mode:
            start_idx = _STRATEGY_ORDER.index(RecoveryStrategy.RESTART)
        elif self._plain_mode_active and self._fallback_active:
            start_idx = _STRATEGY_ORDER.index(RecoveryStrategy.SAFE_MODE)
        elif self._plain_mode_active:
            start_idx = _STRATEGY_ORDER.index(RecoveryStrategy.SAFE_MODE)
        elif self._fallback_active:
            start_idx = _STRATEGY_ORDER.index(RecoveryStrategy.RETRY)
        else:
            start_idx = _STRATEGY_ORDER.index(
                RecoveryStrategy.RETRY if self._retry_count < self._max_retries
                else RecoveryStrategy.FALLBACK
            )

        for strategy in _STRATEGY_ORDER[start_idx:]:
            self._strategy = strategy
            try:
                success = self._apply_strategy(
                    strategy, source, error,
                    retry_fn, fallback_fn, restart_fn,
                )
                if success:
                    return True
            except Exception:
                continue

        # All strategies failed — record final failure
        self._record_event(source, error, RecoveryStrategy.SAFE_MODE, False)
        return False

    def _apply_strategy(
        self,
        strategy: RecoveryStrategy,
        source: str,
        error: str,
        retry_fn: Optional[Callable],
        fallback_fn: Optional[Callable],
        restart_fn: Optional[Callable],
    ) -> bool:
        """Apply a specific recovery strategy."""
        if strategy == RecoveryStrategy.RETRY:
            if retry_fn:
                retry_fn()
                self._retry_count += 1
                self._record_event(source, error, strategy, True)
                return True
            return False

        elif strategy == RecoveryStrategy.FALLBACK:
            if fallback_fn:
                fallback_fn()
                self._fallback_active = True
                self._retry_count = 0
                self._record_event(source, error, strategy, True)
                return True
            return False

        elif strategy == RecoveryStrategy.PLAIN_MODE:
            # Plain mode: strip all formatting, use basic text
            self._plain_mode_active = True
            self._retry_count = 0
            self._record_event(source, error, strategy, True)
            return True

        elif strategy == RecoveryStrategy.SAFE_MODE:
            # Safe mode: minimal operation, no Rich, no colors
            self._in_safe_mode = True
            self._plain_mode_active = True
            self._fallback_active = True
            self._retry_count = 0
            self._record_event(source, error, strategy, True)
            return True

        elif strategy == RecoveryStrategy.RESTART:
            if restart_fn:
                restart_fn()
                self._in_safe_mode = False
                self._plain_mode_active = False
                self._fallback_active = False
                self._retry_count = 0
                self._record_event(source, error, strategy, True)
                return True
            return False

        return False

    # ── State queries ─────────────────────────────────────────────────

    @property
    def active_strategy(self) -> RecoveryStrategy:
        return self._strategy

    @property
    def in_safe_mode(self) -> bool:
        return self._in_safe_mode

    @property
    def in_plain_mode(self) -> bool:
        return self._plain_mode_active

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @property
    def latest_event(self) -> Optional[RecoveryEvent]:
        """Get the most recent recovery event."""
        if self._history:
            return self._history[-1]
        return None

    @property
    def history(self) -> Tuple[RecoveryEvent, ...]:
        return tuple(self._history)

    @property
    def recovery_count(self) -> int:
        return len(self._history)

    # ── Reset ─────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset recovery state (clear modes, retries, history)."""
        self._strategy = RecoveryStrategy.RETRY
        self._retry_count = 0
        self._in_safe_mode = False
        self._plain_mode_active = False
        self._fallback_active = False

    def reset_retry_count(self) -> None:
        """Reset just the retry count (after a successful operation)."""
        self._retry_count = 0

    # ── Internal ──────────────────────────────────────────────────────

    def _record_event(self, source: str, error: str,
                       strategy: RecoveryStrategy,
                       success: bool) -> None:
        self._history.append(RecoveryEvent(
            source=source,
            error=error,
            strategy=strategy,
            success=success,
        ))
