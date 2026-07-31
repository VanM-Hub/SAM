"""ServerShutdown (Sprint 268).

Program D - Runtime Services & Deployment.
Prosedur shutdown server. Sync, deterministic.
"""
from __future__ import annotations

from .server_runtime import ServerRuntime


class ServerShutdown:
    """Prosedur shutdown server."""

    def __init__(self, server: ServerRuntime) -> None:
        self._server = server
        self._done = False

    def run(self) -> None:
        self._server.set_started(False)
        self._done = True

    @property
    def done(self) -> bool:
        return self._done
