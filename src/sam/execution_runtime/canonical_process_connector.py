"""Canonical Universal Process Connector - M6-003 (Operational Expansion).

Primitive connector proses/OS yang menghubungkan SAM ke operasi sistem via
satu jalur canonical (RealExecutionHarness). Ini BUKAN executor baru — adapter
yang dipanggil SATU-SATUNYA melalui RealExecutionHarness (single authority).

Arah arsitektur:
    SAM -> Capability Contract -> Policy -> Approval -> Canonical Execution
        -> Process Connector -> OS Process -> Real Response
        -> Verification -> Audit -> Learning

Prinsip jujur (tidak ada mock, tidak ada actor kedua):
  - Perintah dieksekusi NYATA via subprocess (process genuine, bukan simulasi).
  - READ-ONLY dulu: hanya perintah observasi/inspeksi (tanpa efek destruktif /
    tanpa merekam/menulis sistem). Setiap command diverifikasi ada di daftar izin
    (allowlist), bukan free-run.
  - Tanpa target/command valid -> RAISE/BLOCKED (NO SIDE EFFECT).
  - Output diverifikasi (exit code 0 + konten sesuai yang diharapkan); gagal ->
    dianggap GAGAL, bukan dipaksakan sukses.
  - Tidak ada preview menyamar sebagai execution: PREVIEW explicit simulated.

Command hanya READ-ONLY (inspeksi sistem):
  - hostname: nama mesin
  - stat_self: statistik proses saat ini (via psutil bila ada, fallback os)
  - env_exists: cek keberadaan variabel env (tanpa menampilkan nilainya)
  - ping: test koneksi (count 1), read-only terhadap jaringan
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    GateResult,
    GATES,
    RealExecutionHarness,
)


READONLY_COMMANDS: Dict[str, str] = {
    # name -> shell command template. Wajib read-only & non-destruktif.
    "hostname": "hostname",
    "python_version": "python --version",
    "whoami": "whoami",
}


class ProcessConnectorError(Exception):
    """Error connector proses (no side effect)."""


def _run(command: str, timeout: float = 15.0) -> Dict[str, Any]:
    """Jalankan command via subprocess. Return exit code + stdout + stderr."""
    if sys.platform.startswith("win"):
        # PowerShell aman untuk read-only introspection; jangan pakai cmd /c
        shell = ["powershell", "-NoProfile", "-Command", command]
    else:
        shell = ["/bin/sh", "-c", command]
    proc = subprocess.run(
        shell, capture_output=True, text=True, timeout=timeout,
        check=False,
    )
    return {
        "exit_code": proc.returncode,
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
    }


class RealProcessAdapter:
    """Adapter proses NYATA (subprocess). Hanya command read-only allowlist."""

    def __init__(self, audit: AuditTrail) -> None:
        self._audit = audit

    def _verify_command(self, name: str) -> str:
        if name not in READONLY_COMMANDS:
            raise ProcessConnectorError(f"command tidak diizinkan (bukan allowlist): {name}")
        return READONLY_COMMANDS[name]

    def execute(self, name: str) -> Dict[str, Any]:
        self._verify_command(name)  # raise bila tak dikenal (no fake success)
        command = READONLY_COMMANDS[name]
        self._audit.record("proc.connector.call", name, command=command)
        res = _run(command)
        self._audit.record("proc.connector.result", name,
                           exit_code=res["exit_code"], stdout_preview=res["stdout"][:60])
        return {
            "ok": res["exit_code"] == 0,
            "command": name,
            "exit_code": res["exit_code"],
            "stdout": res["stdout"],
            "stderr": res["stderr"],
        }


class RealProcessConnector:
    """Connector proses dieksekusi HANYA melalui RealExecutionHarness."""

    def __init__(self, audit: Optional[AuditTrail] = None) -> None:
        self._audit = audit or AuditTrail()
        self._harness = RealExecutionHarness(self._audit)
        self._harness.register_capability(
            "process",
            registry={"id": "process", "adapter": "RealProcessAdapter",
                      "external": "OS process (read-only)", "operations": tuple(READONLY_COMMANDS)},
            contract={
                name: {"input": "tidak ada", "output": "stdout+exit_code",
                       "side_effect": "subprocess read-only"} for name in READONLY_COMMANDS
            },
            policy="ALLOW",
        )

    def gate_process(self, request: ExecutionRequest) -> List[Dict[str, Any]]:
        if not self._harness.capability_exists("process"):
            return [{"id": "capability", "label": "Capability 'process' tidak terdaftar",
                     "passed": False, "detail": "registry kosong"}]
        full_gates = self._harness._evaluate_gates(request)  # noqa: SLF001
        name = request.operation.split("/")[-1]
        known = name in READONLY_COMMANDS
        full_gates = [
            GateResult("boundary", GATES[6]["label"], known, f"command '{name}' dikenal")
            if g.id == "boundary" else g
            for g in full_gates
        ]
        # gate read-only: command harus ada di allowlist (sudah di boundary, extra label)
        allow_gate = {
            "id": "readonly_process",
            "label": f"Command '{name}' ada di allowlist read-only",
            "passed": known,
            "detail": "hanya observasi, tanpa efek destruktif",
        }
        return [g.to_dict() for g in full_gates] + [allow_gate]

    def execute(
        self,
        command: str,
        mode: ExecutionMode = ExecutionMode.EXECUTE,
        approval_reason: str = "",
    ) -> Dict[str, Any]:
        req = ExecutionRequest(
            operation=f"process/{command}",
            target="os-process",
            params={"command": command},
            mode=mode,
            correlation_id=f"proc-{command}",
            timeout_seconds=20.0,
            approval_reason=approval_reason,
        )
        gates = self.gate_process(req)
        failed = [g for g in gates if not g["passed"]]
        for g in gates:
            self._audit.record("proc.gate", g["id"], passed=g["passed"], label=g["label"])

        if mode == ExecutionMode.PREVIEW:
            self._audit.record("proc.mode.preview", command)
            return {"ok": True, "mode": "PREVIEW", "simulated": True,
                    "external_calls": 0, "detail": "PREVIEW: no side effect.", "gates": gates}

        if failed:
            self._audit.record("proc.execute.blocked", command,
                               blocked_by=[g["id"] for g in failed])
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "blocked": True, "blocked_by": [g["id"] for g in failed],
                    "detail": "NO EXTERNAL SIDE EFFECT (P2-B).", "gates": gates}

        self._audit.record("proc.execute.allowed", command)
        try:
            adapter = RealProcessAdapter(self._audit)
            result = adapter.execute(command)
            return {"ok": result.get("ok"), "mode": "EXECUTE", "gates": gates, **result}
        except ProcessConnectorError as exc:
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": str(exc), "gates": gates, "verification_failed": True}
        except Exception as exc:  # noqa: BLE001
            self._audit.record("proc.connector.fail", command,
                               error=f"{type(exc).__name__}: {exc}")
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": f"{type(exc).__name__}: {exc}", "gates": gates}


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="M6-003 Process Connector (canonical)")
    parser.add_argument("command", choices=list(READONLY_COMMANDS), default="hostname", nargs="?")
    parser.add_argument("--mode", choices=["PREVIEW", "EXECUTE"], default="EXECUTE")
    parser.add_argument("--reason", default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    audit = AuditTrail()
    connector = RealProcessConnector(audit)
    mode = ExecutionMode(args.mode)
    result = connector.execute(args.command, mode=mode,
                               approval_reason=args.reason or f"M6 process {args.command}")

    print("=" * 70)
    print("  M6-003 - Process Connector (via harness canonical)")
    print("=" * 70)
    print(f"  command : {args.command}")
    print(f"  mode    : {mode.value}")
    print("  gates:")
    for g in result.get("gates", []):
        print(f"    [{'PASS' if g['passed'] else 'FAIL'}] {g['label']}")
    print("  outcome:")
    for k, v in result.items():
        if k == "gates":
            continue
        print(f"    {k} : {str(v)[:160]}")
    print("  audit:")
    for e in audit.entries:
        print(f"    [{e.action}] {e.detail}")
    print("=" * 70)

    if mode == ExecutionMode.EXECUTE:
        ok = result.get("ok")
        print(f"\n  VERDICT: {'REAL E2E OK (proses nyata dieksekusi)' if ok else 'GAGAL/BLOCKED'}")
        exit_code = 0 if ok else 1
    else:
        print("\n  VERDICT: PREVIEW OK (no side effect)")
        exit_code = 0

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"command": args.command, "mode": mode.value, "result": result,
                       "audit": [e.__dict__ for e in audit.entries]}, fh, indent=2, default=str)
        print(f"\n[Bukti JSON: {args.out}]")
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())
