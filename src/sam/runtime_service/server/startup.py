"""ServerStartup (Sprint 268).

Program D - Runtime Services & Deployment.
Prosedur startup server. Sync, deterministic.
"""
from __future__ import annotations

from .server_runtime import ServerRuntime


class ServerStartup:
    """Prosedur startup server."""

    def __init__(self, server: ServerRuntime) -> None:
        self._server = server
        self._done = False

    def run(self) -> ServerRuntime:
        if self._done:
            return self._server
        self._server.set_started(True)
        self._done = True
        return self._server

    @property
    def done(self) -> bool:
        return self._done
