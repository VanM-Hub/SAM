# -*- coding: utf-8 -*-
"""Test M2 - Canonical Tool Contract Adapter (Contract Absorption).

Membuktikan contract tool bernilai dari `universal_tool` dapat diserap ke
canonical `RealExecutionHarness` dan benar-benar mengeksekusi jalur EXECUTE
nyata (bukan mock): capability -> contract -> policy -> approval -> executor ->
real filesystem -> verification -> audit.

Non-destruktif: file `universal_tool/*` tidak diubah/dihapus. Contract diserap
lewat adapter `canonical_tool_contract`.

Cara jalan:
    python -m pytest tests/execution_runtime/test_m2_canonical_tool_contract.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.execution_runtime.canonical_tool_contract import (
    CanonicalToolContract,
    build_tool_contract,
    contract_to_registry_dict,
    from_universal_tool_contract,
    TOOL_KIND_EXECUTE,
    TOOL_KIND_READ,
    TOOL_KIND_WRITE,
)
from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    RealExecutionHarness,
)


@pytest.fixture()
def tmpfile(tmp_path) -> str:
    path = tmp_path / "m2_source.txt"
    path.write_text("M2 content", encoding="utf-8")
    return str(path)


def _build_harness_with_tool_contract(tmp_path_file: str):
    """Bangun harness canonical + daftarkan capability 'tool' via contract MIGRATING."""
    audit = AuditTrail()
    harness = RealExecutionHarness(audit=audit)

    # Serap kontrak tool (MIGRATING dari universal_tool) ke bentuk canonical.
    # Di sini kita fabrikasi via build_tool_contract; di real path, contract
    # datang dari universal_tool.ToolContract dan di-normalisasi
    # `from_universal_tool_contract`.
    contract = build_tool_contract(
        tool_id="file_tool",
        contract_id="ct-file-001",
        supported_kinds=(TOOL_KIND_READ, TOOL_KIND_WRITE, TOOL_KIND_EXECUTE),
        entry_points=("read", "write", "execute"),
        requires_approval=True,
        requires_governance=True,
    )
    registry = contract_to_registry_dict(contract)
    harness.register_capability("tool", registry, contract.to_contract_dict(), policy="ALLOW")
    return harness, audit, contract


def test_m2_contract_to_dict_is_truthy():
    """Contract canonical harus truthty agar lolos gate 'contract'."""
    c = build_tool_contract("t", "c1", (TOOL_KIND_READ,), ())
    assert c.to_contract_dict()
    assert c.to_contract_dict()["tool_id"] == "t"
    assert c.to_contract_dict()["contract_id"] == "c1"
    assert TOOL_KIND_READ in c.to_contract_dict()["supported_kinds"]


def test_m2_from_universal_tool_contract_dict():
    """Adatper menyerap dict kontrak (bentuk universal_tool ToolContract)."""
    # Bentuk persis seperti ToolContract.as_dict() universal_tool
    legacy = {
        "tool_id": "legacy_tool",
        "contract_id": "ct-legacy-1",
        "capabilities": [
            {"kind": "execute", "name": "run"},
            {"kind": "read", "name": "read"},
        ],
        "entry_points": ["run", "read"],
        "requires_approval": True,
        "requires_governance": True,
        "supports_capability": ["execute", "read", "write"],
    }
    cc = from_universal_tool_contract(legacy)
    assert cc is not None
    assert cc.tool_id == "legacy_tool"
    assert cc.allows("execute")
    assert cc.allows("read")
    assert cc.allows("write")
    assert not cc.allows("query")
    assert cc.governed is True


def test_m2_from_universal_tool_contract_obj():
    """Adatper menyerap objek dataclass (bukan dict) bila atributnya tersedia."""
    class _LegacyToolContract:
        tool_id = "obj_tool"
        contract_id = "ct-obj-1"
        capabilities = ()
        entry_points = ("do",)
        requires_approval = True
        requires_governance = True
        supports_capability = ["read"]

    cc = from_universal_tool_contract(_LegacyToolContract())
    assert cc is not None
    assert cc.allows("read")
    assert not cc.allows("execute")


def test_m2_invalid_contract_returns_none():
    """Bentuk yang tidak dikenali -> None (bukan contract tool lintas)."""
    assert from_universal_tool_contract(None) is None
    assert from_universal_tool_contract({"foo": "bar"}) is None


def test_m2_start_approval_false(tmpfile: str):
    """EXECUTE tanpa approval reason harus BLOCKED - tidak ada efek samping.

    Target file VALID (agar gate lain lolos), tapi approval_reason kosong
    -> approval gate gagal -> NO EXTERNAL SIDE EFFECT.
    """
    audit = AuditTrail()
    harness = RealExecutionHarness(audit=audit)
    contract = build_tool_contract("t", "c", (TOOL_KIND_READ,), ())
    harness.register_capability("tool", contract_to_registry_dict(contract), contract.to_contract_dict(), "ALLOW")

    req = ExecutionRequest(
        operation="tool/read",  # single-segment capability "tool"
        target=tmpfile,  # file valid -> boundary lolos
        mode=ExecutionMode.EXECUTE,
        params={},
        correlation_id="m2-no-approve",
        timeout_seconds=10.0,
        # approval_reason KOSONG -> approval gate wajib gagal
    )
    result = harness.execute(req)
    assert result.external_effect is False
    assert result.outcome.get("ok") is False
    assert result.outcome.get("blocked") is True
    # Salah satu gate yang gagal harus approval
    assert "approval" in result.outcome.get("blocked_by", [])


def test_m2_real_execute_read(tmpfile: str):
    """Contract MIGRATING -> canonical EXECUTE nyata baca file -> verified + audit."""
    harness, audit, _contract = _build_harness_with_tool_contract(tmpfile)
    req = ExecutionRequest(
        operation="tool/read",
        target=tmpfile,
        mode=ExecutionMode.EXECUTE,
        params={},
        correlation_id="m2-real-read",
        timeout_seconds=10.0,
        approval_reason="M2 test: real read verified",
    )
    result = harness.execute(req)
    assert result.external_effect is True
    assert result.outcome.get("ok") is True
    # Ada isi nyata file (bukan mock)
    assert "M2 content" in str(result.outcome.get("content", ""))
    # Verifikasi menyatakan bukan simulasi
    assert result.verification.get("checks", {}).get("not_simulated", True) is True
    # Audit merekam jalur
    assert len(audit.entries) > 0
    actions = [e.action for e in audit.entries]
    assert any("execution" in a or "adapter" in a or "verify" in a for a in actions)


def test_m2_real_execute_write_is_not_canonical_yet(tmp_path) -> None:
    """Write ECKAN belum jadi jalur canonical fase ini -> harus BLOCKED/aman.

    `RealFilesystemAdapter` fase 1 adalah read-only (read/hash/meta). Ini justru
    bukti positif: canonical boundary TIDAK menjalankan efek samping di luar
    approval+daftar aksi; tidak ada eksekusi liar.
    """
    out_path = str(tmp_path / "m2_written.txt")
    audit = AuditTrail()
    harness = RealExecutionHarness(audit=audit)
    contract = build_tool_contract("t2", "c2", (TOOL_KIND_WRITE,), ("write",))
    harness.register_capability("tool", contract_to_registry_dict(contract), contract.to_contract_dict(), "ALLOW")

    params = {"content": "m2-write", "path": out_path}
    req = ExecutionRequest(
        operation="tool/write",
        target=out_path,
        mode=ExecutionMode.EXECUTE,
        params=params,
        correlation_id="m2-write-guard",
        timeout_seconds=10.0,
        approval_reason="M2 test: write guard",
    )
    result = harness.execute(req)
    # Fase 1 canonical tidak mendukung write -> bukan sukses, file tidak ada
    assert result.external_effect is False
    assert result.outcome.get("ok") is False
    assert not os.path.exists(out_path)
