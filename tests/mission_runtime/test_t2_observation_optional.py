"""T2 - Observation OPTIONAL (read-only, best-effort) di MCR (keputusan CA 2026-08-11).

Keputusan (berbasis prinsip EA-C04/IP-3.2 "Observe, never govern" + "tanpa authority"):
- Observation di MCR bersifat OPTIONAL/best-effort, BUKAN required.
- Observation TIDAK boleh menggagalkan/memblokir siklus (tidak punya authority).
- Siklus yang sudah lolos governance tetap COMPLETED walau observasi gagal/tak ada engine.
- Kegagalan observasi dicatat eksplisit lewat `observation_available=False`
  (auditable), bukan diam-diam None menyerupai sukses.
"""
import asyncio

from sam.mission_cognition import MissionCognitiveRuntime, MissionCycleStatus


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class _BadObservationEngine:
    """Engine yang selalu gagal recomend() — mensimulasikan observasi error."""

    def recommend(self):
        raise RuntimeError("observation provider down")


class _GoodObservationEngine:
    """Engine yang menghasilkan rekomendasi read-only (dict)."""

    def __init__(self):
        self.calls = 0
        self.value = {"observations": ["healthy"], "recommendations": ["none"]}

    def recommend(self):
        self.calls += 1
        return self.value


class TestT2ObservationOptional:
    """T2: Observation = optional/best-effort, tidak menggagalkan siklus."""

    def test_tanpa_engine_siklus_tetap_completed(self) -> None:
        """No observation engine -> siklus tetap COMPLETED (bukan blocked/failed)."""
        mcr = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False, observation_engine=None
        )
        res = _run(mcr.run_cycle("mission", evidences=()))
        assert res.status is MissionCycleStatus.COMPLETED
        assert res.observation_available is False
        assert res.observation_summary is None

    def test_engine_gagal_siklus_tetap_completed(self) -> None:
        """Observation engine error -> siklus tetap COMPLETED (graceful)."""
        mcr = MissionCognitiveRuntime(
            governance_engine=None,
            governance_required=False,
            observation_engine=_BadObservationEngine(),
        )
        res = _run(mcr.run_cycle("mission", evidences=()))
        assert res.status is MissionCycleStatus.COMPLETED
        assert res.observation_available is False
        assert res.observation_summary is None

    def test_observation_tidak_punya_authority_memblokir(self) -> None:
        """Observation TIDAK pernah memicu BLOCKED/FAILED (tidak punya authority)."""
        mcr = MissionCognitiveRuntime(
            governance_engine=None,
            governance_required=False,
            observation_engine=_BadObservationEngine(),
        )
        res = _run(mcr.run_cycle("mission", evidences=()))
        assert res.status not in (
            MissionCycleStatus.BLOCKED,
            MissionCycleStatus.FAILED,
        )

    def test_dengan_engine_observation_tersedia(self) -> None:
        """Engine ada & sukses -> observation_available=True, summary terisi."""
        good = _GoodObservationEngine()
        mcr = MissionCognitiveRuntime(
            governance_engine=None,
            governance_required=False,
            observation_engine=good,
        )
        res = _run(mcr.run_cycle("mission", evidences=()))
        assert res.status is MissionCycleStatus.COMPLETED
        assert res.observation_available is True
        assert good.calls >= 1
        assert res.observation_summary is not None
        assert res.observation_summary["observations"] == ["healthy"]

    def test_observasi_tetap_read_only_tidak_mengubah_keputusan(self) -> None:
        """Observation read-only: tidak mengubah keputusan governance hasil cycle."""
        # Jalankan dua cycle identik, beda hanya ada/tidaknya observation engine.
        # governance_decision harus sama (observasi tidak punya authority).
        mcr_no_obs = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False, observation_engine=None
        )
        mcr_obs = MissionCognitiveRuntime(
            governance_engine=None,
            governance_required=False,
            observation_engine=_GoodObservationEngine(),
        )
        res_no_obs = _run(mcr_no_obs.run_cycle("mission", evidences=()))
        res_obs = _run(mcr_obs.run_cycle("mission", evidences=()))
        assert res_obs.status is MissionCycleStatus.COMPLETED
        assert res_obs.governance_decision == res_no_obs.governance_decision
        # observation tidak mengubah status siklus
        assert res_obs.status is res_no_obs.status

    def test_field_auditable_ada_di_to_dict(self) -> None:
        """observation_available terekspos di to_dict (auditable)."""
        mcr = MissionCognitiveRuntime(
            governance_engine=None, governance_required=False, observation_engine=None
        )
        res = _run(mcr.run_cycle("mission", evidences=()))
        d = res.to_dict()
        assert "observation_available" in d
        assert d["observation_available"] is False
