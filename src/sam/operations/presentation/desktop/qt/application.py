"""QtApplication — Bootstrap and lifecycle for the SAM Qt Desktop.

Wraps QApplication with startup/shutdown/exception handling.
No business logic. No domain imports.
"""

from __future__ import annotations

import sys
import signal
from typing import Optional, Callable

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QApplication = object  # stub


class QtApplication:
    """SAM Qt Desktop application bootstrap.

    Wraps QApplication lifecycle with exception hook, graceful exit,
    and signal handling. No business logic.
    """

    def __init__(self, app_name: str = "SAM Desktop", version: str = "4.10.0"):
        if not HAS_QT:
            raise ImportError(
                "PySide6 is required to run the SAM Qt Desktop. "
                "Install with: pip install PySide6"
            )

        self._app_name = app_name
        self._version = version
        self._qapp: Optional[QApplication] = None
        self._main_window = None
        self._running = False
        self._started = False

        # Exception hook
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._exception_hook

    # ── Lifecycle ─────────────────────────────────────────────────────

    def startup(self) -> None:
        """Create and configure QApplication."""
        if self._started:
            return
        self._qapp = QApplication(sys.argv)
        self._qapp.setApplicationName(self._app_name)
        self._qapp.setApplicationVersion(self._version)
        self._qapp.setOrganizationName("SAM")

        # Graceful exit on Ctrl+C
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self._started = True

    def run(self) -> int:
        """Enter Qt event loop. Returns exit code."""
        if not self._qapp:
            raise RuntimeError("QtApplication not started. Call startup() first.")
        self._running = True
        try:
            exit_code = self._qapp.exec_()
        finally:
            self._running = False
        return exit_code

    def shutdown(self) -> None:
        """Shutdown Qt application."""
        self._running = False
        if self._qapp:
            self._qapp.quit()
        # Restore exception hook
        sys.excepthook = self._original_excepthook
        self._started = False

    # ── Properties ────────────────────────────────────────────────────

    @property
    def qapp(self) -> Optional[QApplication]:
        return self._qapp

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def app_name(self) -> str:
        return self._app_name

    @property
    def version(self) -> str:
        return self._version

    # ── Exception hook ────────────────────────────────────────────────

    def _exception_hook(self, exc_type, exc_value, exc_tb) -> None:
        """Exception hook that logs and exits gracefully."""
        import traceback
        traceback.print_exception(exc_type, exc_value, exc_tb)
        self.shutdown()

    # ── Context manager ───────────────────────────────────────────────

    def __enter__(self):
        self.startup()
        return self

    def __exit__(self, *args):
        self.shutdown()
