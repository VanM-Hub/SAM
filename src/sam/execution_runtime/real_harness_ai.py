"""
P4 — Real AI Provider activation via harness.

Mengintegrasikan jalur HTTP NYATA `ProviderExecutor` (providers/execution/
provider_executor.py) ke pola RealExecutionHarness (P2-B).

Prinsip jujur:
  - Tanpa kredensial (env var API key kosong / Van offline)
        -> gate credential GAGAL -> NO EXTERNAL SIDE EFFECT (terbukti aman).
  - Dengan kredensial tersedia
        -> jalur HTTP httpx nyata berjalan ke provider (terbukti E2E).

Tidak ada kredensial di-hardcode (baca dari environment). Non-invasif:
modul ini hanya memakai ProviderExecutor yang SUDAH ADA + pola gate P2-B.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any, Dict, List, Optional

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    GateResult,
    GATES,
    RealExecutionHarness,
)

# Jalur HTTP nyata yang SUDAH ADA di SAM
from sam.providers.execution.provider_executor import (
    PROVIDER_ENV,
    ProviderExecutor,
    ProviderExecutionConfig,
)


# ---------------------------------------------------------------------------
# Gate credential tambahan (P4) — provider AI butuh API key via approved boundary
# ---------------------------------------------------------------------------

def provider_credential_gate(provider_id: str, audit: AuditTrail) -> bool:
    """Pastikan provider punya kredensial sebelum EXECUTE. Tanpa -> NO SIDE EFFECT."""
    env, _ = PROVIDER_ENV.get(provider_id, ("", ""))
    ok = bool(env) and bool(os.environ.get(env, ""))
    audit.record("harness.gate.credential_ai", provider_id,
                 env=env or "(non-auth)", present=ok)
    return ok


# ---------------------------------------------------------------------------
# Harness AI — meneruskan ke ProviderExecutor saat semua gate lolos
# ---------------------------------------------------------------------------

class RealAIProviderHarness:
    """Jalur EXECUTE AI terkontrol: gate P2-B + gate credential provider."""

    def __init__(self, audit: Optional[AuditTrail] = None) -> None:
        self._audit = audit or AuditTrail()
        self._executor = ProviderExecutor()  # SUDAH ADA; baca env saat execute
        self._harness = RealExecutionHarness(self._audit)
        # Daftarkan capability 'ai' (satu segmen — cocok dengan `split("/")[0]` di gate P2-B)
        self._harness.register_capability(
            "ai",
            registry={"id": "ai", "adapter": "ProviderExecutor",
                      "external": "HTTP", "providers": [p for p, (e, b) in PROVIDER_ENV.items() if b and e]},
            contract={"chat": {"input": "prompt/messages", "output": "completion", "side_effect": "HTTP call"}},
            policy="ALLOW",
        )

    def register_adapter(self, provider_id: str, adapter) -> None:
        self._executor.register_adapter(provider_id, adapter)

    def gate_ai(self, provider_id: str, request: ExecutionRequest) -> List[Dict[str, Any]]:
        """Evaluasi semua gate P2-B + gate credential provider."""
        # pastikan capability 'ai' terdaftar (segmen pertama operation = 'ai')
        if not self._harness.capability_exists("ai"):
            return [{"id": "capability", "label": "Capability 'ai' tidak terdaftar",
                     "passed": False, "detail": "registry kosong"}]
        # evaluasi 14 gate P2-B lewat harness standar (cap 'ai' sudah di-registry)
        full_gates = self._harness._evaluate_gates(request)
        # gate 'boundary' hardcoded cek file -> untuk AI timpa: boundary = provider dikenal di PROVIDER_ENV
        known = provider_id in PROVIDER_ENV and bool(PROVIDER_ENV[provider_id][1])
        full_gates = [
            GateResult("boundary", GATES[6]["label"], known,
                       f"provider '{provider_id}' dikenal di PROVIDER_ENV")
            if g.id == "boundary" else g
            for g in full_gates
        ]

        # gate tambahan: credential provider AI
        cred_ok = provider_credential_gate(provider_id, self._audit)
        cred_gate = {
            "id": "credential_ai",
            "label": f"Kredensial provider '{provider_id}' tersedia lewat approved boundary",
            "passed": cred_ok,
            "detail": f"env={PROVIDER_ENV.get(provider_id, ('',''))[0] or 'non-auth'}",
        }

        all_results = [g.to_dict() for g in full_gates] + [cred_gate]
        return all_results

    def execute(self, provider_id: str, operation: str,
                payload: Optional[Dict[str, Any]] = None,
                mode: ExecutionMode = ExecutionMode.EXECUTE,
                timeout_seconds: int = 30,
                approval_reason: str = "") -> Dict[str, Any]:
        """Jalur eksekusi AI. Invariant P2-B: gate gagal -> NO EXTERNAL SIDE EFFECT."""
        req = ExecutionRequest(
            operation=f"ai/{provider_id}/{operation}",
            target="providers/execution",
            params={"operation": operation, "payload": payload or {}},
            mode=mode,
            correlation_id=str(uuid.uuid4()),
            timeout_seconds=timeout_seconds,
            approval_reason=approval_reason,
        )

        # evaluasi semua gate (14 P2-B + credential provider)
        gate_results = self.gate_ai(provider_id, req)
        failed = [g for g in gate_results if not g["passed"]]

        for g in gate_results:
            self._audit.record("harness.gate", g["id"], passed=g["passed"], label=g["label"])

        # PREVIEW -> aman, simulasi, no HTTP
        if mode == ExecutionMode.PREVIEW:
            self._audit.record("harness.mode.preview", f"ai/{provider_id}/{operation}")
            return {
                "ok": True, "mode": "PREVIEW", "simulated": True,
                "external_calls": 0,
                "detail": "PREVIEW: no external side effect.",
                "gates": gate_results,
            }

        # EXECUTE -> semua gate wajib
        if failed:
            self._audit.record("harness.execute.blocked", f"ai/{provider_id}/{operation}",
                               blocked_by=[g["id"] for g in failed])
            return {
                "ok": False, "mode": "EXECUTE",
                "external_calls": 0, "blocked": True,
                "blocked_by": [g["id"] for g in failed],
                "detail": "NO EXTERNAL SIDE EFFECT (P2-B).",
                "gates": gate_results,
            }

        # Semua gate lolos -> jalankan ProviderExecutor (HTTP nyata)
        self._audit.record("harness.execute.allowed", f"ai/{provider_id}/{operation}")
        self._audit.record("harness.provider.executor.dispatch", provider_id,
                           operation=operation, mode="execute")
        try:
            result = self._executor.execute(
                provider_id, operation, payload,
                timeout_seconds=timeout_seconds,
            )
            self._audit.record("harness.provider.executor.ok", provider_id,
                               status=result.get("status"), external_calls=result.get("external_calls"))
            return {"ok": True, "mode": "EXECUTE", "gates": gate_results, **result}
        except Exception as exc:  # noqa: BLE001
            self._audit.record("harness.provider.executor.fail", provider_id,
                               error=f"{type(exc).__name__}: {exc}")
            return {
                "ok": False, "mode": "EXECUTE", "blocked": False,
                "external_calls": 0,
                "error": f"{type(exc).__name__}: {exc}",
                "gates": gate_results,
            }


# ---------------------------------------------------------------------------
# CLI pembuktian
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="P4 Real AI Provider activation")
    parser.add_argument("provider", nargs="?", default="openai",
                        choices=list(PROVIDER_ENV.keys()),
                        help="Provider (default: openai)")
    parser.add_argument("--mode", choices=["PREVIEW", "EXECUTE"], default="EXECUTE")
    parser.add_argument("--prompt", default="Hello SAM, reply briefly.",
                        help="Prompt untuk provider")
    parser.add_argument("--reason", default="",
                        help="Reason approval (WAJIB utk EXECUTE)")
    parser.add_argument("--out", default=None, help="Simpan bukti ke JSON")
    args = parser.parse_args(argv)

    audit = AuditTrail()
    harness = RealAIProviderHarness(audit)

    mode = ExecutionMode(args.mode)
    reason = args.reason or (f"P4: eksekusi nyata {args.provider}" if mode == ExecutionMode.EXECUTE else "")

    payload = {
        "prompt": args.prompt,
        "model": "default",
        "temperature": 0.2,
        "max_tokens": 256,
    }

    result = harness.execute(
        args.provider, "chat", payload,
        mode=mode, timeout_seconds=30, approval_reason=reason,
    )

    env, base = PROVIDER_ENV.get(args.provider, ("", ""))
    cred_present = bool(env) and bool(os.environ.get(env, ""))

    print("=" * 70)
    print("  P4 — Real AI Provider activation (via harness)")
    print("=" * 70)
    print(f"  provider    : {args.provider}")
    print(f"  mode        : {mode.value}")
    print(f"  env var     : {env or '(non-auth)'}")
    print(f"  credential  : {'PRESENT' if cred_present else 'ABSENT (offline/no key)'}")
    print(f"  correlation : {result.get('correlation_id','n/a')}")
    print("")
    print("  gates:")
    for g in result.get("gates", []):
        print(f"    [{'PASS' if g['passed'] else 'FAIL'}] {g['label']}")
    print("")
    print("  outcome:")
    for k, v in result.items():
        if k in ("gates",):
            continue
        if isinstance(v, dict):
            print(f"    {k} : {json.dumps(v, ensure_ascii=False)[:120]}")
        elif isinstance(v, (list,)):
            print(f"    {k} : {str(v)[:120]}")
        else:
            print(f"    {k} : {v}")
    print("")
    print("  audit (ringkas):")
    for e in audit.entries:
        print(f"    [{e.action}] {e.detail}")
    print("=" * 70)

    # Verdict
    if mode == ExecutionMode.EXECUTE and not cred_present:
        # Tanpa kredensial -> NO SIDE EFFECT adalah hasil yang BENAR & aman
        print("\n  VERDICT: PLATFORM AMAN — tanpa kredensial, EXECUTE diblokir")
        print("           (NO EXTERNAL SIDE EFFECT, sesuai P2-B).")
        print("           Untuk E2E penuh: set API key env saat online.")
        exit_code = 1
    elif mode == ExecutionMode.EXECUTE and cred_present:
        ok = result.get("ok") and result.get("status") == "completed"
        print(f"\n  VERDICT: {'REAL E2E OK (HTTP nyata ke ' + args.provider + ')' if ok else 'GAGAL di HTTP'}")
        exit_code = 0 if ok else 1
    else:
        print("\n  VERDICT: PREVIEW OK (no side effect)")
        exit_code = 0

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"provider": args.provider, "mode": mode.value,
                       "result": result, "audit": [e.__dict__ for e in audit.entries]},
                      fh, indent=2, default=str)
        print(f"\n[Bukti JSON disimpan ke: {args.out}]")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
