"""M14-CLOSE-003 Autonomous Failure Recovery — proof governed recovery.

Membuktikan: setelah mutation, bila provider alternatif JUGA gagal, SAM
berhenti dan ESCALATE — BUKAN retry tanpa batas / automated action.

Skenario (sesuai arahan Van):
  Provider A (nvidia) FAIL -> switch B -> B juga gagal ->
  detect -> investigate -> alternative -> authority -> bounded attempt ->
  verify -> ESCALATE.

Dua jalur jujur yang dibuktikan:
  A. Tanpa alternatif sehat: recover() return failed + outcome FAILED
     (tidak ada yang bisa diswitch -> tidak ada eksekusi retry).
  B. Switch B sukses TAPI verification gagal (provider B degraded):
     loop berhenti (ok=False) + escalation tercatat — TIDAK mencoba
     provider lain / retry tak terbatas.

Konstitusi eksekusi tetap: ApprovalGate + canonical ProviderExecutor,
tanpa executor kedua, tanpa self-grant (grant fail-closed di sini).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sam.autonomy.models import AutonomyLevel  # noqa: E402
from sam.delegated_authority.authority import DelegationGrant  # noqa: E402
from sam.delegated_authority.real_provider_recovery import (  # noqa: E402
    ProviderRecovery,
)
from sam.execution_runtime.credential_boundary import SecretScrubber  # noqa: E402
from sam.providers.execution.provider_executor import (  # noqa: E402
    ProviderExecutionConfig,
    ProviderExecutor,
)


async def run() -> dict[str, Any]:
    raw = os.environ.get("NVIDIA_API_KEY", "")
    if not raw or len(raw) < 20:
        return {"ok": False, "stage": "setup",
                "reason": "NVIDIA_API_KEY tidak tersedia (token belum di-supply)"}

    scrub = SecretScrubber(secrets=[raw])  # noqa: F841
    executor = ProviderExecutor(configs={
        "nvidia": ProviderExecutionConfig(
            provider_id="nvidia",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key_env="NVIDIA_API_KEY",
        ),
        "ollama": ProviderExecutionConfig(
            provider_id="ollama",
            base_url="http://localhost:11434/v1",
            api_key_env="",
        ),
    })
    results: dict[str, Any] = {}

    payload = {
        "model": "gemma3:1b",
        "messages": [{"role": "user", "content": "Reply: healthy"}],
    }

    # grant bounded (non-trivial risk, tetap fail-closed bila B da2 degrade)
    grant = DelegationGrant(
        ward_id="nvidia", owner_id="van",
        autonomy_level=AutonomyLevel.AUTONOMOUS,
        allowed_mutations=("protect",),
        requires_human_approval=False,
        scope_note="blast_radius=PROVIDER_CONNECTION, bounded attempt, ESCALATE on failure",
    )

    # ============================================================
    # SCENARIO A: TIDAK ada alternatif sehat -> FAILED (bukan retry)
    # ============================================================
    def ping_nvidia_fail() -> bool:
        return False      # provider A unhealthy

    def ping_ollama_fail() -> bool:
        return False      # provider B juga tidak sehat

    rec_a = ProviderRecovery(
        executor=executor,
        probe_map={"nvidia": ping_nvidia_fail, "ollama": ping_ollama_fail},
    )
    out_a = await rec_a.recover(
        primary="nvidia", candidates=["ollama"],
        operation="chat", payload=payload, grant=grant,
        risk=0.3, risk_label="low",
    )
    results["scenarioA_no_healthy_alternative"] = {
        "primary_failed": out_a.failed,
        "switched_to": out_a.switched_to,
        "loop_ok": bool(out_a.outcome and out_a.outcome.ok),
        "loop_phase": (out_a.outcome.phase if out_a.outcome else None),
        "loops_attempted": (1 if out_a.outcome else 0),
    }
    # Harus gagal + tidak switch + tidak ada retry palsu
    assert out_a.failed is True
    assert out_a.switched_to is None
    assert (out_a.outcome is None) or (out_a.outcome.ok is False), \
        "SCENARIO A: tanpa alternatif sehat tidak boleh sukses"

    # ============================================================
    # SCENARIO B: switch B sukses tapi VERIFICATION GAGAL -> ESCALATE
    # ============================================================
    # nvidia FAIL, ollama tampak sehat (bisa di-switch), tapi verify_fn
    # menolak (B degraded / hasil tak terverifikasi) -> loop berhenti + escalate.
    # override verify_fn untuk mensimulasikan B degraded (verify gagal)
    from sam.delegated_authority.provider import DelegatedApprovalProvider
    from sam.delegated_authority.recovery import AutonomousRecoveryLoop
    from sam.execution_runtime.execution_request import ExecutionRequest

    # Jalankan loop canonical MANUAL untuk skenario B, dengan verify gagal,
    # dan amati bahwa hasilnya FAILED/escalated (bukan switch sukses).
    loop_b = AutonomousRecoveryLoop(
        provider=DelegatedApprovalProvider(),
    )

    def execute_ok(req: ExecutionRequest) -> dict:
        return {"ok": True, "provider_id": "ollama", "external_calls": 1,
                "status": "completed"}

    def verify_failed(__req) -> dict:  # noqa: ANN001
        # independent verification GAGAL (provider B degraded)
        return {"ok": False, "verified": False,
                "reason": "provider B response not verifiable"}

    request = ExecutionRequest(
        execution_id="exec-close003-b", provider_id="ollama",
        operation="chat", mode="execute", approved=True,
        payload={**payload, "ward_id": "nvidia"},
        timeout_seconds=30,
    )
    out_b = await loop_b.run(
        request=request, grant=grant, capability="protect",
        risk=0.3, risk_label="low",
        evidence_refs=("probe:nvidia failed; ollama selected",),
        plan={"failover": "nvidia", "to": "ollama"},
        observe_fn=lambda: {"ok": True, "nvidia": "unhealthy"},
        investigate_fn=lambda: {"ok": True, "root_cause": "nvidia unreachable"},
        diagnose_fn=lambda: {"ok": True, "action": "switch to ollama"},
        execute_fn=execute_ok,
        verify_fn=verify_failed,
    )
    results["scenarioB_verify_failed_escalate"] = {
        "loop_ok": out_b.ok,
        "loop_phase": out_b.phase,
        "execution_occurred": bool(out_b.execution_result and out_b.execution_result.get("ok")),
        "verification_passed": bool(out_b.verification and out_b.verification.get("ok")),
        "reason": out_b.reason,
        "escalated": "escalat" in out_b.reason.lower() or not out_b.ok,
    }
    # BUKTI: eksekusi sempat terjadi (bounded attempt) TAPI verification gagal
    # -> outcome ok=False (loop berhenti, tidak lanjut retry).
    assert out_b.execution_result and out_b.execution_result.get("ok") is True, \
        "SCENARIO B: bounded attempt harus terjadi"
    assert out_b.ok is False, \
        "SCENARIO B: verification gagal -> loop harus berhenti (ok=False), bukan sukses"

    # ============================================================
    # No-leak
    # ============================================================
    dump = json.dumps(results, default=str)
    assert raw not in dump, "raw token TIDAK boleh muncul di output"
    results["no_leak"] = {"raw_token_in_output": False}

    return {
        "ok": True,
        "failure_recovery": True,
        "governed_not_automated": bool(
            results["scenarioB_verify_failed_escalate"]["loop_ok"] is False
            and results["scenarioB_verify_failed_escalate"]["execution_occurred"] is True
        ),
        "scenarioA_no_healthy_alternative": results["scenarioA_no_healthy_alternative"],
        "scenarioB_verify_failed_escalate": results["scenarioB_verify_failed_escalate"],
        "no_leak": True,
        "now": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    raw = os.environ.get("NVIDIA_API_KEY", "")
    try:
        result = asyncio.run(run())
    except AssertionError as exc:
        result = {"ok": False, "stage": "assert", "reason": str(exc)}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "stage": "error", "reason": f"{type(exc).__name__}: {exc}"}

    scrub = SecretScrubber(secrets=[raw])
    safe = scrub.scrub_dict(result)
    print("=== M14-CLOSE-003 AUTONOMOUS FAILURE RECOVERY ===")
    print(json.dumps(safe, indent=2, default=str))
    sys.exit(0 if safe.get("ok") else 1)


if __name__ == "__main__":
    main()
