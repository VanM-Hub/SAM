"""Conversation Translation — bridge read-only untuk terjemahan.

Sprint 118 — Connector Translation.
Akses translation engine (read-only, menghasilkan DTO netral baru).
"""
from __future__ import annotations

from .translation_engine import TranslationEngine
from .translation_request import TranslationRequest
from .translation_result import TranslationResult


class ConversationTranslationBridge:
    """Bridge conversation translation."""

    def __init__(self) -> None:
        self._engine = TranslationEngine()

    def translate(self, request: TranslationRequest) -> TranslationResult:
        return self._engine.translate(request)
