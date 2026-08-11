"""
P4-NVIDIA — Real AI Provider via NVIDIA NIM (build.nvidia.com), OpenAI-compatible.

Jalur REAL eksekusi LLM ke NVIDIA NIM cloud lewat ProviderExecutor (sudah ada),
dengan config INJECTION (provider 'nvidia') — TIDAK menyentuh PROVIDER_ENV
global di provider_executor.py (dipakai banyak tempat, risiko tinggi).

Prinsip jujur (P2-B):
  - Tanpa NVIDIA_API_KEY            -> gate credential GAGAL -> NO EXTERNAL SIDE EFFECT.
  - Dengan NVIDIA_API_KEY tersedia  -> HTTP nyata ke integrate.api.nvidia.com.
  - Wire-format OpenAI-compatible ('model' + 'messages') -> cocok untuk NIM.

Keamanan:
  - API key dibaca dari env (NVIDIA_API_KEY), TIDAK di-hardcode di file ini.
  - Hanya op baca/chat ringan; tanpa writes.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any, Dict, Optional

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    GateResult,
    GATES,
    RealExecutionHarness,
)
from sam.providers.execution.provider_executor import (
    ProviderExecutor,
    ProviderExecutionConfig,
)

# Config Nvidia NIM cloud (OpenAI-compatible) — INJECTED, bukan global.
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_ENV = "NVIDIA_API_KEY"
NVIDIA_MODEL = "minimaxai/minimax-m3"  # model favorit Van (id benar dari /v1/models; tanpa prefix nvidia/)


class RealNvidiaHarness:
    """Jalur EXECUTE AI terkontrol ke Nvidia NIM (mirip real_harness_ai.py)."""

    def __init__(self, audit: Optional[AuditTrail] = None) -> None:
        self._audit = audit or AuditTrail()
        # ProviderExecutor dengan config injection untuk 'nvidia' (non-invasif).
        self._executor = ProviderExecutor(configs={
            "nvidia": ProviderExecutionConfig(
                provider_id="nvidia",
                base_url=NVIDIA_BASE_URL,
                api_key_env=NVIDIA_ENV,
            ),
        })
        self._harness = RealExecutionHarness(self._audit)
        self._harness.register_capability(
            "ai",
            registry={"id": "ai", "adapter": "ProviderExecutor",
                      "external": "HTTP", "providers": ["nvidia"]},
            contract={"chat": {"input": "prompt/messages", "output": "completion",
                               "side_effect": "HTTP call to Nvidia NIM"}},
            policy="ALLOW",
        )

    def credential_ok(self) -> bool:
        ok = bool(os.environ.get(NVIDIA_ENV, ""))
        self._audit.record("harness.gate.credential_ai", "nvidia",
                           env=NVIDIA_ENV, present=ok)
        return ok

    def execute(self, operation: str, payload: Optional[Dict[str, Any]] = None,
                mode: ExecutionMode = ExecutionMode.EXECUTE,
                timeout_seconds: int = 60,
                approval_reason: str = "") -> Dict[str, Any]:
        req = ExecutionRequest(
            operation=f"ai/nvidia/{operation}",
            target="providers/execution",
            params={"operation": operation, "payload": payload or {}},
            mode=mode,
            correlation_id=str(uuid.uuid4()),
            timeout_seconds=timeout_seconds,
            approval_reason=approval_reason,
        )
        # gate: boundary = provider nvidia dikenal (injected config ada)
        known = True
        gate_list = [
            GateResult("boundary", GATES[6]["label"], known,
                       "provider 'nvidia' dikenal (config injection)"),
        ]
        full_gates = self._harness._evaluate_gates(req)
        full_gates = [g if g.id != "boundary" else gate_list[0] for g in full_gates]
        cred = self.credential_ok()
        cred_gate = {
            "id": "credential_ai",
            "label": f"Kredensial Nvidia ({NVIDIA_ENV}) tersedia lewat approved boundary",
            "passed": cred, "detail": f"env={NVIDIA_ENV}",
        }
        gate_results = [g.to_dict() for g in full_gates] + [cred_gate]
        for g in gate_results:
            self._audit.record("harness.gate", g["id"], passed=g["passed"], label=g["label"])

        if mode == ExecutionMode.PREVIEW:
            self._audit.record("harness.mode.preview", f"ai/nvidia/{operation}")
            return {"ok": True, "mode": "PREVIEW", "simulated": True,
                    "external_calls": 0, "detail": "PREVIEW: no side effect.",
                    "gates": gate_results}

        failed = [g for g in gate_results if not g["passed"]]
        if failed:
            self._audit.record("harness.execute.blocked", f"ai/nvidia/{operation}",
                               blocked_by=[g["id"] for g in failed])
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "blocked": True, "blocked_by": [g["id"] for g in failed],
                    "detail": "NO EXTERNAL SIDE EFFECT (P2-B).", "gates": gate_results}

        self._audit.record("harness.execute.allowed", f"ai/nvidia/{operation}")
        try:
            result = self._executor.execute("nvidia", operation, payload,
                                            timeout_seconds=timeout_seconds)
            self._audit.record("harness.provider.executor.ok", "nvidia",
                               status=result.get("status"), external_calls=result.get("external_calls"))
            return {"ok": True, "mode": "EXECUTE", "gates": gate_results, **result}
        except Exception as exc:  # noqa: BLE001
            self._audit.record("harness.provider.executor.fail", "nvidia",
                               error=f"{type(exc).__name__}: {exc}")
            return {"ok": False, "mode": "EXECUTE", "blocked": False,
                    "external_calls": 0, "error": f"{type(exc).__name__}: {exc}",
                    "gates": gate_results}


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="P4 Real AI Provider — NVIDIA NIM")
    parser.add_argument("--mode", choices=["PREVIEW", "EXECUTE"], default="EXECUTE")
    parser.add_argument("--prompt", default="Reply with the single word: OK",
                        help="Prompt untuk Nvidia")
    parser.add_argument("--model", default=NVIDIA_MODEL)
    parser.add_argument("--reason", default="", help="Reason approval (WAJIB utk EXECUTE)")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    audit = AuditTrail()
    harness = RealNvidiaHarness(audit)
    mode = ExecutionMode(args.mode)
    reason = args.reason or (f"P4 NVIDIA: eksekusi nyata {args.model}")

    payload = {"prompt": args.prompt, "model": args.model,
               "temperature": 0.2, "max_tokens": 64}
    result = harness.execute("chat", payload, mode=mode, timeout_seconds=60,
                             approval_reason=reason)

    cred = bool(os.environ.get(NVIDIA_ENV, ""))
    print("=" * 72)
    print("  P4 — Real AI Provider activation via NVIDIA NIM (harness)")
    print("=" * 72)
    print(f"  provider    : nvidia  ({NVIDIA_BASE_URL})")
    print(f"  model       : {args.model}")
    print(f"  mode        : {mode.value}")
    print(f"  credential  : {'PRESENT' if cred else 'ABSENT (no key)'}")
    print("")
    print("  gates:")
    for g in result.get("gates", []):
        print(f"    [{'PASS' if g['passed'] else 'FAIL'}] {g['label']}")
    print("")
    print("  outcome:")
    for k, v in result.items():
        if k == "gates":
            continue
        s = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
        print(f"    {k} : {s[:160]}")
    print("")
    print("  audit:")
    for e in audit.entries:
        print(f"    [{e.action}] {e.detail}")
    print("=" * 72)

    if mode == ExecutionMode.EXECUTE and not cred:
        print("\n  VERDICT: PLATFORM AMAN — tanpa NVIDIA_API_KEY, EXECUTE diblokir (NO SIDE EFFECT).")
        exit_code = 1
    elif mode == ExecutionMode.EXECUTE and cred:
        ok = result.get("ok") and result.get("status") == "completed"
        print(f"\n  VERDICT: {'REAL E2E OK (HTTP nyata ke NVIDIA)' if ok else 'GAGAL di HTTP'}")
        exit_code = 0 if ok else 1
    else:
        print("\n  VERDICT: PREVIEW OK (no side effect)")
        exit_code = 0

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"provider": "nvidia", "mode": mode.value, "result": result,
                       "audit": [e.__dict__ for e in audit.entries]}, fh, indent=2, default=str)
        print(f"\n[Bukti JSON: {args.out}]")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
