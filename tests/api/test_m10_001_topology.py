"""M10-001 — Deployment Topology Boundary (Defense).

Menetapkan & menjaganya dengan test negatif: UI/API layer TIDAK BOLEH memiliki
jalur langsung ke connector / executor / provider / execution runtime.

Topologi canonical (M10-001):
    User Browser
        |  (HTTP fetch /ux)
        v
    UI / API (thin client + REST route adapter)
        |  (hanya memanggil Application Service)
        v
    Application Layer (MissionUXService / ApprovalGate)
        |  (canonical orchestration + approval gate)
        v
    Canonical Execution Runtime (RealExecutionHarness / m8_mission_framework)
        |  (capability + connector execution)
        v
    External Connectors (GitHub / HTTP / SMTP / DB / Process / Browser ...)
        |  (real external effect)
        v
    External World

DILARANG ada:
    UI -> connector
    UI -> executor
    UI -> provider
    route handler -> connector / executor / provider / execution runtime

Test ini memindai kode (source text) + memverifikasi runtime composition-root.
Composition/Dependency Injection (passing instance ke Application Service) adalah
SATU-SATUNYA cara yang sah — dilakukan di wiring.py (composition root), BUKAN di
route handler, BUKAN di UI.
"""
from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sam.api.server import app


REPO_ROOT = Path(__file__).resolve().parents[2]  # tests/api/ -> SAM root
API_DIR = REPO_ROOT / "src" / "sam" / "api"
STATIC_DIR = API_DIR / "static"
ROUTES_DIR = API_DIR / "routes"

# Modul batin yang TIDAK boleh diimpot langsung oleh route handler / UI.
FORBIDDEN_MODULES = (
    "execution_runtime",  # termasuk RealExecutionHarness, m8_mission_framework
    "providers",          # termasuk ProviderExecutor
    "universal_",         # legacy
    "operational_workspace",  # workspace legacy
)

# Pola fetch eksternal / akses langsung yang dilarang di UI.
FORBIDDEN_UI_PATTERNS = (
    r"fetch\(\s*['\"]https?://",
    r"axios\.(get|post|put|patch|delete)\(\s*['\"]https?://",
    r"xmlhttprequest",
    r"api\.github\.com",
    r"api\.nvidia",
    r"apps\.nvidia",
    r"api\.openai",
    r"WebSocket\(",
)


def _iter_files(directory: Path, suffix: str):
    for p in directory.rglob("*.py") if suffix == ".py" else directory.glob("*"):
        if p.is_file() and p.suffix == suffix:
            yield p


class TestDeploymentTopology(unittest.TestCase):
    """M10-001 — menegakkan topologi canonical via pemindaian kode."""

    def test_browser_is_thin_client_to_ux(self):
        """UI TIDAK boleh akses eksternal / provider / executor / connector."""
        if not STATIC_DIR.exists():
            self.skipTest("tidak ada static dir")
        for f in STATIC_DIR.glob("*.html"):
            text = f.read_text(encoding="utf-8", errors="replace")
            for pat in FORBIDDEN_UI_PATTERNS:
                assert not re.search(pat, text, flags=re.I), (
                    f"{f.name}: UI tidak boleh akses langsung: {pat}"
                )
            # fetch/URL eksternal dilarang; semua interaksi ke /ux/* (server).
            ext = re.findall(r"['\"](https?://[^'\"]+)['\"]", text)
            for u in ext:
                assert u.startswith("http://127.0.0.1") or u.startswith(
                    "http://localhost"
                ), f"{f.name}: URL non-lokal di UI: {u}"

    def test_route_handlers_never_import_runtime_core(self):
        """Route handler TIDAK mengimpor connector/executor/provider/runtime."""
        if not ROUTES_DIR.exists():
            self.skipTest("tidak ada routes dir")
        for f in sorted(ROUTES_DIR.glob("*.py")):
            text = f.read_text(encoding="utf-8", errors="replace")
            for mod in FORBIDDEN_MODULES:
                # import langsung ke modul batin (langsung provider/executor).
                assert not re.search(
                    rf"^from sam\.{mod}\.|^import sam\.{mod}\.",
                    text,
                    flags=re.M,
                ), f"{f.name}: route handler mengimpor sam.{mod} langsung"
            # Route handler hanya boleh import application layer / model / util.
            forbidden = re.findall(
                r"^from sam\.(providers|execution_runtime|universal_\w+)\b",
                text,
                flags=re.M,
            )
            assert not forbidden, f"{f.name}: import batin terlarang: {forbidden}"

    def test_runtime_objects_only_in_composition_root(self):
        """Executor/provider/runtime hanya di-wire di wiring.py, bukan di route."""
        if not ROUTES_DIR.exists():
            self.skipTest("tidak ada routes dir")
        for f in sorted(ROUTES_DIR.glob("*.py")):
            text = f.read_text(encoding="utf-8", errors="replace")
            # Route handler TIDAK boleh meng-instansiasi executor/provider.
            for pat in (
                r"RealExecutionHarness\(",
                r"ExecutionRuntime\(",
                r"ProviderExecutor\(",
                r"m8_mission_framework\.",
                r"RealProviderExecutor\(",
            ):
                assert not re.search(pat, text), (
                    f"{f.name}: instansiasi runtime di route handler: {pat}"
                )

    def test_ux_route_bridges_application_layer_only(self):
        """Route /ux hanya adapter ke Application Service (bukan runtime)."""
        ux = ROUTES_DIR / "ux.py"
        text = ux.read_text(encoding="utf-8")
        assert "from sam.application.ux.service import MissionUXService" in text, (
            "route /ux harus bergantung pada MissionUXService"
        )
        for mod in FORBIDDEN_MODULES:
            assert not re.search(rf"sam\.{mod}\b", text), (
                f"route /ux mengimpor sam.{mod}"
            )

    def test_server_serves_ui_not_embedded_executor(self):
        """GET /ui mengembalikan HTML; /ux bekerja; tanpa import runtime di server."""
        server_py = API_DIR / "server.py"
        text = server_py.read_text(encoding="utf-8")
        # server host memakai composition via wiring; TIDAK instansiasi executor.
        for pat in (r"RealExecutionHarness\(", r"ExecutionRuntime\(", r"ProviderExecutor\("):
            assert not re.search(pat, text), f"server.py instansiasi runtime: {pat}"
        c = TestClient(app)
        r = c.get("/ui")
        assert r.status_code == 200
        # UI service di-serve dari server (bukan teks kosong / error page).
        assert "mission workspace" in r.text.lower()


if __name__ == "__main__":
    unittest.main(verbosity=2)
