"""test_m12_007_health_readiness.py — M12-007 Readiness model (fail-closed).

Readiness `/health/ready` harus mencerminkan kondisi produksi:
  - Dev (tanpa SAM_ENV / PG) -> 200 ready (RuntimeAPI health OK).
  - Produksi (SAM_ENV=production) tetapi PG tidak siap (tanpa DSN) -> 503
    NOT READY, konsisten dgn M12-004/005 fail-closed (tanpa fallback diam-diam).
  - Produksi + PG tersedia -> 200 ready.

Catatan: test PG-ok membaca `SAM_PG_DSN` dari env (di-set saat menjalankan);
skip bila tidak tersedia (tidak hardcode password di repo).
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from sam.api.server import app


@pytest.fixture(autouse=True)
def _isolate_env():
    saved = {k: os.environ.get(k) for k in ("SAM_ENV", "SAM_PG_DSN", "SAM_ENABLE_PG")}
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_ready_dev_ok():
    """Dev (tanpa env produksi): readiness 200."""
    os.environ.pop("SAM_ENV", None)
    os.environ.pop("SAM_PG_DSN", None)
    os.environ.pop("SAM_ENABLE_PG", None)
    client = TestClient(app)
    r = client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["persistence"] == "ready"


def test_ready_production_without_pg_503():
    """Produksi tanpa DSN -> readiness 503 (fail-closed persistence)."""
    os.environ["SAM_ENV"] = "production"
    os.environ.pop("SAM_PG_DSN", None)
    os.environ.pop("SAM_ENABLE_PG", None)
    client = TestClient(app)
    r = client.get("/health/ready")
    assert r.status_code == 503
    detail = r.json()["detail"]
    assert detail["persistence"] == "production-persistence-unavailable"


def test_ready_production_down_pg_503():
    """Produksi + DSN ke PG yang mati -> 503 (fail-closed)."""
    os.environ["SAM_ENV"] = "production"
    os.environ["SAM_PG_DSN"] = "host=127.0.0.1 port=1 dbname=sam user=sam password=***"
    client = TestClient(app)
    r = client.get("/health/ready")
    assert r.status_code == 503
    detail = r.json()["detail"]
    assert detail["persistence"] == "production-persistence-unavailable"


def test_ready_production_pg_ok():
    """Produksi + PG tersedia -> 200. Skip bila SAM_PG_DSN env tidak diset."""
    dsn = os.environ.get("SAM_PG_DSN", "").strip()
    if not dsn:
        pytest.skip("SAM_PG_DSN tidak diset")
    os.environ["SAM_ENV"] = "production"
    client = TestClient(app)
    r = client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["persistence"] == "ready"
