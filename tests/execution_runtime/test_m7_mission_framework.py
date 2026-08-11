"""M7 — tests. Real Operational Work framework.

Menguji (tanpa API key nyata, deterministik):
1. MissionBuilder merangkai langkah nyata berurutan + audit.
2. Gate credential jujur: tanpa token -> stage BLOCKED (NO SIDE EFFECT),
   bukan mock/pass palsu.
3. Mission menghasilkan artifact tertulis nyata + experience persist + audit.
4. M7-003 System Ops: observasi nyata Process + SQLite, verifikasi snapshot.
5. Repeatable: menjalankan mission dua kali deterministik (persist tetap).
"""
from __future__ import annotations

import os
import tempfile

import pytest

from sam.execution_runtime.m7_mission_framework import (
    CredentialGate,
    Mission,
    MissionStep,
    MISSION_7_001,
    MISSION_7_002,
    MISSION_7_003,
    PersistedExperience,
    m7_001_build,
    m7_002_build,
    m7_003_build,
)
from sam.execution_runtime.real_harness import AuditTrail


def _tmp_out():
    d = tempfile.mkdtemp(prefix="m7test_")
    return d


# --- 1. builder chain + audit ---
def test_m7_step_chain_runs_in_order():
    audit = AuditTrail()
    mission = Mission("M7-000", "Chain Test", audit)
    mission.artifact_path = os.path.join(_tmp_out(), "report.txt")
    order = []

    mission.add(MissionStep("a", runner=lambda: order.append("a") or {"ok": True}))
    mission.add(MissionStep("b", runner=lambda: order.append("b") or {"ok": True}))
    mission.add(MissionStep("c", runner=lambda: order.append("c") or {"ok": True}))

    result = mission.run()
    assert order == ["a", "b", "c"]
    assert result["ok"] is True
    assert any(e.action == "m7.step" for e in audit.entries)


# --- 2. gate credential jujur (tanpa token -> BLOCKED, bukan mock) ---
def test_m7_credential_gate_blocks_without_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    gate = CredentialGate("GITHUB_TOKEN", "kredensial GitHub")
    assert gate.passed() is False

    audit = AuditTrail()
    mission = Mission("M7-X", "Gate Test", audit)
    mission.artifact_path = os.path.join(_tmp_out(), "report.txt")
    mission.add(MissionStep("gate", gate=gate, runner=lambda: {"ok": True, "detail": "tidak boleh dipanggil"}))
    result = mission.run()
    # stage gate ter-blocked, tidak pernah call runner
    assert result["ok"] is False
    assert result["timeline"][0]["blocked"] is True
    assert result["timeline"][0]["blocked_by"] == "GITHUB_TOKEN"
    assert "tidak boleh dipanggil" not in str(result["timeline"])


def test_m7_credential_gate_passes_with_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token-untuk-test")
    gate = CredentialGate("GITHUB_TOKEN", "kredensial GitHub")
    assert gate.passed() is True
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


# --- 3. artifact + experience + audit ---
def test_m7_mission_produces_artifact_and_experience():
    out = _tmp_out()
    exp_path = os.path.join(out, "exp.json")
    audit = AuditTrail()
    mission = Mission("M7-Y", "Artifact Test", audit)
    mission.artifact_path = os.path.join(out, "report.txt")
    mission.add(MissionStep("observe", runner=lambda: {"ok": True, "detail": "x"}))

    exp = PersistedExperience(exp_path, audit)
    result = mission.run(exp_repo=exp)

    assert os.path.isfile(result["artifact_path"])
    assert os.path.getsize(result["artifact_path"]) > 0
    assert result["experience_id"]  # experience di-store
    assert exp.count() == 1
    assert any(e.action == "m7.artifact" for e in audit.entries)
    assert any(e.action == "m7.learn.store" for e in audit.entries)


# --- 4. M7-003 System Ops nyata ---
def test_m7_003_system_ops_real():
    out = _tmp_out()
    audit = AuditTrail()
    mission = m7_003_build(audit, artifact_dir=out)
    result = mission.run()

    assert result["mission_id"] == MISSION_7_003
    assert result["ok"] is True
    stages = [t["stage"] for t in result["timeline"]]
    assert "observe" in stages and "verify" in stages
    # observasi hostname + db nyata
    observe = next(t for t in result["timeline"] if t["stage"] == "observe")
    assert observe["detail"].startswith("host=")


# --- 5. repeatable ---
def test_m7_repeatable_deterministic():
    out = _tmp_out()
    audit = AuditTrail()
    mission = m7_003_build(audit, artifact_dir=out)
    r1 = mission.run()
    r2 = mission.run()
    # kedua run sukses (repeatable, bukan one-shot)
    assert r1["ok"] is True
    assert r2["ok"] is True


# --- 6. M7-002 GitHub gate jujur ---
def test_m7_002_github_gate_honest(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    audit = AuditTrail()
    mission = m7_002_build(audit)
    result = mission.run()
    assert result["mission_id"] == MISSION_7_002
    gate_step = next(t for t in result["timeline"] if t["stage"] == "gate")
    assert gate_step["blocked"] is True
    assert result["ok"] is False  # tanpa token -> tidak diklaim sukses
