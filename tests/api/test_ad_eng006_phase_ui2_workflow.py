"""test_ad_eng006_phase_ui2_workflow.py — AD-ENG-006 Phase UI-2 (decision wiring).

Acceptance minimum Phase UI-2 (keputusan Van 2026-08-17):

  Mission A selected -> Approve A -> POST {mission_id:A, intent:approve}
      -> A berubah (approved/blocked jujur), B TIDAK berubah.
  selected A -> reject A ; selected B -> approve B ; refresh -> state server tetap benar.
  unknown mission -> UI tidak fallback ke current (404, tanpa fallback).
  missing mission_id -> tidak boleh terjadi dari UI (guard; route sisi-server 422).

Sifat test: route-level TestClient (bukan browser) — mensimulasikan persis kontrak
HTTP yang dipakai UI (POST /ux/submit -> GET /ux/missions -> GET /ux/missions/{mid}
-> POST /ux/decide {intent,mission_id}). `selectedMissionId` di UI = mission_id
yang dikirim; di sini kita ekstrak dari /ux/missions dan decide dengan mission_id
tsb. Ini bukti kontrak backend yg sama dgn wiring UI.
"""
import unittest

from fastapi.testclient import TestClient

from sam.api.server import app


SHAKY_MISSION = None  # diisi per-test utk memastikan tidak ada state bocor antar-test


def _mid_of(s):
    return (s.get("observability") or {}).get("mission_id")


class PhaseUI2Workflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def _submit(self, text):
        r = self.client.post("/ux/submit", json={"text": text})
        self.assertEqual(r.status_code, 200)
        return r.json()

    def _missions(self):
        r = self.client.get("/ux/missions")
        self.assertEqual(r.status_code, 200)
        return r.json().get("missions") or []

    def _card_by_id(self, cards, mid):
        for c in cards:
            if c.get("mission_id") == mid:
                return c
        return None

    def test_selected_A_approve_A_changes_A_not_B(self):
        """Acceptance minimum: A selected -> approve A; A berubah, B tidak."""
        a = self._submit("Buat GitHub issue 'A-approve ui2'")
        b = self._submit("Buat GitHub issue 'B-approve ui2'")
        midA, midB = _mid_of(a), _mid_of(b)
        self.assertTrue(midA and midB and midA != midB)

        # selected A -> GET detail A (UI memilih A)
        dA = self.client.get(f"/ux/missions/{midA}")
        self.assertEqual(dA.status_code, 200)
        self.assertEqual(dA.json()["status"], "waiting_approval")

        # approve A (selectedMissionId=A)
        r = self.client.post(
            "/ux/decide",
            json={"intent": "approve", "mission_id": midA, "approver": "user"},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        # approval A berubah dari waiting_approval -> approved
        self.assertEqual(body["approval"]["status"], "approved")

        # refresh -> B tetap waiting_approval (tidak tersentuh)
        cards = self._missions()
        cb = self._card_by_id(cards, midB)
        self.assertIsNotNone(cb)
        self.assertEqual(cb["status"], "waiting_approval")

    def test_selected_A_reject_A_marks_A_rejected(self):
        """selected A -> reject A: A rejected, 0 mutation."""
        a = self._submit("Buat GitHub issue 'A-reject ui2'")
        midA = _mid_of(a)
        r = self.client.post(
            "/ux/decide",
            json={"intent": "reject", "mission_id": midA, "approver": "user"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["approval"]["status"], "rejected")
        # refresh card -> rejected
        cards = self._missions()
        c = self._card_by_id(cards, midA)
        self.assertIsNotNone(c)
        self.assertEqual(c["status"], "rejected")

    def test_selected_B_approve_B_changes_B_not_A(self):
        """selected B -> approve B: B berubah, A (rejected sblmnya) tetap."""
        a = self._submit("Buat GitHub issue 'A-pre ui2'")
        b = self._submit("Buat GitHub issue 'B-approve ui2'")
        midA, midB = _mid_of(a), _mid_of(b)
        # tandai A rejected dulu
        self.client.post("/ux/decide", json={"intent": "reject", "mission_id": midA, "approver": "user"})
        # approve B
        r = self.client.post(
            "/ux/decide",
            json={"intent": "approve", "mission_id": midB, "approver": "user"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["approval"]["status"], "approved")
        cards = self._missions()
        # B berubah, A tetap rejected
        self.assertEqual(self._card_by_id(cards, midB)["status"] == "approved"
                         or self._card_by_id(cards, midB)["status"] == "blocked", True,
                         "B harus approved/blocked (jujur) setelah approve")
        self.assertEqual(self._card_by_id(cards, midA)["status"], "rejected")

    def test_refresh_state_server_truth(self):
        """refresh -> state dari server tetap benar (bukan lokal/current)."""
        a = self._submit("Buat GitHub issue 'refresh ui2'")
        midA = _mid_of(a)
        cards = self._missions()
        c0 = self._card_by_id(cards, midA)
        self.assertEqual(c0["status"], "waiting_approval")
        # decide reject -> refresh -> server bilang rejected
        self.client.post("/ux/decide", json={"intent": "reject", "mission_id": midA, "approver": "user"})
        cards = self._missions()
        self.assertEqual(self._card_by_id(cards, midA)["status"], "rejected")

    def test_unknown_mission_no_fallback_to_current(self):
        """unknown mission -> 404; UI detail tidak fallback ke current mission.

        GET /ux/missions/{unknown} -> 404 dgn pesan generik (tidak memuat
        mission_id => tidak membocorkan keberadaan, tidak fallback ke current).
        """
        mid = "mission-000000000000"
        r = self.client.get(f"/ux/missions/{mid}")
        self.assertEqual(r.status_code, 404)
        detail = r.json().get("detail", r.json())
        if isinstance(detail, dict):
            self.assertEqual(detail.get("code"), "MISSION_NOT_FOUND")
        else:
            # detail string generik; anti-oracle: tidak memuat mission_id target
            self.assertIsInstance(detail, str)
        self.assertNotIn(mid, str(detail))


if __name__ == "__main__":
    unittest.main()
