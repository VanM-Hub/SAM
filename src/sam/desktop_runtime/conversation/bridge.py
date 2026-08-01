"""Sprint 272 - Desktop Runtime Foundation: conversation bridge (read-only).

Bridge ke lapisan percakapan TIDAK diubah; hanya membaca snapshot metadata
secara statis tanpa memanggil subsystem lain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class ConversationBridgeSnapshot:
    """Snapshot metadata percakapan yang dibaca bridge (read-only)."""

    conversation_id: str = "unknown"
    mode: str = "conversation"
    runtime_scope: Tuple[str, ...] = ("conversation",)

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "mode": self.mode,
            "runtime_scope": list(self.runtime_scope),
        }


@dataclass(frozen=True)
class ConversationBridge:
    """Bridge read-only untuk percakapan desktop (tanpa IO/thread)."""

    snapshot: ConversationBridgeSnapshot = field(
        default_factory=ConversationBridgeSnapshot
    )

    def read_only(self) -> bool:
        return True

    def scope(self) -> Tuple[str, ...]:
        return self.snapshot.runtime_scope

    def as_dict(self) -> dict:
        return {
            "read_only": True,
            "snapshot": self.snapshot.as_dict(),
        }
