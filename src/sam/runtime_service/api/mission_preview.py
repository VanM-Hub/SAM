"""Mission Preview Consumer (WP-B2, Program B - Runtime Realization).

AD-ENG-002 Activation Pattern Standard (mengikuti PolicyPreviewConsumer/
WorkflowPreviewConsumer yang SUDAH ADA):
  Conversation -> RuntimeService -> ExecutionRuntime(preview)
  -> MissionPreviewConsumer -> MissionRegistry -> ConversationMissionBridge -> STOP.

Wire Mission di entry via jalur resmi, pakai MissionRegistry + ConversationMissionBridge
yang SUDAH ADA. Mission jadi capability governance aktif & terpublikasi (lifecycle +
metadata + governance), read-only.

Tanpa runtime baru; tanpa mengubah RuntimeService di luar activation flow resmi;
tanpa shortcut; preview-only (tidak mengorkestrasi workflow, tidak mengeksekusi
mission, tidak memanggil Provider/Connector/ExecutionRuntime lain).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sam.mission_runtime import MissionRegistry, ConversationMissionBridge, MissionDescriptor


@dataclass(frozen=True)
class MissionPreview:
    """Snapshot mission (immutable, read-only). Preview-only, no execution.

    Field paralel dengan PolicyPreview/WorkflowPreview: identitas + status +
    metadata publikasi. as_dict() utk payload REST/CLI.
    """
    mission_id: str
    found: bool = False
    name: str = ""
    category: str = ""
    description: str = ""
    tags: Tuple[str, ...] = ()
    status: str = ""
    integration_ok: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "found": self.found,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "tags": list(self.tags),
            "status": self.status,
            "integration_ok": self.integration_ok,
            "external_calls": self.external_calls,
        }


class MissionPreviewConsumer:
    """Consumer Mission via jalur Conversation -> RuntimeService.

    READ-ONLY: resolve mission dari MissionRegistry (yang sudah ada), via
    ConversationMissionBridge. Mission jadi capability governance yang aktif,
    mempublikasikan lifecycle + metadata + governance state.

    BUKAN pipeline internal; tidak mengubah ExecutionRuntime/RuntimeService/
    mission_runtime; tidak mengorkestrasi/mengeksekusi mission.
    """

    def __init__(self, registry: Optional[MissionRegistry] = None) -> None:
        self._registry = registry or MissionRegistry()
        self._bridge = ConversationMissionBridge(self._registry)

    @property
    def registry(self) -> MissionRegistry:
        return self._registry

    @property
    def bridge(self) -> ConversationMissionBridge:
        return self._bridge

    def list_missions(self) -> List[str]:
        """Daftar id mission (read-only)."""
        return list(self._registry.ids())

    def resolve_mission(self, mission_id: str) -> MissionPreview:
        """Resolve satu mission via bridge (read-only, no execution)."""
        desc = self._bridge.locate(mission_id)
        if desc is None:
            return MissionPreview(mission_id=mission_id, found=False)
        return MissionPreview(
            mission_id=mission_id,
            found=True,
            name=desc.name,
            category=desc.category,
            description=desc.description,
            tags=tuple(desc.tags),
            status="published",
            integration_ok=True,
            external_calls=0,
        )

    def summary(self) -> dict:
        """Ringkasan mission registry (read-only)."""
        return self._bridge.summary()


def build_mission_preview_consumer(
    registry: Optional[MissionRegistry] = None,
) -> MissionPreviewConsumer:
    """Factory activation: buat MissionPreviewConsumer (registration point).

    Activation entry resmi: menghasilkan consumer yang siap didaftarkan sebagai
    handler preview Mission, tanpa mengubah Runtime Model / RuntimeService.
    """
    return MissionPreviewConsumer(registry=registry)
