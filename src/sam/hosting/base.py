"""
Hosting Adapter — Phase 0

Abstraksi platform untuk SAM Runtime.
Mengisolasi kernel dari platform-specific details.
"""

from abc import ABC, abstractmethod
from typing import Optional


class HostingAdapter(ABC):
    """Base class for all hosting adapters.

    Setiap platform (Desktop, Windows Service, systemd, Docker)
    mengimplementasikan adapter ini.
    """

    @abstractmethod
    def get_workspace(self) -> str:
        """Return path to workspace directory."""
        ...

    @abstractmethod
    def get_environment(self) -> dict:
        """Return platform-specific environment variables."""
        ...

    @abstractmethod
    def get_signal_handler(self):
        """Return platform-specific signal handler (if any)."""
        ...

    @abstractmethod
    def get_log_path(self) -> str:
        """Return path to log directory."""
        ...


class DesktopAdapter(HostingAdapter):
    """Adapter untuk desktop environment (Windows/Linux/macOS)."""

    def get_workspace(self) -> str:
        return "./workspace"

    def get_environment(self) -> dict:
        return {}

    def get_signal_handler(self):
        return None

    def get_log_path(self) -> str:
        return "./workspace/logs"


class DockerAdapter(HostingAdapter):
    """Adapter untuk Docker container."""

    def __init__(self, workspace: str = "/opt/sam/workspace"):
        self._workspace = workspace

    def get_workspace(self) -> str:
        return self._workspace

    def get_environment(self) -> dict:
        return {"CONTAINERIZED": "true"}

    def get_signal_handler(self):
        return None

    def get_log_path(self) -> str:
        return f"{self._workspace}/logs"
