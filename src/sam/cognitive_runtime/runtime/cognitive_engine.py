"""Cognitive Engine — info engine kognitif (Sprint 191).

Engine murni menyusun representasi — BUKAN LLM/AI, tidak inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class CognitiveEngineInfo:
    """Info engine kognitif (immutable)."""
    name: str = "cognitive_engine"
    no_inference: bool = True
    is_llm: bool = False
    is_ai: bool = False
    deterministic: bool = True
    preview_only: bool = True


class CognitiveEngine:
    """Engine kognitif. Hanya menyusun DTO, tidak reasoning."""

    def info(self) -> CognitiveEngineInfo:
        return CognitiveEngineInfo()
