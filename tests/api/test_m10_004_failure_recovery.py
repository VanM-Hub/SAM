"""M10-004 — Failure & Recovery: bukan hanya happy path.

Syarat Van: buktikan \u201ctimeout / credential failure / external 500 / partial
operation / process crash / restart / duplicate request\u201d — dan prinsip
\u201cfailure \u2260 success=False saja\u201d: harus ada ACTUAL STATE + RECOVERY SEMANTICS.

Di lapisan UX (jalur HTTP yang dilihat operator), kita membuktikan:
  - credential hilang   -> status BLOCKED (bukan sekedar ok=False; ada
                           failure_kind, failure_message, dan NO side effect).
  - token invalid       -> FAILED (bukan sekedar False; ada reason).
  - user menolak        -> REJECTED (semantics berbeda dari FAILED).
  - duplicate request   -> state/submission tetap konsisten, approval gate
                           yang sama, tidak ada eksekusi ganda tanpa approval.
  - restart (session)   -> tidak menghilangkan truth: state terminal tetap
                           terbaca; submit baru menggantikan sesi lama dgn rapi.

Pendekatan: deterministik, tanpa membutuhkan server eksternal. Gunakan
CredentialBoundary untuk simulasi credential hilang, dan /ux untuk state.
"""
from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from sam.api.server import app
from sam.execution_runtime.credential_boundary import (
    BoundaryStatus,
    CredentialBoundary,
    CredentialRequirement,
)
from sam.runtime_service.secrets.secret_provider import SecretProvider


class _EmptyProvider(SecretProvider):
    """SecretProvider yang selalu mengembalikan kosong (simulasi env hilang)."""

    def get(self, key: str):
        return None


class TestFailureClassification(unittest.TestCase):
    """M10-004 — setiap kegagalan punya status aktual (bukan bool False saja)."""

    def test_missing_credential_is_blocked_not_fake(self):
        """Credential hilang -> BLOCKED; classified, bukan hanya ok=False."""
        b = CredentialBoundary(provider=_EmptyProvider())
        req = CredentialRequirement(provider_id="gh", env_var="GITHUB_TOKEN",
                                    min_length=8)
        res = b.resolve(req)
        assert res.status == BoundaryStatus.MISSING
        assert res.action == "blocked"
        assert res.available is False
        d = res.as_dict()
        assert d["status"] == "missing"
        assert d["action"] == "blocked"
        assert "BLOCKED" in d["reason"], "reason harus jelaskan state (BLOCKED)"

    def test_invalid_credential_is_failed(self):
        """Credential terlalu pendek / placeholder -> FAILED (bukan False)."""
        class _Short(SecretProvider):
            def get(self, key):
                return "short"
        b = CredentialBoundary(provider=_Short())
        req = CredentialRequirement(provider_id="gh", env_var="GITHUB_TOKEN",
                                    min_length=8)
        res = b.resolve(req)
        assert res.status == BoundaryStatus.INVALID
        assert res.action == "failed"
        d = res.as_dict()
        assert d["action"] == "failed"
        assert "FAILED" in d["reason"]

    def test_boundary_execute_blocked_has_zero_side_effect(self):
        """BLOCKED: function TIDAK pernah dipanggil (zero side effect), dan
        hasil memuat state aktual (blocked=True, status) — bukan sekadar False."""
        called = []
        def fn():
            called.append(1)
            return {"ok": True}
        b = CredentialBoundary(provider=_EmptyProvider())
        from sam.execution_runtime.credential_boundary import BoundaryAwareExecution
        out = BoundaryAwareExecution(b).execute(
            CredentialRequirement(provider_id="gh", env_var="GITHUB_TOKEN",
                                  min_length=8),
            fn,
        )
        assert not called, "BLOCKED bukan hanya bool False: executor TIDAK dipanggil"
        assert out["blocked"] is True
        assert out["status"] == "missing"
        assert out["action"] == "blocked"
        assert out["ok"] is False
        assert "NO SIDE EFFECT" in out["detail"]

    def test_rejected_is_separate_semantics(self):
        """REJECTED (user tolak) harus beda dari FAILED/BLOCKED."""
        c = TestClient(app)
        s0 = c.post("/ux/submit", json={"text": "Buat github issue"}).json()
        mid = s0["observability"]["mission_id"]
        r = c.post("/ux/decide", json={"intent": "reject", "mission_id": mid, "approver": "user"})
        s = r.json()
        assert s["execution"]["status"] == "rejected"
        assert s["execution"]["failure_kind"] == "rejected"
        assert s["approval"]["status"] == "rejected"
        # Tidak ada evidence / artifact mission result (0 mutation).
        assert not s["evidence"]
        # Observability mencatat state actim.
        assert s["observability"]["status"] == "rejected"
        assert s["observability"]["execution_id"] == ""


class TestDuplicateAndRestart(unittest.TestCase):
    """M10-004 — duplicate request & restart/session consistency."""

    def test_duplicate_submit_replaces_cleanly(self):
        """Submit berulang menggantikan sesi lama dgn rapi: state baru
        waiting_approval, status lama tidak membocorkan ke sesi baru."""
        c = TestClient(app)
        r1 = c.post("/ux/submit", json={"text": "Buat github issue pertama"})
        id1 = r1.json()["request_id"]
        assert r1.json()["approval"]["status"] == "waiting_approval"

        r2 = c.post("/ux/submit", json={"text": "Buat github issue kedua"})
        id2 = r2.json()["request_id"]
        assert id2 != id1, "submit baru harus request_id baru"
        assert r2.json()["approval"]["status"] == "waiting_approval"
        # state terbaru = sesi kedua, bukan campuran.
        st = c.get("/ux/state").json()
        assert st["request_id"] == id2

    def test_no_duplicate_execution_without_approval(self):
        """Satu operasi TIDAK dieksekusi ganda tanpa approval: setelah submit,
        tidak ada eksekusi sampai approve; evidence kosong."""
        c = TestClient(app)
        c.post("/ux/submit", json={"text": "Buat github issue (tanpa approve)"})
        st = c.get("/ux/state").json()
        assert st["execution"]["status"] == "waiting_approval"
        assert not st["evidence"], "tanpa approval tidak boleh ada evidence/eksekusi"

    def test_restart_keeps_terminal_truth_readable(self):
        """Simulasi 'restart' (fresh TestClient/session ke singleton yang sama):
        state terminal yang sudah tercatat tetap terbaca dari server (bukan
        hilang), dan submit baru memberi sesi bersih."""
        c = TestClient(app)
        s0 = c.post("/ux/submit", json={"text": "Buat github issue (reject utk restart)"}).json()
        mid = s0["observability"]["mission_id"]
        c.post("/ux/decide", json={"intent": "reject", "mission_id": mid, "approver": "user"})
        # fresh client (seolah server dinyalakan ulang tapi store-nya in-memory)
        c2 = TestClient(app)
        st = c2.get("/ux/state").json()
        assert st["execution"]["status"] == "rejected", (
            "state terminal harus tetap terbaca pasca-restart/share store"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
