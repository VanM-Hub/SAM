# Mission Timeline & Progress - IP-3.5-002 (AO-ENG-001, MISSION-3.5)
# WP-10 (Mission Timeline) + WP-12 (Mission Progress).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail: Timeline != Execution Schedule; Progress != Control;
#   Progress adalah deskripsi kemajuan, bukan instruksi untuk memajukan.

"""Mission Timeline & Progress.

Menyajikan timeline mission (urutan checkpoint) dan progress (tingkat
kemajuan) secara deklaratif. Platform menghitung progress dari input yang
DIBERIKAN; ia tidak pernah memajukan/mengubah mission runtime.
"""

from dataclasses import dataclass
from typing import Tuple, Sequence, Optional


@dataclass(frozen=True)
class MissionTimelineView:
    """Timeline mission sebagai urutan checkpoint untuk tampilan.

    Checkpoints diambil dari input; tidak ada perintah eksekusi.
    """

    mission_id: str
    checkpoints: Tuple[str, ...] = ()
    current_index: int = -1

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "current_index",
            max(-1, min(int(self.current_index), len(self.checkpoints) - 1)),
        )

    def is_complete(self) -> bool:
        return len(self.checkpoints) > 0 and self.current_index >= len(self.checkpoints) - 1


@dataclass(frozen=True)
class MissionProgress:
    """Tingkat kemajuan mission (presentational, immutable).

    progress dalam [0.0, 1.0]. Deskripsi, bukan kontrol.
    """

    mission_id: str
    progress: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "progress", min(1.0, max(0.0, float(self.progress))))

    @property
    def percent(self) -> float:
        return self.progress * 100.0


def compute_progress(
    mission_id: str, done: int, total: int
) -> MissionProgress:
    """Hitung progress dari jumlah selesai / total (deterministik).

    Murni komputasi tampilan; tidak memengaruhi mission.
    """
    if total <= 0:
        return MissionProgress(mission_id=mission_id, progress=0.0)
    return MissionProgress(
        mission_id=mission_id, progress=min(1.0, max(0.0, done / total))
    )


def timeline_from_checkpoints(
    mission_id: str, checkpoints: Sequence[str], current_index: int = -1
) -> MissionTimelineView:
    """Buat timeline view dari checkpoints (deterministik)."""
    return MissionTimelineView(
        mission_id=mission_id,
        checkpoints=tuple(checkpoints),
        current_index=int(current_index),
    )
