"""
OP-372 — Runtime Registry

Registry seluruh runtime yang dikenal SAM.
Launcher mengambil registry — tidak mengelola lifecycle runtime itu sendiri.
Tidak boleh import domain/guardian/conversation secara langsung.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class RuntimeType(Enum):
    """Types of runtime known to the launcher."""

    GUARDIAN = "guardian"
    REASONING = "reasoning"
    DECISION = "decision"
    CONVERSATION = "conversation"
    CONSOLE = "console"
    DESKTOP = "desktop"
    HEADLESS = "headless"
    API_SERVER = "api_server"


@dataclass(frozen=True)
class RuntimeDescriptor:
    """Immutable description of a runtime registered with the launcher."""

    type: RuntimeType
    name: str
    path: str = ""
    version: str = "0.0.0"
    available: bool = True
    capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "name": self.name,
            "path": self.path,
            "version": self.version,
            "available": self.available,
            "capabilities": self.capabilities,
        }


class RuntimeRegistry:
    """Registry of known runtimes.

    Read-only from launcher perspective.
    Plugins and runtime modules register themselves externally.
    """

    def __init__(self) -> None:
        self._runtimes: Dict[RuntimeType, RuntimeDescriptor] = {}

    def register(self, descriptor: RuntimeDescriptor) -> None:
        """Register a runtime descriptor.

        If type already registered, existing descriptor remains
        (first-registration wins).
        """
        if descriptor.type not in self._runtimes:
            self._runtimes[descriptor.type] = descriptor

    def get(self, type_: RuntimeType) -> Optional[RuntimeDescriptor]:
        """Get descriptor for a runtime type."""
        return self._runtimes.get(type_)

    def list(self) -> List[RuntimeDescriptor]:
        """List all registered runtimes."""
        return list(self._runtimes.values())

    def available_types(self) -> List[RuntimeType]:
        """List runtime types that are marked available."""
        return [k for k, v in self._runtimes.items() if v.available]

    def is_registered(self, type_: RuntimeType) -> bool:
        """Check if a runtime type is registered."""
        return type_ in self._runtimes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtimes": {rt.value: desc.to_dict() for rt, desc in self._runtimes.items()},
        }
