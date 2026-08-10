"""Mission Cognitive Runtime (MCR) — Cognitive Kernel bounded context.

Mengorkestrasi siklus kognitif misi dengan memanggil kemampuan SAM yang sudah
ada (foundation immutable): ReasoningEngine (governed_reasoning) untuk reason,
Governance Kernel eksternal untuk govern (handoff wajib), jalur execution_runtime
untuk execute, observation (read-only) untuk observe, dan ReflectionManager
(healing) untuk reflect+learn.

MCR adalah pure orchestrator, bukan God Object. Tidak meniru OpenClaw, tidak
meng-embed GPT, tidak mengubah foundation.
"""

from sam.mission_cognition.runtime import (
    MissionCognitiveRuntime,
    MissionCycleResult,
    MissionCycleStatus,
)

__all__ = [
    "MissionCognitiveRuntime",
    "MissionCycleResult",
    "MissionCycleStatus",
]
