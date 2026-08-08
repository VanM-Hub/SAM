# Mission Workspace - IP-3.5-002 (AO-ENG-001, MISSION-3.5)
# WP-09: menyajikan Mission menjadi entry point operasional berbasis mission
#        (mission-centric workflow).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# CAPABILITY BOUNDARY: Mission Experience MENERIMA data mission dari luar
#   (Runtime Services / caller) sebagai input, TIDAK mengimpor & memanipulasi
#   mission_runtime. Tidak ada builder/coordinator/allocator/registry call.
#   Platform mengagregasi & menyajikan, tidak mengeksekusi mission.
# Guardrail: Mission Experience != Mission Execution; Journey != Governance;
#   Progress != Control; Present mission != Run mission.

"""Mission Workspace.

Menyediakan pandangan mission-centric: ringkasan mission, progress, dan
susunan misi yang disajikan. Seluruh input diberikan dari luar (dataclass
immutable sederhana); platform hanya menyusun & menyajikan secara
deterministik, tanpa memanipulasi mission runtime.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Sequence


# --- Mission input model (diberikan dari luar, bukan diambil dari runtime) ---

@dataclass(frozen=True)
class MissionInput:
    """Data mission yang DIBERIKAN ke platform untuk penyajian.

    Platform tidak menarik mission dari runtime; ia menerima ringkasan /
    snapshot mission dari caller (governed runtime service). Murni input.
    """

    mission_id: str
    title: str = ""
    # Status/state mission sebagai label deklaratif (mis. "active", "pending",
    # "complete"). Bukan perintah untuk mengubah state.
    state: str = "unknown"
    # Fase/tahapan saat ini (mis. "planning", "execution", "review").
    stage: str = ""
    # 0.0 - 1.0; deskripsi kemajuan, bukan kontrol.
    progress: float = 0.0

    def __post_init__(self) -> None:
        if not self.mission_id or not self.mission_id.strip():
            raise ValueError("mission_id wajib diisi.")
        if not (0.0 <= self.progress <= 1.0):
            # clamp deterministik, bukan error
            object.__setattr__(self, "progress", min(1.0, max(0.0, self.progress)))


@dataclass(frozen=True)
class MissionTimelineInput:
    """Timeline mission (checkpoints) yang DIBERIKAN ke platform.

    Checkpoint bersifat deklaratif (urutan tampilan), bukan perintah eksekusi.
    """

    mission_id: str
    checkpoints: Tuple[str, ...] = ()


@dataclass(frozen=True)
class MissionHealthInput:
    """Health mission (observasional) yang DIBERIKAN ke platform.

    Health bersifat observasional; platform tidak mengubahnya.
    """

    mission_id: str
    state: str = "unknown"
    checks: Tuple[str, ...] = ()


# --- Mission presentation model ---------------------------------------------

@dataclass(frozen=True)
class MissionJourneyStep:
    """Satu langkah perjalanan misi (presentation view).

    Perepresentasikan progres dari kumpulan checkpoints; bukan perintah.
    """

    label: str
    order: int = 0
    done: bool = False


@dataclass(frozen=True)
class MissionJourney:
    """Perjalanan misi sebagai urutan langkah presentasi.

    Aggregate deterministik dari checkpoints; murni tampilan.
    """

    mission_id: str
    steps: Tuple[MissionJourneyStep, ...] = ()

    def completed_count(self) -> int:
        return sum(1 for s in self.steps if s.done)

    def total_count(self) -> int:
        return len(self.steps)

    def completion_ratio(self) -> float:
        if not self.steps:
            return 0.0
        return self.completed_count() / self.total_count()


@dataclass(frozen=True)
class MissionWorkspaceView:
    """Pandangan mission-centric lengkap untuk disajikan.

    Immutable & deterministik. Menggabungkan mission input + journey.
    """

    missions: Tuple[MissionInput, ...] = ()
    journeys: Tuple[MissionJourney, ...] = ()
    timelines: Tuple[MissionTimelineInput, ...] = ()
    health: Tuple[MissionHealthInput, ...] = ()

    def mission(self, mission_id: str) -> Optional[MissionInput]:
        for m in self.missions:
            if m.mission_id == mission_id:
                return m
        return None

    def journey(self, mission_id: str) -> Optional[MissionJourney]:
        for j in self.journeys:
            if j.mission_id == mission_id:
                return j
        return None

    def timeline(self, mission_id: str) -> Optional[MissionTimelineInput]:
        for t in self.timelines:
            if t.mission_id == mission_id:
                return t
        return None

    def health(self, mission_id: str) -> Optional[MissionHealthInput]:
        for h in self.health:
            if h.mission_id == mission_id:
                return h
        return None


def build_journey(
    mission_id: str, checkpoints: Sequence[str]
) -> MissionJourney:
    """Build perjalanan misi dari checkpoints (deterministik, presentational).

    Semua langkah dianggap belum selesai (done=False) kecuali ditandai;
    aggregate murni untuk tampilan.
    """
    steps = tuple(
        MissionJourneyStep(label=label, order=idx)
        for idx, label in enumerate(checkpoints)
    )
    return MissionJourney(mission_id=mission_id, steps=steps)
