"""Desktop Runtime - Program F (v29.0.0).

Entry point UI resmi SAM: composition layer yang menghubungkan seluruh
subsystem. Hanya visualisasi, tanpa business logic baru, tanpa eksekusi
sendiri, preview-only & synchronous.
"""
from .bridge import DesktopRuntimeBridge
from .foundation import (
    DesktopCapability,
    DesktopContract,
    DesktopDescriptor,
    DesktopMetadata,
    DesktopRegistry,
    KNOWN_COMPONENTS,
)

__all__ = [
    "DesktopRuntimeBridge",
    "DesktopCapability",
    "DesktopContract",
    "DesktopDescriptor",
    "DesktopMetadata",
    "DesktopRegistry",
    "KNOWN_COMPONENTS",
]
