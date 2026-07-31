"""Translation Result — DTO hasil terjemahan.

Sprint 118 — Connector Translation.
Hasil terjemahan ke DTO netral (provider-agnostic).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class TranslationResult:
    """Hasil terjemahan internal -> netral."""
    request_id: str
    connector_id: str
    success: bool = False
    neutral_payload: Dict[str, Any] = field(default_factory=dict)
    target_schema: str = "neutral"
    message: str = ""
