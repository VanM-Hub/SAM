"""test_m12_009_watchdog.py — M12-009 External Watchdog (deteksi).

Menguji `sam_watchdog.check_once` & rotator log terhadap HTTP server mock
lokal (tanpa server SAM nyata / tanpa bergantung service):
  - healthy+ready  -> code 0 (OK)
  - /health 200 tp /health/ready 503 (fail-closed pg down) -> code 2 (NOT_READY)
  - /health 503 / tidak healthy -> code 3 (UNHEALTHY)
  - koneksi ditolak / server mati -> code 1 (DEAD)
  - rotator log bounded (simpan max N baris)
"""
from __future__ import annotations

import importlib.util
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

# Import sam_watchdog.py via path (tools/ di root, bukan package sam.tools).
_wd_path = Path(__file__).resolve().parent.parent.parent / "tools" / "sam_watchdog.py"
_spec = importlib.util.spec_from_file_location("sam_watchdog", _wd_path)
_wd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wd)
check_once = _wd.check_once
_LogRotator = _wd._LogRotator


class _Handler(BaseHTTPRequestHandler):
    """Handler dinamis yang dikontrol via variabel class-level per-test."""
    mode = "ok"

    def do_GET(self):
        if self.mode == "ok":
            if self.path == "/health":
                body = b'{"status":"healthy","state":"healthy"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == "/health/ready":
                body = b'{"status":"ready","state":"healthy","persistence":"ready"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()
        elif self.mode == "not_ready":
            if self.path == "/health":
                body = b'{"status":"healthy"}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:  # ready -> 503
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
        elif self.mode == "unhealthy":
            self.send_response(503)
            self.end_headers()
        else:  # dead -> server stop, koneksi ditolak (simulasi oleh test lain)
            self.send_response(500)
            self.end_headers()

    def log_message(self, *a):
        pass


@pytest.fixture()
def mock_server():
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv, f"http://127.0.0.1:{port}"
    srv.shutdown()
    srv.server_close()


def test_ok(mock_server):
    _Handler.mode = "ok"
    srv, url = mock_server
    code, detail = check_once(url)
    assert code == 0
    assert "OK" in detail


def test_not_ready_fail_closed(mock_server):
    _Handler.mode = "not_ready"
    srv, url = mock_server
    code, detail = check_once(url)
    assert code == 2
    assert "NOT_READY" in detail


def test_unhealthy(mock_server):
    _Handler.mode = "unhealthy"
    srv, url = mock_server
    code, detail = check_once(url)
    assert code == 3
    assert "UNHEALTHY" in detail


def test_dead_connection_refused():
    # Port yang hampir pasti tidak listen -> koneksi ditolak -> DEAD
    code, detail = check_once("http://127.0.0.1:1", timeout=3)
    assert code == 1
    assert "DEAD" in detail


def test_log_rotator_bounded(tmp_path):
    lp = tmp_path / "watchdog.log"
    rot = _LogRotator(lp, max_lines=5)
    for i in range(10):
        rot.append(f"line-{i}")
    lines = lp.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5
    assert lines[0] == "line-5"
    assert lines[-1] == "line-9"
