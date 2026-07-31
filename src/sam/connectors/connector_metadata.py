"""Connector Metadata — frozen DTO untuk metadata connector.

Sprint 112 — Connector Foundation.
Metadata murni, provider-agnostic, tidak mengandung rahasia/credentials.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ConnectorMetadata:
    """Metadata deskriptif connector.

    SECURITY: tidak pernah menyimpan API key, token, secret, atau credential apa pun.
    Metadata hanya info deskriptif (nama, vendor, kategori, dokumentasi).
    """
    metadata_id: str
    connector_id: str
    vendor: str = ""
    category: str = "generic"
    homepage: str = ""
    docs_ref: str = ""
    license: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)
