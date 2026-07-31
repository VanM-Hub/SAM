"""Provider Capability — frozen DTO untuk kapabilitas provider.

Sprint 144 — Provider Foundation (OP-1402).
Kapabilitas dideklarasikan secara murni (preview-only); tidak ada eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ProviderOperation:
    """Operasi yang didukung provider (generik, bukan API spesifik domain)."""
    name: str
    description: str = ""
    preview_only: bool = True  # selalu preview di Phase XIV


@dataclass(frozen=True)
class ProviderCapability:
    """Kapabilitas yang didukung oleh sebuah provider."""
    capability_id: str
    provider_id: str
    name: str
    category: str = "generic"
    description: str = ""
    operations: List[ProviderOperation] = field(default_factory=list)

    def supports(self, operation: str) -> bool:
        """Cek apakah provider mendukung operasi tertentu (deterministik)."""
        return any(op.name == operation for op in self.operations)
