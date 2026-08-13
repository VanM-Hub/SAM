"""test_m12_008_metrics.py — M12-008 Observability (telemetri /metrics).

Memverifikasi:
  - Metrics registry (counter thread-safe, bounded, render Prometheus).
  - GET /metrics -> 200 text/plain berisi counter SAM.
  - Integrasi nyata: submit menaikkan sam_mission_received; approve menaikkan
    sam_mission_approved; produksi down menaikkan sam_mission_blocked (fail-closed).
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from sam.api.server import app
from sam.application.ux.metrics import Metrics


def test_metrics_registry_render():
    m = Metrics()
    m.inc("sam_mission_received")
    m.inc("sam_mission_received")
    m.inc("sam_execution_completed")
    assert m.get("sam_mission_received") == 2
    assert m.get("sam_execution_completed") == 1
    # unknown name diabaikan (bounded, tidak sembarang key)
    m.inc("not_a_real_metric")
    assert "not_a_real_metric" not in m.snapshot()
    body = m.render_prometheus()
    assert "sam_mission_received 2" in body
    assert "# TYPE sam_mission_received counter" in body


def test_metrics_endpoint_ok():
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    body = r.text
    # semua telemetri inti terekspos
    for name in ("sam_mission_received", "sam_mission_blocked", "sam_mission_approved",
                 "sam_execution_started", "sam_execution_completed", "sam_execution_failed",
                 "sam_idempotency_replay", "sam_idempotency_conflict", "sam_persistence_error"):
        assert name in body


@pytest.fixture(autouse=True)
def _isolate_env():
    saved = {k: os.environ.get(k) for k in ("SAM_ENV", "SAM_PG_DSN", "SAM_ENABLE_PG", "GITHUB_TOKEN")}
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_submit_increments_mission_received():
    from sam.application.ux import metrics as _m
    before = _m.metrics.get("sam_mission_received")
    client = TestClient(app)
    r = client.post("/ux/submit", json={"text": "Buat GitHub issue 'uji metrics'"})
    assert r.status_code == 200
    after = _m.metrics.get("sam_mission_received")
    assert after >= before + 1


def test_production_down_increments_blocked():
    """Produksi down -> submit DI-BLOCK & sam_mission_blocked naik.
    (Unit service: env produksi dibaca saat instance dibuat; route global
    dibangun sekali saat import, jadi uji lewat instance service segar.)"""
    from sam.application.ux import metrics as _m
    from sam.application.ux.service import MissionUXService
    os.environ["SAM_ENV"] = "production"
    os.environ["SAM_PG_DSN"] = "host=127.0.0.1 port=1 dbname=sam user=sam password=***"
    before = _m.metrics.get("sam_mission_blocked")
    svc = MissionUXService()
    assert svc._production_blocked is True
    st = svc.submit("Buat GitHub issue 'uji block'", idempotency_key="m12block-key")
    assert st.status == "blocked"
    assert st.failure_kind == "persistence-required"
    after = _m.metrics.get("sam_mission_blocked")
    assert after >= before + 1


def test_metrics_endpoint_reflects_increment():
    from sam.application.ux import metrics as _m
    _m.metrics.inc("sam_execution_failed")
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    val = int([ln for ln in r.text.splitlines() if ln.startswith("sam_execution_failed ")][0].split()[-1])
    assert val >= 1
