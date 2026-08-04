"""
OP-364 — Host Manager
======================

The Launcher only selects a host.
Host implementations remain in their existing modules.
No new hosts are created here.
"""

import enum
from typing import Dict, List, Optional


class HostType(enum.Enum):
    CONSOLE = "Console"
    DESKTOP = "Desktop"
    HEADLESS = "Headless"
    API_SERVER = "API Server"
    TESTING = "Testing"
    DIAGNOSTICS = "Diagnostics"


class Host:
    """Descriptor for a discoverable host.

    Immutable after creation.
    """

    __slots__ = ("host_type", "display_name", "description", "available")

    def __init__(
        self,
        host_type: HostType,
        display_name: str = "",
        description: str = "",
        available: bool = True,
    ) -> None:
        self.host_type = host_type
        self.display_name = display_name or host_type.value
        self.description = description
        self.available = available

    def __repr__(self) -> str:
        status = "available" if self.available else "unavailable"
        return f"<Host {self.display_name} ({status})>"


class HostManager:
    """Discovers, filters, and selects available hosts.

    Does NOT import or start any host.
    """

    def __init__(self) -> None:
        self._hosts: Dict[HostType, Host] = {}
        self._discover()

    def _discover(self) -> None:
        """Register all known host types."""
        for htype in HostType:
            if htype == HostType.DIAGNOSTICS:
                continue  # not a real runtime host
            self._hosts[htype] = Host(
                host_type=htype,
                display_name=htype.value,
                available=True,
            )

    @property
    def hosts(self) -> List[Host]:
        return list(self._hosts.values())

    @property
    def available_hosts(self) -> List[Host]:
        return [h for h in self._hosts.values() if h.available]

    def get(self, host_type: HostType) -> Optional[Host]:
        return self._hosts.get(host_type)

    def mark_unavailable(self, host_type: HostType) -> None:
        host = self._hosts.get(host_type)
        if host:
            self._hosts[host_type] = Host(
                host_type=host_type,
                display_name=host.display_name,
                description="",
                available=False,
            )

    def select(self, host_type: HostType) -> Optional[Host]:
        """Select a host for launch. Returns None if unavailable."""
        host = self._hosts.get(host_type)
        if host and host.available:
            return host
        return None

    def __repr__(self) -> str:
        available = sum(1 for h in self._hosts.values() if h.available)
        return f"<HostManager {available}/{len(self._hosts)} available>"
