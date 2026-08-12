"""M10-002 — Secrets: External Secret → Credential Boundary → Connector.

Keputusan Van (M10-002): semua credential harus mengalir lewat

    External Secret -> Credential Boundary -> Connector

dan TIDAK PERNAH masuk: source code; mission payload; prompt; audit;
evidence; artifact; browser response; logs.

Fokus M10-002 = lapisan yang BELUM ditutup M8-005 (yang menguji boundary
internal): pengiriman secret lewat JALUR HTTP NYATA (browser response) dan
semua permukaan observasi (state/evidence/audit) yang dilihat operator/UI.

Test ini memakai jalur LIVE (TestClient terhadap app server production yang
sama dengan browser). Disaring jujur bila GITHUB_TOKEN tidak ada (skenario
approve full), skenario berperilaku deterministik untuk state/anti-leak.

Tanpa key nyata di mana pun: secret HANYA di env (di-set via SecretProvider
sama seperti runtime), dan asersi memastikan TIDAK pernah tampil di output.
"""
from __future__ import annotations

import os
import re
import unittest

import pytest
from fastapi.testclient import TestClient

from sam.api.server import app
from sam.execution_runtime.credential_boundary import SecretScrubber


TOKEN_ENV = "GITHUB_TOKEN"
HAVE_TOKEN = bool(os.getenv(TOKEN_ENV))


def _all_endpoints_observable() -> list:
    """Endpoint observability yang dilihat operator/UI (bukan GitHub)."""
    return ["/ux/state", "/ux/evidence", "/ux/audit", "/ui"]


class TestSecretFlowHTTP(unittest.TestCase):
    """M10-002 — secret melalui jalur HTTP tanpa bocor."""

    def test_resolve_scope_never_returns_raw(self):
        """Resolver credential hanya menampilkan masked (len), TIDAK pernah raw."""
        from sam.execution_runtime.credential_boundary import (
            CredentialBoundary, CredentialRequirement,
        )
        b = CredentialBoundary()
        req = CredentialRequirement(provider_id="gh", env_var="_M10TMP_TOKEN",
                                    min_length=8)
        # Simulasikan env hadir (raw hanya dalam scope) — pakai env var SEMENTARA
        # sendiri, JANGAN menimpa GITHUB_TOKEN nyata (biar tidak menghapus token
        # proses untuk test lain di suite).
        import os as _os
        _os.environ[req.env_var] = "ghp_" + ("x" * 40)
        try:
            res = b.resolve(req)
        finally:
            _os.environ.pop(req.env_var, None)
        assert res.available is True
        assert "ghp_xxxxxxxx" not in str(res.masked), "masked tidak boleh expose suffix"
        assert "[len=" in res.masked, "masked hanya menampilkan panjang, tanpa isi"
        # as_dict (yang keluar ke audit/timeline) TIDAK mengandung raw.
        d = res.as_dict()
        blob = str(d).lower()
        assert "ghp_" not in blob, "as_dict tidak boleh memuat raw secret"

    def test_boundary_audit_never_contains_raw(self):
        """Audit boundary berisi masked (len), TIDAK pernah raw token."""
        from sam.execution_runtime.credential_boundary import (
            CredentialBoundary, CredentialRequirement,
        )
        import os as _os
        b = CredentialBoundary()
        raw = "ghp_ABCDEFGH_" + "z" * 30
        env_name = "_M10TMP_GHTOKEN"
        _os.environ[env_name] = raw
        try:
            b.resolve(CredentialRequirement(provider_id="gh", env_var=env_name,
                                            min_length=8))
        finally:
            _os.environ.pop(env_name, None)
        aud = b.audit_log()
        blob = "".join(str(a) for a in aud)
        assert raw not in blob, "audit boundary memuat raw secret"
        assert "ghp_" not in blob.lower(), "audit boundary memuat token GitHub"
        assert "[len=" in blob, "audit harus menyimpan masked (len) sbg bukti hadir"

    def test_ui_html_has_no_hardcoded_secret(self):
        """UI HTML (served ke browser) TIDAK mengandung secret/placeholder token."""
        c = TestClient(app)
        ui = c.get("/ui").text
        # Tidak ada key literal / token sk- / ghp_ — apapun bentuknya.
        for pat in (r"ghp_[A-Za-z0-9]{10,}", r"sk-[A-Za-z0-9]{10,}",
                    r"nvapi-[A-Za-z0-9]{30,}", r"AIza[0-9A-Za-z_-]{30,}"):
            assert not re.search(pat, ui), f"UI HTML bocor pola {pat}"
        assert "GITHUB_TOKEN=" not in ui.replace(" ", "")

    @pytest.mark.skipif(not HAVE_TOKEN, reason="butuh token utk jalur approve nyata")
    def test_approve_flow_response_never_leaks_token(self):
        """Setelah approve (raw nyata di scope), response /ux/decide + THEN
        /ux/state|evidence|audit TIDAK pernah memuat token GitHub."""
        from sam.runtime_service.secrets.secret_provider import SecretProvider
        tok = os.environ[TOKEN_ENV]
        c = TestClient(app)
        c.post("/ux/submit", json={"text": "Buat github issue utk m10-002 secret flow"})
        resp = c.post("/ux/decide", json={"intent": "approve", "approver": "user"})
        assert resp.status_code == 200
        # seluruh blok response + state + evidence + audit
        for ep in [_all_endpoints_observable()[-1]] + _all_endpoints_observable()[:-1]:
            if ep == "/ui":
                body = c.get(ep).text
            else:
                body = str(c.get(ep).json())
            assert tok not in body, f"{ep} membocorkan token GitHub mentah"
            assert "ghp_" not in body.lower(), f"{ep} membocorkan pola ghp_"

    def test_prompt_payload_never_contains_secret(self):
        """Mission payload / prompt yang dikirim ke LLM TIDAK membawa secret."""
        # MissionUXService → plan disusun dari input user (teks) + understanding,
        # TIDAK menyelipkan credential. Pastikan payload submit+response TIDAK
        # mengandung modul credential.
        c = TestClient(app)
        r = c.post("/ux/submit", json={"text": "Buat github issue plain"})
        s = r.json()
        blob = str(s).lower()
        for marker in ("ghp_", "nvapi-", "bearer "):
            assert marker not in blob, f"mission payload bocor {marker}"


if __name__ == "__main__":
    unittest.main(verbosity=2)
