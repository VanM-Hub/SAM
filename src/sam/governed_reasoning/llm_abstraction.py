"""Provider Abstraction - WP-06 (MISSION-4.4 / IP-4.4-001).

Abstraksi Provider agar LLM tetap provider-agnostic. Tidak ada dependensi
pada vendor tertentu; seluruh provider menggunakan interface yang sama;
response dinormalisasi; error dipetakan secara konsisten.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


class ProviderError:
    """Error provider yang dipetakan (konsisten lintas vendor)."""

    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    UNAUTHORIZED = "unauthorized"
    INVALID_REQUEST = "invalid_request"
    UPSTREAM = "upstream"


@dataclass(frozen=True)
class NormalizedResponse:
    """Response hasil normalisasi (konsisten)."""

    content: str
    model: str = ""
    usage: Dict[str, Any] = field(default_factory=dict)
    raw_status: str = ""

    def as_dict(self) -> dict:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "raw_status": self.raw_status,
        }


@dataclass(frozen=True)
class MappedError:
    """Error yang dipetakan ke kategori konsisten."""

    code: str
    message: str
    retryable: bool = False

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }


class ResponseNormalizer:
    """Menormalkan response dari berbagai bentuk provider."""

    @staticmethod
    def normalize(raw: Any, *, model: str = "") -> NormalizedResponse:
        if isinstance(raw, NormalizedResponse):
            return raw
        if isinstance(raw, dict):
            content = raw.get("content") or raw.get("text") or str(raw)
            usage = raw.get("usage") or {}
            return NormalizedResponse(
                content=str(content),
                model=model or str(raw.get("model", "")),
                usage=dict(usage) if isinstance(usage, dict) else {"raw": usage},
                raw_status=str(raw.get("status", "")),
            )
        if isinstance(raw, str):
            return NormalizedResponse(content=raw, model=model)
        # objek dengan .content
        content = getattr(raw, "content", None)
        if content is not None:
            return NormalizedResponse(
                content=str(content), model=model
            )
        return NormalizedResponse(content=str(raw), model=model)


class ErrorMapper:
    """Memetakan exception / status ke kategori konsisten."""

    @staticmethod
    def map(exc: Exception) -> MappedError:
        message = str(exc).lower()
        code = ProviderError.UPSTREAM
        retryable = False
        if "rate" in message or "429" in message:
            code, retryable = ProviderError.RATE_LIMIT, True
        elif "timeout" in message or "timed out" in message:
            code, retryable = ProviderError.TIMEOUT, True
        elif "unauthorized" in message or "401" in message or "403" in message:
            code = ProviderError.UNAUTHORIZED
        elif "invalid" in message or "400" in message:
            code = ProviderError.INVALID_REQUEST
        return MappedError(code=code, message=str(exc), retryable=retryable)

    @staticmethod
    def from_code(code: str) -> str:
        return code
