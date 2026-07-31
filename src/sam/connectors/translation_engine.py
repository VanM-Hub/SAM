"""Translation Engine — engine terjemahan internal -> DTO netral.

Sprint 118 — Connector Translation.
Menerjemahkan payload SAM menjadi struktur netral (bukan format provider manapun).
Deterministik, sinkronus, preview-only.
"""
from __future__ import annotations
from typing import Any, Dict, List

from .translation_request import TranslationRequest
from .translation_result import TranslationResult


class TranslationEngine:
    """Terjemah payload internal ke bentuk netral.

    Mapping sederhana & deterministik: setiap key menjadi entri dalam list
    'fields' dengan tipe yang dideklarasi. Tidak ada transformasi provider.
    """

    SUPPORTED_KEYS: List[str] = [
        "id", "name", "type", "value", "status", "message", "metadata",
    ]

    def translate(self, request: TranslationRequest) -> TranslationResult:
        fields = []
        for key in self.SUPPORTED_KEYS:
            if key in request.payload:
                fields.append({
                    "key": key,
                    "value": request.payload[key],
                    "type": self._infer_type(request.payload[key]),
                })
        neutral = {
            "schema": "sam.neutral.v1",
            "connector_id": request.connector_id,
            "fields": fields,
        }
        return TranslationResult(request.request_id, request.connector_id, True,
                                 neutral, "neutral", "translated")

    @staticmethod
    def _infer_type(value: Any) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, (dict, list)):
            return "object" if isinstance(value, dict) else "array"
        return "unknown"
