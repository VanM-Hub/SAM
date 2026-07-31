"""Translation Request — DTO permintaan terjemahan.

Sprint 118 — Connector Translation.
Terjemahan DTO internal SAM -> DTO netral. Belum format provider.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class TranslationRequest:
    """Permintaan terjemahan internal -> netral."""
    request_id: str
    connector_id: str
    source_schema: str = "sam"
    payload: Dict[str, Any] = field(default_factory=dict)
