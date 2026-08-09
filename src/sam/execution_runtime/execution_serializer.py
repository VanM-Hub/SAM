"""Execution Request/Response Serializer - IP-4.1-001 WP-06/07.

Provider Execution Foundation.
Menyediakan serializer deterministik untuk ExecutionRequest & ExecutionResponse.

Scope (Foundation immutable, Article VI - Immutable Contracts):
- Request memiliki serializer (round-trip deterministik).
- Response konsisten (immutable).
- Request dapat dijelaskan & diaudit.
- Tidak ada mutasi contract yang telah diterbitkan.

Tidak ada network. Murni serialization/deserialization.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from .execution_request import ExecutionRequest
from .execution_response import ExecutionResponse


class ExecutionSerializationError(Exception):
    """Kesalahan serialisasi/deserialisasi."""


# ---------------------------------------------------------------------------
# Valid mode set (mirror request)
# ---------------------------------------------------------------------------

VALID_MODES = ("preview", "simulation", "execute", "rollback")
VALID_STATUS = ("pending", "executing", "completed", "failed", "cancelled", "timeout")


# ---------------------------------------------------------------------------
# Request serializer
# ---------------------------------------------------------------------------


def _validate_mode(mode: str) -> None:
    if mode not in VALID_MODES:
        raise ExecutionSerializationError(
            "mode invalid: '{}' (harus {})".format(mode, "|".join(VALID_MODES)))


def _validate_status(status: str) -> None:
    if status and status not in VALID_STATUS:
        raise ExecutionSerializationError(
            "status invalid: '{}'".format(status))


class ExecutionRequestSerializer:
    """Serializer ExecutionRequest (json-safe, round-trip deterministik)."""

    @staticmethod
    def to_dict(request: ExecutionRequest) -> Dict[str, Any]:
        return request.as_dict()

    @staticmethod
    def to_json(request: ExecutionRequest, pretty: bool = False) -> str:
        d = request.as_dict()
        if pretty:
            return json.dumps(d, indent=2, sort_keys=True)
        return json.dumps(d, sort_keys=True)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ExecutionRequest:
        execution_id = data.get("execution_id")
        provider_id = data.get("provider_id")
        if not execution_id or not provider_id:
            raise ExecutionSerializationError("execution_id & provider_id wajib")
        mode = data.get("mode", "preview")
        _validate_mode(mode)
        return ExecutionRequest(
            execution_id=execution_id,
            provider_id=provider_id,
            operation=data.get("operation", ""),
            payload=dict(data.get("payload") or {}),
            mode=mode,
            timeout_seconds=int(data.get("timeout_seconds", 60)),
            max_retries=int(data.get("max_retries", 2)),
            cancellation_token=data.get("cancellation_token"),
            approved=bool(data.get("approved", False)),
            approver=data.get("approver", "") or "",
            deterministic=bool(data.get("deterministic", True)),
            synchronous=bool(data.get("synchronous", True)),
        )

    @staticmethod
    def from_json(text: str) -> ExecutionRequest:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ExecutionSerializationError("JSON tidak valid: {}".format(exc))
        if not isinstance(data, dict):
            raise ExecutionSerializationError("root JSON harus objek")
        return ExecutionRequestSerializer.from_dict(data)


# ---------------------------------------------------------------------------
# Response serializer
# ---------------------------------------------------------------------------


class ExecutionResponseSerializer:
    """Serializer ExecutionResponse (immutable, json-safe)."""

    @staticmethod
    def to_dict(response: ExecutionResponse) -> Dict[str, Any]:
        return response.as_dict()

    @staticmethod
    def to_json(response: ExecutionResponse) -> str:
        return json.dumps(response.as_dict(), sort_keys=True)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ExecutionResponse:
        execution_id = data.get("execution_id")
        provider_id = data.get("provider_id")
        operation = data.get("operation", "")
        status = data.get("status", "pending")
        _validate_status(status)
        return ExecutionResponse(
            execution_id=execution_id or "",
            provider_id=provider_id or "",
            operation=operation,
            status=status,
            payload=dict(data.get("payload") or {}),
            message=data.get("message", "") or "",
            mode=data.get("mode", "preview"),
            external_calls=int(data.get("external_calls", 0)),
            retries_used=int(data.get("retries_used", 0)),
            duration_ms=int(data.get("duration_ms", 0)),
            error=data.get("error"),
        )
