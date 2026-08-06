"""ENG-G-001 · G1 — Conversation Structure: ViewModel.

Presentation Capability (read-only). ViewModel hanya menyusun state
tampilan conversation; TIDAK memuat business logic, TIDAK memanggil
Runtime/Registry/Provider/Connector. Fasih dengan pola DTO immutable
(Sprint 276) dan Composition Principle (Art XVI): presentasi hanya
menggabungkan hasil, tidak mengeksekusi.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ConversationViewModel:
    """State tampilan conversation (komposisi, read-only).

    G1: struktur awal — capability belum dicolok (diisi G3-G9).
    Field capability mencerminkan 9 capability roadmap Program G
    (Mission/Workflow/Policy/Audit/Artifact/Approval/Preview/Knowledge/
    Memory) sebagai placeholder status 'not_attached' agar struktur
    siap menerima hasil dari jalur runtime_service (G2+).
    """

    conversation_id: str = "conversation"
    mode: str = "capability"
    read_only: bool = True
    capabilities: Dict[str, str] = field(
        default_factory=lambda: {
            "mission": "not_attached",
            "workflow": "not_attached",
            "policy": "not_attached",
            "audit": "not_attached",
            "artifact": "not_attached",
            "approval": "not_attached",
            "preview": "not_attached",
            "knowledge": "not_attached",
            "memory": "not_attached",
        }
    )
    available_capability_names: Tuple[str, ...] = field(
        default_factory=lambda: (
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
    )

    def capability_status(self, name: str) -> str:
        """Status attach capability (read-only accessor; bukan logic eksekusi)."""
        return self.capabilities.get(name, "unknown")

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "mode": self.mode,
            "read_only": self.read_only,
            "capabilities": dict(self.capabilities),
            "available_capability_names": list(self.available_capability_names),
        }

    def capability_list(self) -> List[str]:
        return list(self.available_capability_names)
