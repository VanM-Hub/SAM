"""Mission Cognitive Runtime (MCR) — application result contract.

`AgentRunResult` adalah compatibility DTO untuk REST (application boundary).
Kontraknya dipertahankan persis (mission_id/ok/final_state/steps/external_calls/
detail) agar serializer route REST tidak berubah. Ia dipindahkan dari
`agent/runtime/` (legacy AgentRuntime retired — Step 9B) ke bounded context
Mission Cognitive Runtime, berdekatan dengan canonical `MissionCycleResult`
yang di-map kepadanya via `map_cognitive_result` di `api.llm_wiring`.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentRunResult:
    """Hasil menjalankan mission (immutable) — kontrak REST compatibility.

    Dipetakan dari `MissionCycleResult` oleh application use case
    (`AgentBridge.map_cognitive_result`). Serializer route REST hanya membaca
    field-field ini dan TIDAK perlu tahu internal MCR.
    """
    mission_id: str
    ok: bool = False
    final_state: str = "Created"
    steps: int = 0
    external_calls: int = 0
    detail: str = ""


__all__ = ["AgentRunResult"]
