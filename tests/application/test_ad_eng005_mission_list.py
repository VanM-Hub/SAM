"""test_ad_eng005_mission_list.py — AD-ENG-005 Mission List (Layer 2, Opsi 2).

Buktikan keputusan Van (2026-08-16) + kontrak ADR:
  - `mission-*` = canonical Mission identity (SURVIVE di durable repository).
  - `MultiMissionService` = coordination/registration boundary: MissionUXService
    tetap jalur pembentukan + persist; MultiMissionService meregistrasikan
    canonical mission-* ke MissionRegistry (TIDAK membuat Mission kedua / m_*).
  - Enumerasi `GET /ux/missions` dari repository durable + overlay registry
    (precedence live > durable; absence from registry != mission tidak ada).
  - Semantik Opsi-2: satu Conversation dapat banyak command; setiap command
    yang menghasilkan Mission = satu Mission aggregate tersendiri (mission-*).

Test berskala application-layer dengan instance segar (anti test pollution) &
`_interpret` di-mock agar deterministik (tanpa AI). Persistence memakai
InMemory durable repository.
"""
from __future__ import annotations

import pytest

from sam.application.ux.service import MissionUXService
from sam.application.ux.mission_registry import MultiMissionService
from sam.application.ux.conversation import ConversationService
from sam.application.ux.repositories import (
    InMemoryConversationRepository,
    InMemoryPersistenceUnit,
)
from sam.application.ux.state import UxStateStatus
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from sam.api.server import app


# ---------------------------------------------------------------------------
# _interpret deterministik (bukan AI) — menghasilkan operasi MISSION nyata
# ---------------------------------------------------------------------------
def _fake_interpret_github(text):
    return (
        "github.create_issue",
        "VanM-Hub/test-issues",
        "SAM memahami: membuat GitHub issue (kernel test AD-ENG-005).",
        ["verifikasi koneksi", "membuat issue", "verifikasi independen"],
        "SAM akan membuat GitHub issue di repo VanM-Hub/test-issues.",
        "Persetujuan diperlukan sebelum eksekusi.",
    )


def _fake_interpret_observe(text):
    return (
        "environment.observe",
        "host",
        "SAM memahami: memeriksa komputer (observe) kernel test AD-ENG-005.",
        ["mengumpulkan data host", "menilai status"],
        "SAM akan memeriksa status komputer.",
        "Persetujuan diperlukan sebelum eksekusi.",
    )


@pytest.fixture(autouse=True)
def _no_pg(monkeypatch):
    """Pastikan test ini berjalan di dev (tanpa PG/DSN) → persistence InMemory.

    Juga jaga agar MissionUXService default tidak otomatis memakai PG.
    """
    monkeypatch.delenv("SAM_PG_DSN", raising=False)
    monkeypatch.delenv("SAM_PG_PASSWORD", raising=False)
    monkeypatch.setenv("SAM_ENV", "")


@pytest.fixture
def interpret(monkeypatch):
    monkeypatch.setattr(
        MissionUXService, "_interpret", staticmethod(_fake_interpret_github)
    )
    return MissionUXService


# ---------------------------------------------------------------------------
# Helper: bangun graph nyata (unit durable + multi + conversation) TERISOLASI
# ---------------------------------------------------------------------------
class _Graph:
    """Pegang persistence unit + MultiMissionService + ConversationService +
    MissionUXService sumber, berbagi unit durable yang SAMA."""

    def __init__(self, interpret):
        self.unit = InMemoryPersistenceUnit()
        self.source = MissionUXService(persistence=self.unit)
        self.multi = MultiMissionService(
            service_factory=lambda: MissionUXService(persistence=self.unit)
        )
        self.conv = ConversationService(
            conversation_repo=InMemoryConversationRepository(),
            mission_service=self.source,
            multi_mission=self.multi,
            tenant="default",
        )

    def command(self, text, cid=None):
        # Pastikan conversation ada (fail-closed: harus create/resume dulu).
        if cid is None:
            convo = self.conv.create_or_resume_conversation()
            return self.conv.submit_command(
                conversation_id=convo.conversation_id, text=text
            )
        # cid eksplisit wajib sudah ada (fail-closed), BUKAN dibuat diam-diam.
        if not self.conv.conversation_exists(cid):
            raise KeyError(f"conversation `{cid}` tidak ditemukan")
        return self.conv.submit_command(conversation_id=cid, text=text)

    def list_cards(self, tenant="default"):
        """Replikasi enumerasi ADR §3.1 (utanpa HTTP): durable + overlay live."""
        repo = self.unit.missions
        cards = []
        for mid in repo.list_missions():
            keys = self.multi.registry().list_keys(tenant=tenant, mission_id=mid)
            if keys:
                live = self.multi.registry().get(
                    tenant, keys[-1]["mission_id"], keys[-1].get("execution_id")
                )
                state = live
            else:
                state = repo.load_mission(mid)
            cards.append(_card(mid, state))
        cards.sort(key=lambda c: c.get("updated_at") or "", reverse=True)
        return cards

    def get_card(self, mission_id, tenant="default"):
        keys = self.multi.registry().list_keys(tenant=tenant, mission_id=mission_id)
        if keys:
            live = self.multi.registry().get(
                tenant, keys[-1]["mission_id"], keys[-1].get("execution_id")
            )
            return _card(mission_id, live)
        state = self.unit.missions.load_mission(mission_id)
        return _card(mission_id, state)


