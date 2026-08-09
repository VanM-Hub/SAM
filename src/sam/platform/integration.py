# Platform Integration - IP-3.5-005 (AO-ENG-001, MISSION-3.5)
# WP-29 (E2E Integration) + WP-30 (Regression Gate).
#
# Bound context: src/sam/platform/ (consumer-only, presentation-passive).
# Guardrail: Integration = menyusun seluruh pandangan platform menjadi satu
#   entry point presentasi. TIDAK menambah governance/runtime/authority.

"""Platform Integration.

Menyatukan Platform Workspace, Mission Experience, Citizen Experience, dan
Explainability Experience menjadi satu PlatformPresentation yang kohesif
(entry point unifikasi untuk presentation layer). Semua tetap read-only;
platform never performs governance.
"""

from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple

from sam.platform.workspace_api import WorkspaceAPI, WorkspaceSnapshot, default_workspace
from sam.platform.mission_api import MissionSnapshot as MSnap
from sam.platform.citizen_api import CitizenSnapshot as CSnap
from sam.platform.explain_api import ExplainabilitySnapshot as ESnap


@dataclass(frozen=True)
class PlatformPresentation:
    """Presentasi platform terpadu (read/assemble, immutable).

    Gabungan snapshot keempat experience; entry point bagi presentation
    layer untuk menyajikan keseluruhan platform. Tidak memegang otoritas.
    """

    workspace: WorkspaceSnapshot
    mission: Optional[MSnap] = None
    citizen: Optional[CSnap] = None
    explainability: Optional[ESnap] = None

    @property
    def has_mission(self) -> bool:
        return self.mission is not None

    @property
    def has_citizen(self) -> bool:
        return self.citizen is not None

    @property
    def has_explainability(self) -> bool:
        return self.explainability is not None

    def summary_keys(self) -> Tuple[str, ...]:
        """Kunci ringkasan platform (deterministik, ASCII)."""
        keys = ["workspace"]
        if self.mission is not None:
            keys.append("mission")
        if self.citizen is not None:
            keys.append("citizen")
        if self.explainability is not None:
            keys.append("explainability")
        return tuple(keys)


class PlatformEngine:
    """Facade terpadu untuk presentation layer.

    Memegang referensi ke keempat experience API dan menyusun presentasi
    platform secara konsisten. DILARANG mengeksekusi/memanipulasi apa pun.
    """

    # Urutan deterministik/stable untuk agregasi multi-API.
    def __init__(
        self,
        workspace: "WorkspaceAPI",
        mission=None,
        citizen=None,
        explainability=None,
    ) -> None:
        self._workspace = workspace
        self._mission = mission
        self._citizen = citizen
        self._explainability = explainability

    def present(self, session_id: str = "default") -> PlatformPresentation:
        """Susun presentasi platform lengkap (deterministik).

        Menggabungkan snapshot workspace + mission + citizen + explainability
        bila tersedia. Hanya membaca; tidak mengeksekusi apa pun.
        """
        ws = self._workspace.snapshot(session_id)
        # mission: pick first mission id (deterministik) bila ada
        m_snap = None
        if self._mission is not None:
            ids = self._mission.mission_ids()
            if ids:
                m_snap = self._mission.snapshot(ids[0])
        c_snap = self._citizen.snapshot() if self._citizen else None
        e_snap = self._explainability.snapshot() if self._explainability else None
        return PlatformPresentation(
            workspace=ws,
            mission=m_snap,
            citizen=c_snap,
            explainability=e_snap,
        )

    def coverage(self) -> Tuple[str, ...]:
        """Daftar experience yang terpasang (deterministik)."""
        out = ["platform"]
        if self._mission is not None:
            out.append("mission")
        if self._citizen is not None:
            out.append("citizen")
        if self._explainability is not None:
            out.append("explainability")
        return tuple(out)
