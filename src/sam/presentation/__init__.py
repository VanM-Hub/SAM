"""Presentation Layer - Program F (v30.0.0).

Entry point UI resmi SAM: presentation layer yang menghubungkan seluruh
subsystem. Hanya visualisasi & komposisi, tanpa business logic, tanpa
eksekusi/engine/pipeline sendiri, preview-only & synchronous. Semua
operasi menuju RuntimeService.
"""
from .bridge import PresentationLayerBridge
from .foundation import (
    PresentationCapability,
    PresentationContract,
    PresentationDescriptor,
    PresentationMetadata,
    PresentationRegistry,
    KNOWN_COMPONENTS,
)
from .presentation_layer import PresentationLayer

__all__ = [
    "PresentationLayerBridge",
    "PresentationLayer",
    "PresentationCapability",
    "PresentationContract",
    "PresentationDescriptor",
    "PresentationMetadata",
    "PresentationRegistry",
    "KNOWN_COMPONENTS",
]
