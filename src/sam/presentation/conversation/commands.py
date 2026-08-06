"""ENG-G-001 · G1 — Conversation Structure: Command.

Presentation Capability (read-only). Command ini adalah service
composition-only (pola PresentationController, Sprint 276): menyusun
"perintah akses" tanpa memanggil subsystem. Pada G1 struktur command
belum mencolokkan RuntimeService — wiring ke jalur runtime_service.api
dilakukan di G2. Di sini TIDAK ada business logic dan TIDAK ada akses
langsung ke Runtime/Registry/Provider/Connector/ExecutionRuntime.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class ConversationCommandSpec:
    """Deskripsi command conversation (immutable, composition)."""

    name: str
    capability: str
    handler: Optional[Callable[..., Any]] = None

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "capability": self.capability,
            "has_handler": self.handler is not None,
        }


class ConversationCommand:
    """Kumpulan command presentation conversation (composition-only).

    G1: command terdaftar dengan referensi capability; handler (fungsi
    akses ke runtime_service) DIISI saat G2 via `attach`. Command sendiri
    tidak mengeksekusi apa pun pada akhir G1.
    """

    def __init__(self) -> None:
        self._specs: Dict[str, ConversationCommandSpec] = {name: self._spec(name) for name in self._capability_names()}
        self._handlers: Dict[str, Callable[..., Any]] = {}

    @staticmethod
    def _capability_names() -> tuple:
        return (
            "mission",
            "workflow",
            "policy",
            "audit",
            "artifact",
            "approval",
            "preview",
            "knowledge",
            "memory",
        )

    @staticmethod
    def _spec(name: str) -> ConversationCommandSpec:
        return ConversationCommandSpec(name=f"{name}_access", capability=name)

    def attach(self, capability: str, handler: Callable[..., Any]) -> None:
        """Pasang handler akses (via jalur runtime_service, G2+). Composition-only."""
        if capability in self._specs:
            self._specs[capability] = ConversationCommandSpec(
                name=f"{capability}_access", capability=capability, handler=handler
            )
            self._handlers[capability] = handler

    def spec(self, capability: str) -> Optional[ConversationCommandSpec]:
        return self._specs.get(capability)

    def has_handler(self, capability: str) -> bool:
        return capability in self._handlers

    def names(self) -> tuple:
        return tuple(self._specs.keys())

    def as_dict(self) -> dict:
        return {name: spec.as_dict() for name, spec in self._specs.items()}
