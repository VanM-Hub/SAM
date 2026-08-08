# Mission Context & Insight - IP-3.5-002 (AO-ENG-001, MISSION-3.5)
# WP-13 (Mission Context) + WP-14 (Mission Insight).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail: Mission Context != State Control; Insight != Authority;
#   Insight adalah agregasi observasional, bukan keputusan operasi.

"""Mission Context & Insight.

Menyediakan konteks mission (identitas + hubungan mission di dalam tampilan)
dan insight mission (ringkasan observasional multi-mission). Semua agregasi
bersifat deterministik & read-only; platform tidak pernah mengambil keputusan
eksekusi mission.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Sequence


@dataclass(frozen=True)
class MissionContext:
    """Konteks mission di dalam platform workspace.

    Menyimpan identitas mission aktif & peran mission untuk navigasi.
    Context milik layer tampilan; bukan otoritas / bukan state runtime.
    """

    active_mission_id: str = ""
    # Mission yang sedang fokus (deklaratif).
    focus_mission_id: str = ""

    def with_active(self, mission_id: str) -> "MissionContext":
        return MissionContext(
            active_mission_id=mission_id or self.active_mission_id,
            focus_mission_id=self.focus_mission_id,
        )

    def with_focus(self, mission_id: str) -> "MissionContext":
        return MissionContext(
            active_mission_id=self.active_mission_id,
            focus_mission_id=mission_id or self.focus_mission_id,
        )


@dataclass(frozen=True)
class MissionInsight:
    """Insight observasional lintas mission (deterministik, read-only).

    Merangkum keadaan mission yang DIBERIKAN; bukan rekomendasi aksi.
    """

    total_missions: int = 0
    active_count: int = 0
    complete_count: int = 0
    # Progress rata-rata [0,1] atas mission yang punya data.
    average_progress: float = 0.0

    @property
    def has_data(self) -> bool:
        return self.total_missions > 0


def build_insight(
    missions: Sequence["object"],
) -> MissionInsight:
    """Build insight dari koleksi MissionInput (deterministik).

    Menghitung total, active, complete, dan average progress. Murni
    agregasi observasional; tidak menjalankan apa pun.
    """
    missions = list(missions)
    total = len(missions)
    active = sum(1 for m in missions if getattr(m, "state", "") == "active")
    complete = sum(1 for m in missions if getattr(m, "state", "") == "complete")
    progs = [float(getattr(m, "progress", 0.0)) for m in missions]
    avg = (sum(progs) / len(progs)) if progs else 0.0
    return MissionInsight(
        total_missions=total,
        active_count=active,
        complete_count=complete,
        average_progress=min(1.0, max(0.0, avg)),
    )