def _card(mission_id, state):
    if not isinstance(state, dict):
        return None
    understanding = state.get("understanding") or {}
    plan = state.get("plan") or {}
    execution = state.get("execution") or {}
    return {
        "mission_id": mission_id,
        "status": (
            execution.get("status")
            or (state.get("observability") or {}).get("status")
            or "unknown"
        ),
        "what_sam_understood": understanding.get("what_sam_understood") or "",
        "operation": understanding.get("operation") or "",
        "target": understanding.get("target") or "",
        "updated_at": state.get("updated_at") or "",
        "approval_required": bool(plan.get("approval_required", False)),
    }


# ---------------------------------------------------------------------------
# T1 — restart-like: mission durable (repo), registry kosong -> list tetap ada
# ---------------------------------------------------------------------------
def test_t1_repo_present_registry_empty_list_still_returns(interpret):
    """Mission ada di durable repository tapi TIDAK di registry (restart-like;
    registry hilang) -> Mission List TETAP mengembalikan mission (durable state)."""
    g = _Graph(interpret)
    g.command("buat issue github judul: T1")
    mids = g.unit.missions.list_missions()
    assert len(mids) == 1
    mission_id = mids[0]
    # Simulasi restart: registry di-KOSONGKAN (hilang saat process mati).
    g.multi.registry().clear(tenant="default")
    assert g.multi.registry().size() == 0

    cards = g.list_cards()
    assert len(cards) == 1, "mission durable harus tetap tampil walau registry kosong"
    assert cards[0]["mission_id"] == mission_id
    assert cards[0]["operation"] == "github.create_issue"
    # status dari durable state (bukan registry)
    assert cards[0]["status"] == UxStateStatus.WAITING_APPROVAL


# ---------------------------------------------------------------------------
# T2 — precedence: live registry state beda dari persisted -> live yang dipakai
# ---------------------------------------------------------------------------
def test_t2_live_overrides_durable(interpret):
    g = _Graph(interpret)
    g.command("buat issue github judul: T2")
    mids = g.unit.missions.list_missions()
    assert len(mids) == 1
    mission_id = mids[0]

    # Tirukan runtime: registry berisi state LIVE "running", durable "waiting".
    import copy
    durable = copy.deepcopy(g.unit.missions.load_mission(mission_id))
    durable.setdefault("execution", {})["status"] = UxStateStatus.RUNNING
    g.multi.registry().save("default", mission_id, mission_id, durable)
    # pastikan durable (repo) sendiri masih waiting_approval
    assert (g.unit.missions.load_mission(mission_id)["execution"]["status"]) == UxStateStatus.WAITING_APPROVAL

    cards = g.list_cards()
    assert cards[0]["mission_id"] == mission_id
    assert cards[0]["status"] == UxStateStatus.RUNNING, "live state harus menang"


# ---------------------------------------------------------------------------
# INTEGRATION (wajib perintah Van): conversation command → mission-* → repo →
# multi/registry → list → SAME mission-*. Dua command = dua mission-* beda.
# ---------------------------------------------------------------------------
def test_integration_conversation_mission_list_same_mission(interpret):
    g = _Graph(interpret)
    r1 = g.command("buat issue github judul: Integrasi A")
    st1 = r1["state"]
    mission1 = (st1.observability or {}).get("mission_id")
    assert mission1, "command mission harus menghasilkan mission-*"

    # mission-* ada di durable repository & di registry (keyed mission-*, TIDAK m_*)
    assert mission1 in g.unit.missions.list_missions()
    reg_keys = [k for k in g.multi.registry().list_keys(tenant="default")]
    assert any(k["mission_id"] == mission1 for k in reg_keys), \
        "registry harus mereferensikan canonical mission-* yang SAMA"

    # Satu aggregate, satu identity: durable.mission_id == registry.mission_id
    durable = g.unit.missions.load_mission(mission1)
    assert (durable.get("observability") or {}).get("mission_id") == mission1
    reg_state = g.multi.registry().get("default", mission1, mission1)
    assert (reg_state.get("observability") or {}).get("mission_id") == mission1, \
        "registry TIDAK boleh memuat Mission identity kedua (drift)"

    # GET /ux/missions mengembalikan mission yang SAMA (mission-*)
    cards = g.list_cards()
    assert len(cards) == 1
    assert cards[0]["mission_id"] == mission1
    assert cards[0]["what_sam_understood"].startswith("SAM memahami")


