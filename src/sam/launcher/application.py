"""
OP-361 — Launcher Application
==============================

Core application lifecycle for the SAM Launcher.
Defines states, context, and the top-level orchestrator.
"""

import enum
import sys
import time
from typing import Any, Dict, List, Optional, Callable


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class LauncherState(enum.Enum):
    """Finite state machine for the launcher lifecycle."""
    INIT = "INIT"
    BOOTSTRAP = "BOOTSTRAP"
    VALIDATION = "VALIDATION"
    READY = "READY"
    START_HOST = "START_HOST"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class LauncherResult:
    """Result of a launcher operation. Immutable."""

    __slots__ = ("success", "message", "data")

    def __init__(self, success: bool, message: str = "", data: Any = None) -> None:
        self.success = success
        self.message = message
        self.data = data

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"<LauncherResult {status}: {self.message}>"

    @classmethod
    def ok(cls, message: str = "", data: Any = None) -> "LauncherResult":
        return cls(True, message, data)

    @classmethod
    def fail(cls, message: str = "", data: Any = None) -> "LauncherResult":
        return cls(False, message, data)


class LauncherContext:
    """Mutable context that travels through the launcher pipeline.

    Created fresh on every launch. Not persisted.
    """

    __slots__ = (
        "state",
        "started_at",
        "config",
        "env_report",
        "bootstrap_report",
        "diagnostics_snapshot",
        "host_type",
        "safe_mode",
        "exit_code",
        "metadata",
    )

    def __init__(self) -> None:
        self.state: LauncherState = LauncherState.INIT
        self.started_at: float = time.time()
        self.config: Any = None
        self.env_report: Any = None
        self.bootstrap_report: Any = None
        self.diagnostics_snapshot: Any = None
        self.host_type: Optional[str] = None
        self.safe_mode: Any = None
        self.exit_code: int = 0
        self.metadata: Dict[str, Any] = {}

    @property
    def elapsed(self) -> float:
        return time.time() - self.started_at

    def __repr__(self) -> str:
        return (
            f"<LauncherContext state={self.state.value} "
            f"elapsed={self.elapsed:.2f}s>"
        )


# ──────────────────────────────────────────────
# Application
# ──────────────────────────────────────────────

class LauncherApplication:
    """Top-level orchestrator for the SAM Launcher.

    Manages the lifecycle and delegates to subsystems.
    Does NOT import Guardian, Domain, Repository, or Storage.
    """

    def __init__(self) -> None:
        self._ctx: Optional[LauncherContext] = None
        self._hooks: Dict[LauncherState, List[Callable]] = {
            s: [] for s in LauncherState
        }

    # ── lifecycle ──────────────────────────────

    def run(self) -> int:
        """Execute the full launcher lifecycle.

        Returns exit code (0 = success).
        """
        ctx = LauncherContext()
        self._ctx = ctx

        try:
            self._transition(ctx, LauncherState.BOOTSTRAP)
            self._do_bootstrap(ctx)

            self._transition(ctx, LauncherState.VALIDATION)
            self._do_validation(ctx)

            self._transition(ctx, LauncherState.READY)
            self._do_ready(ctx)

            self._transition(ctx, LauncherState.START_HOST)
            self._do_start_host(ctx)

            self._transition(ctx, LauncherState.RUNNING)
            self._do_running(ctx)

        except KeyboardInterrupt:
            self._transition(ctx, LauncherState.STOPPING)
            ctx.exit_code = 130

        except Exception as exc:
            self._transition(ctx, LauncherState.ERROR)
            ctx.exit_code = 1
            ctx.metadata["error"] = str(exc)

        finally:
            self._transition(ctx, LauncherState.STOPPED)

        return ctx.exit_code

    def _transition(self, ctx: LauncherContext, new_state: LauncherState) -> None:
        ctx.state = new_state
        for hook in self._hooks.get(new_state, []):
            try:
                hook(ctx)
            except Exception:
                pass  # hooks must not break startup

    # ── phase stubs (overridden by integration) ──

    def _do_bootstrap(self, ctx: LauncherContext) -> None:
        pass

    def _do_validation(self, ctx: LauncherContext) -> None:
        pass

    def _do_ready(self, ctx: LauncherContext) -> None:
        pass

    def _do_start_host(self, ctx: LauncherContext) -> None:
        pass

    def _do_running(self, ctx: LauncherContext) -> None:
        pass

    # ── hooks ──────────────────────────────────

    def on(self, state: LauncherState, hook: Callable) -> None:
        """Register a lifecycle hook for a state."""
        self._hooks.setdefault(state, []).append(hook)

    @property
    def context(self) -> Optional[LauncherContext]:
        return self._ctx

    def __repr__(self) -> str:
        state = self._ctx.state if self._ctx else "NONE"
        return f"<LauncherApplication state={state}>"
