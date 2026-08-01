"""Sprint 272 - Desktop Runtime Foundation."""
from .capability import DesktopCapability
from .contract import DesktopContract
from .descriptor import DesktopDescriptor
from .metadata import DesktopMetadata
from .registry import DesktopRegistry, KNOWN_COMPONENTS

__all__ = [
    "DesktopCapability",
    "DesktopContract",
    "DesktopDescriptor",
    "DesktopMetadata",
    "DesktopRegistry",
    "KNOWN_COMPONENTS",
]
