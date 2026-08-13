"""test_m12_016_24h_test.py — M12-016 12-Hour Mission Test harness.

Kontrak M12-016: Operator tak sentuh SAM 12 jam + controlled failure.
  NO LOST TRUTH / NO DUPLICATE / NO UNOBSERVED FAILURE /
  NO UNSAFE CONTINUATION / NO MANUAL RECOVERY.

Cakupan unit (mock psql/urllib agar deterministik; TIDAK butuh docker):
  - cmd_begin : baseline tersimpan ke state-dir dgn counts + idempotency.
  - cmd_verify PASS bila: truth konsisten, idem konsisten, ready 200,
    tidak ada execution running, periode >= 12 jam.
  - cmd_verify FAIL bila ada: lost truth (count berkurang), duplicate
    (request_id berubah), unobserved failure (ready != 200), unsafe
    continuation (execution running), atau periode < 12 jam (jujur).
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).resolve().parents[2] / "tools" / "m12_016_24h_test.py"
    spec = importlib.util.spec_from_file_location("m12_016_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def m():
    return _load()


def _write_baseline(state_dir, m, started_iso, counts, idem):
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    (Path(state_dir) / "baseline.json").write_text(
        json.dumps({
            "started_at": started_iso,
            "table_counts": counts,
            "idempotency": idem,
            "readiness": {"code": 200, "body": "ready"},
            "service": "RUNNING",
            "unsafe_running_executions": 0,
        }), encoding="utf-8")


def test_begin_records_baseline(m, tmp_path, monkeypatch):
    def fake_psql(db, q):
        if "count" in q:
            return "5"
        return 'k1|{"request_id":"req-A"}'
    monkeypatch.setattr(m, "_psql", fake_psql)
    out = tmp_path / "st"
    rc = m.cmd_begin(type("A", (), {"state_dir": str(out)})())
    assert rc == 0
    bl = json.loads((Path(out) / "baseline.json").read_text(encoding="utf-8"))
    assert bl["table_counts"]["mission_store"] == 5
    assert bl["idempotency"]["k1"] == "req-A"


def test_verify_pass_12h_consistent(m, tmp_path, monkeypatch):
    started = "2000-01-01T00:00:00+00:00"  # jauh >12 jam lalu
    counts = {"mission_store": 1, "sam_audit": 0, "sam_idempotency": 1}
    _write_baseline(str(tmp_path), m, started, counts, {"k1": "req-A"})
    # kini state sama dgn baseline
    monkeypatch.setattr(m, "_table_counts", lambda: dict(counts))
    monkeypatch.setattr(m, "_idempotency_snapshot", lambda: {"k1": "req-A"})
    monkeypatch.setattr(m, "_readiness", lambda: {"code": 200, "body": "ready"})
    monkeypatch.setattr(m, "_unsafe_running_executions", lambda: 0)
    rc = m.cmd_verify(type("A", (), {"state_dir": str(tmp_path)})())
    assert rc == 0  # PASS (semua konsisten + 12h)


def test_verify_fail_lost_truth(m, tmp_path, monkeypatch):
    started = "2000-01-01T00:00:00+00:00"
    counts = {"mission_store": 3, "sam_audit": 0, "sam_idempotency": 1}
    _write_baseline(str(tmp_path), m, started, counts, {"k1": "req-A"})
    # mission_store BERKURANG (lost truth)
    monkeypatch.setattr(m, "_table_counts",
                        lambda: {"mission_store": 1, "sam_audit": 0, "sam_idempotency": 1})
    monkeypatch.setattr(m, "_idempotency_snapshot", lambda: {"k1": "req-A"})
    monkeypatch.setattr(m, "_readiness", lambda: {"code": 200, "body": "ready"})
    monkeypatch.setattr(m, "_unsafe_running_executions", lambda: 0)
    rc = m.cmd_verify(type("A", (), {"state_dir": str(tmp_path)})())
    assert rc == 1  # FAIL (lost truth)


def test_verify_fail_duplicate(m, tmp_path, monkeypatch):
    started = "2000-01-01T00:00:00+00:00"
    counts = {"mission_store": 1, "sam_audit": 0, "sam_idempotency": 1}
    _write_baseline(str(tmp_path), m, started, counts, {"k1": "req-A"})
    monkeypatch.setattr(m, "_table_counts", lambda: dict(counts))
    # request_id BERUBAH untuk key yg sama -> duplicated/inconsistent
    monkeypatch.setattr(m, "_idempotency_snapshot", lambda: {"k1": "req-B"})
    monkeypatch.setattr(m, "_readiness", lambda: {"code": 200, "body": "ready"})
    monkeypatch.setattr(m, "_unsafe_running_executions", lambda: 0)
    rc = m.cmd_verify(type("A", (), {"state_dir": str(tmp_path)})())
    assert rc == 1  # FAIL (duplicate)


def test_verify_fail_unobserved_failure(m, tmp_path, monkeypatch):
    started = "2000-01-01T00:00:00+00:00"
    counts = {"mission_store": 1, "sam_audit": 0, "sam_idempotency": 1}
    _write_baseline(str(tmp_path), m, started, counts, {"k1": "req-A"})
    monkeypatch.setattr(m, "_table_counts", lambda: dict(counts))
    monkeypatch.setattr(m, "_idempotency_snapshot", lambda: {"k1": "req-A"})
    # /health/ready tidak 200 -> unobserved failure / unsafe (fail-closed off?)
    monkeypatch.setattr(m, "_readiness", lambda: {"code": 503, "body": ""})
    monkeypatch.setattr(m, "_unsafe_running_executions", lambda: 0)
    rc = m.cmd_verify(type("A", (), {"state_dir": str(tmp_path)})())
    assert rc == 1  # FAIL


def test_verify_fail_period_not_12h(m, tmp_path, monkeypatch):
    # baseline dibuat 1 jam yg lalu -> elapsed < 12 jam -> PERIOD_12H FAIL
    from datetime import datetime, timedelta, timezone
    started = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    counts = {"mission_store": 1, "sam_audit": 0, "sam_idempotency": 1}
    _write_baseline(str(tmp_path), m, started, counts, {"k1": "req-A"})
    monkeypatch.setattr(m, "_table_counts", lambda: dict(counts))
    monkeypatch.setattr(m, "_idempotency_snapshot", lambda: {"k1": "req-A"})
    monkeypatch.setattr(m, "_readiness", lambda: {"code": 200, "body": "ready"})
    monkeypatch.setattr(m, "_unsafe_running_executions", lambda: 0)
    # elapsed ~1 jam < 12 -> FAIL (jujur: belum lewat periode 12 jam)
    rc = m.cmd_verify(type("A", (), {"state_dir": str(tmp_path)})())
    assert rc == 1  # belum lolos periode 12 jam
