# Mission API - IP-3.5-002 (AO-ENG-001, MISSION-3.5)
# WP-15: facade read/assemble-only untuk Mission Experience.
#        Titik masuk bagi presentation untuk menyajikan pandangan mission.
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail (IP-3.5): Mission API bersifat READ/PREPARE/PRESENT only.
#   TIDAK ada: mission execution, coordinator call, allocator, builder
#   mutation, registry write, state transition. Mission API PRESENTS
#   mission; never runs mission.

"""Mission API (Facade).

Facade read/assemble-only untuk Mission Experience. Menerima data mission
dari luar (governed runtime service / caller), menyusun pandangan mission-
centric (workspace, timeline, journey, progress, context, insight), dan
menyajikannya. Tidak memanipulasi mission runtime.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from sam.platform.mission_workspace import (
    MissionInput,
    MissionTimelineInput,
    MissionHealthInput,
    MissionJourney,
    MissionJourneyStep,
    MissionWorkspaceView,
    build_journey,
)
from sam.platform.mission_timeline import (
    MissionTimelineView,
    MissionProgress,
    compute_progress,
    timeline_from_checkpoints,
)
from sam.platform.mission_context import (
    MissionContext as MCtx,
    MissionInsight,
    build_insight,
)


@dataclass(frozen=True)
class MissionSnapshot:
    """Snapshot baca-saja Mission Experience untuk disajikan.

    Immutable. Menyajikan keadaan mission; tidak memegang otoritas eksekusi.
    """

    mission_id: str
    title: str
    state: str
    stage: str
    progress: float
    journey: MissionJourney
    timeline: MissionTimelineView
    health_state: str
    health_checks: Tuple[str, ...]


class MissionAPI:
    """Facade read-only untuk Mission Experience.

    Menerima input mission (data diberikan), menyusun pandangan mission-
    centric, dan menyajikannya untuk presentation layer. DILARANG
    mengeksekusi / memanipulasi mission runtime.
    """

    def __init__(self) -> None:
        self._missions: Dict[str, MissionInput] = {}
        self._timelines: Dict[str, MissionTimelineInput] = {}
        self._health: Dict[str, MissionHealthInput] = {}
        self._journeys: Dict[str, MissionJourney] = {}

    # --- Input (diberikan dari luar, bukan ditarik dari runtime) ------------

    def register_mission(self, mission: MissionInput) -> None:
        """Terima data mission dari luar untuk penyajian.

        Hanya menyimpan data; tidak mengeksekusi mission.
        """
        self._missions[mission.mission_id] = mission

    def register_timeline(self, timeline: MissionTimelineInput) -> None:
        self._timelines[timeline.mission_id] = timeline

    def register_health(self, health: MissionHealthInput) -> None:
        self._health[health.mission_id] = health

    def register_journey(self, journey: MissionJourney) -> None:
        self._journeys[journey.mission_id] = journey

    # --- Assembly (read-only) -----------------------------------------------

    def view(self) -> MissionWorkspaceView:
        """Pandangan mission-centric lengkap (deterministik)."""
        return MissionWorkspaceView(
            missions=tuple(sorted(self._missions.values(),
                                  key=lambda m: m.mission_id)),
            journeys=tuple(sorted(self._journeys.values(),
                                  key=lambda j: j.mission_id)),
            timelines=tuple(sorted(self._timelines.values(),
                                   key=lambda t: t.mission_id)),
            health=tuple(sorted(self._health.values(),
                                key=lambda h: h.mission_id)),
        )

    def snapshot(self, mission_id: str) -> Optional[MissionSnapshot]:
        """Snapshot mission tertentu untuk disajikan (atau None)."""
        m = self._missions.get(mission_id)
        if m is None:
            return None
        tl = self._timelines.get(mission_id)
        timeline_view = (
            timeline_from_checkpoints(mission_id, tl.checkpoints)
            if tl else MissionTimelineView(mission_id=mission_id)
        )
        journey = self._journeys.get(mission_id) or build_journey(
            mission_id, timeline_view.checkpoints
        )
        h = self._health.get(mission_id)
        return MissionSnapshot(
            mission_id=m.mission_id,
            title=m.title,
            state=m.state,
            stage=m.stage,
            progress=m.progress,
            journey=journey,
            timeline=timeline_view,
            health_state=h.state if h else "unknown",
            health_checks=h.checks if h else (),
        )

    def insights(self) -> MissionInsight:
        """Insight observasional lintas mission (deterministik)."""
        return build_insight(self._missions.values())

    def mission_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._missions.keys()))