def test_integration_two_commands_two_mission_aggregates(interpret, monkeypatch):
    """Dua command dalam satu Conversation menghasilkan DUA mission-* BERBEDA,
    masing-masing satu aggregate Mission (Opsi-2, bukan multi-execution)."""
    g = _Graph(interpret)
    # Satu Conversation untuk dua command (Opsi-2: banyak command per percakapan).
    convo = g.conv.create_or_resume_conversation()
    cid = convo.conversation_id
    # command 1 -> github
    monkeypatch.setattr(
        MissionUXService, "_interpret", staticmethod(_fake_interpret_github)
    )
    r1 = g.command("buat issue github judul: A", cid=cid)
    mission1 = (r1["state"].observability or {}).get("mission_id")

    # command 2 -> observe (command berbeda, mission berbeda)
    monkeypatch.setattr(
        MissionUXService, "_interpret", staticmethod(_fake_interpret_observe)
    )
    r2 = g.command("periksa komputer saya", cid=cid)
    mission2 = (r2["state"].observability or {}).get("mission_id")

    assert mission1 and mission2
    assert mission1 != mission2, "dua command harus menghasilkan dua mission-* BERBEDA"

    # Mission List memuat dua card berbeda
    cards = g.list_cards()
    ids = {c["mission_id"] for c in cards}
    assert {mission1, mission2} <= ids
    # operation masing2 sesuai command-nya (satu aggregate tiap command)
    by_id = {c["mission_id"]: c for c in cards}
    assert by_id[mission1]["operation"] == "github.create_issue"
    assert by_id[mission2]["operation"] == "environment.observe"

    # registry: dua entry, masing2 di-key mission-* canonicaal (bukan m_*)
    reg_keys = g.multi.registry().list_keys(tenant="default")
    assert len(reg_keys) == 2
    for k in reg_keys:
        assert k["mission_id"].startswith("mission-"), \
            "registry slot harus mengikuti canonical mission-*, bukan m_* sebagai Mission kedua"


def test_multimission_does_not_create_second_identity(interpret):
    """submit_mission TIDAK memanggil create(m_*): mission-* hasil submit-lah yg
    didaftarkan; tidak ada m_* yang menjadi Mission identity kedua."""
    g = _Graph(interpret)
    r = g.command("buat issue github judul: no-m_")
    mission = (r["state"].observability or {}).get("mission_id")
    # tidak ada key di _missions/registry yang berupa m_* (slot internal default)
    reg_keys = g.multi.registry().list_keys(tenant="default")
    assert all(not k["mission_id"].startswith("m_") for k in reg_keys)
    assert g.multi.mission_count() == 1


# ---------------------------------------------------------------------------
# HTTP-level (route nyata `GET /ux/missions` & `/ux/missions/{mission-*}`).
# Meng-inject `_routes` global dengan instance UxRoutes SEGAR (isolasi) dan
# DIKEMBALIKAN setelah test (anti pollution). Mission di-seed langsung ke
# instance segar agar deterministik tanpa AI.
# ---------------------------------------------------------------------------
class HttpMissionListTest(unittest.TestCase):
    def setUp(self):
        import sam.api.routes.ux as ux_routes

        self.ux_mod = ux_routes
        self.orig_routes = ux_routes._routes
        # Inject `_interpret` deterministik (tanpa AI).
        self._interpret_patch = mock.patch.object(
            MissionUXService, "_interpret", staticmethod(_fake_interpret_github)
        )
        self._interpret_patch.start()
        # Ganti `_routes` dengan instance segar (isolasi).
        fresh = ux_routes.UxRoutes()
        ux_routes._routes = fresh
        self.client = TestClient(app)
        svc = MissionUXService(persistence=fresh.mission_unit)
        st = svc.submit("buat issue github judul: seed", idempotency_key="httptest-key")
        self.mission_id = (st.observability or {}).get("mission_id")
        self.assertTrue(self.mission_id, "submit harus menghasilkan mission-*")

    def tearDown(self):
        if getattr(self, "ux_mod", None) and getattr(self, "orig_routes", None):
            self.ux_mod._routes = self.orig_routes
        if getattr(self, "_interpret_patch", None):
            self._interpret_patch.stop()

    def test_get_missions_returns_list_shape(self):
        r = self.client.get("/ux/missions")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("missions", body)
        self.assertIsInstance(body["missions"], list)
        ids = [c["mission_id"] for c in body["missions"]]
        self.assertIn(self.mission_id, ids)
        card = next(c for c in body["missions"] if c["mission_id"] == self.mission_id)
        for f in (
            "mission_id", "status", "what_sam_understood",
            "operation", "target", "updated_at", "approval_required",
        ):
            self.assertIn(f, card, f"card harus punya field {f}")
        # non-secret: TIDAK boleh membocorkan blok mentah
        for secret_key in ("confirm", "args", "execution", "plan", "approval", "observability"):
            self.assertNotIn(secret_key, card)

    def test_get_mission_detail_existing(self):
        r = self.client.get(f"/ux/missions/{self.mission_id}")
        self.assertEqual(r.status_code, 200)
        card = r.json()
        self.assertEqual(card["mission_id"], self.mission_id)
        self.assertEqual(card["operation"], "github.create_issue")

    def test_get_mission_detail_unknown_404(self):
        # mission tidak dikenal -> 404 (fail-closed); TIDAK ada fallback
        # ke request_id / m_*.
        r = self.client.get("/ux/missions/mission-tidak-ada-xyz")
        self.assertEqual(r.status_code, 404)
