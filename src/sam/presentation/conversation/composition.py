"""ENG-G-001 · G1 — Conversation Structure: UI Composition.

Presentation Capability (read-only). Komposisi UI menggabungkan
ViewModel + Command menjadi satu pandangan conversation yang siap
dibungkus oleh lapisan di atasnya. Hanya menyusun, TIDAK mengeksekusi
dan TIDAK memanggil subsystem. Konsisten dengan Composition Principle
(Art XVI) dan pola Sprint 276 (service composition-only + DTO immutable).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .viewmodel import ConversationViewModel
from .commands import ConversationCommand, ConversationCommandSpec


@dataclass(frozen=True)
class ConversationComposition:
    """Komposisi UI conversation (View + Command terdaftar). Read-only."""

    viewmodel: ConversationViewModel = field(default_factory=ConversationViewModel)
    command_names: List[str] = field(default_factory=list)
    command_specs: List[Dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "conversation": self.viewmodel.as_dict(),
            "commands": self.command_specs,
        }


def compose_conversation(
    viewmodel: ConversationViewModel, command: ConversationCommand
) -> ConversationComposition:
    """Susun komposisi UI conversation dari ViewModel + Command (composition-only)."""
    specs = [
        spec.as_dict()
        for spec in (command.spec(name) for name in command.names())
        if spec is not None
    ]
    return ConversationComposition(
        viewmodel=viewmodel, command_names=list(command.names()), command_specs=specs
    )
