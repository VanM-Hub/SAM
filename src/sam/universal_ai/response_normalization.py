"""Response Normalization - WP-26 (MISSION-5.1 / IP-5.1-003).

Normalisasi response lintas Provider ke model universal. Consumer menerima
response melalui model seragam dengan provider/model attribution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .adapter_framework import NormalizedResponse


@dataclass(frozen=True)
class NormalizedConversationResponse:
    """Response conversation universal."""

    text: str
    provider_id: str
    model_id: str
    finish_status: str = "complete"
    usage: Dict[str, Any] = field(default_factory=dict)
    structured: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    @property
    def provider_attribution(self) -> str:
        return f"{self.provider_id}:{self.model_id}"

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "finish_status": self.finish_status,
            "usage": dict(self.usage),
            "structured": self.structured,
            "error": self.error,
            "provider_attribution": self.provider_attribution,
        }


class ResponseNormalizer:
    """Menormalisasi response adapter ke response conversation universal."""

    def normalize(self, response: NormalizedResponse) -> NormalizedConversationResponse:
        usage = {}
        if "usage" in response.metadata and isinstance(response.metadata["usage"], dict):
            usage = dict(response.metadata["usage"])
        return NormalizedConversationResponse(
            text=response.text,
            provider_id=response.provider_id,
            model_id=response.model_id,
            finish_status=response.finish_status,
            usage=usage,
            structured=response.structured,
            error=response.error,
        )
