"""Audit Engine — engine audit (Sprint 215).

Bukan LLM, bukan AI, bukan inference. Engine read-only deterministik
yang menghasilkan representasi preview. Tidak evaluasi keputusan.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuditEngine:
    """Engine audit immutable — is_llm=False, is_ai=False."""
    is_llm: bool = False
    is_ai: bool = False
    inference: bool = False
    decision: bool = False

    def info(self) -> dict:
        return {
            "is_llm": self.is_llm,
            "is_ai": self.is_ai,
            "inference": self.inference,
            "decision": self.decision,
            "preview_only": True,
        }
