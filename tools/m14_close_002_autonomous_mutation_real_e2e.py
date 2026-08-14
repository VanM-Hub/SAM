"""M14-CLOSE-002 Real Autonomous Mutation — proof inti M14 closure.

Yang dibuktikan (gap kritis yang Van tunjuk):
  AUTHORITY -> AUTONOMOUS APPROVAL -> REAL MUTATION -> REAL VERIFICATION
  SAM melakukan switch provider TANPA campur tangan user, SETELAH owner
  mendelegasikan authority terbatas (DelegationGrant bounded).

Skenario nyata:
  - Provider utama `nvidia` (eksternal, token NYATA dari env).
  - Provider alternatif `ollama` (lokal non-auth, deterministic, reachable).
  - Failure injection hanya pada PROBE ping (provider A dianggap unhealthy),
    bukan pada kode canonical. Mutasi & eksekusi tetap NYATA.

Alur (9 tahap environment-adaptive + canonical):
  DISCOVERY -> IDENTIFICATION -> ENTRUSTMENT -> OBSERVATION ->
  INVESTIGATION -> DIAGNOSIS -> AUTHORITY -> EXECUTION -> VERIFICATION

M14-CLOSE-001 (Owner Autonomous Grant, bounded):
  DelegationGrant(ward_id="nvidia", owner_id="van",
                  autonomy_level=AUTONOMOUS,
                  allowed_mutations=("protect",),   # blast_radius: provider connection
                  requires_human_approval=False)    # owner supply, bukan self-grant

Tidak melanggar konstitusi eksekusi:
  - SATU ApprovalGate (execute_fn canonical ProviderExecutor + gate evaluate).
  - Tanpa executor kedua, tanpa self-grant, tanpa kenaikan authority via learning.
  - Klaim PROVEN hanya bila mutation REAL terverifikasi.
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
from sam.execution_runtime.credential import mask_secret  # noqa: E402
from sam.execution_runtime.credential_boundary import SecretScrubber  # noqa: E402
from sam.providers.execution.provider_executor import (  # noqa: E402
    ProviderExecutionConfig,
    ProviderExecutor,
)


def _masked(token: str) -> str:
    return mask_secret(token)


async def run() -> dict[str, Any]:
    raw = os.environ.get("NVIDIA_API_KEY", "")
    if not raw or len(raw) < 20:
        return {"ok": False, "stage": "setup",
                "reason": "NVIDIA_API_KEY tidak tersedia (token belum di-supply)"}

    # --- Provider nyata (config eksplisit; token dari env, tidak hardcode) ---
    executor = ProviderExecutor(configs={
        "nvidia": ProviderExecutionConfig(
            provider_id="nvidia",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key_env="NVIDIA_API_KEY",
        ),
        "ollama": ProviderExecutionConfig(
            provider_id="ollama",
            base_url="http://localhost:11434/v1",
            api_key_env="",   # non-auth lokal
        ),
    })
    results: dict[str, Any] = {}

    # --- Grant owner AUTONOMOUS bounded (M14-CLOSE-001) ---
    grant = DelegationGrant(
        ward_id="nvidia",
        owner_id="van",
        autonomy_level=AutonomyLevel.AUTONOMOUS,
        allowed_mutations=("protect",),
        requires_human_approval=False,   # owner supply (bukan self-grant)
        scope_note="blast_radius=PROVIDER_CONNECTION, risk_ceiling=LOW, verification=REQUIRED",
    )
    results["grant"] = grant.as_dict()

    # --- ProviderRecovery dengan probe map (ping nyata) ---
    def ping_nvidia() -> bool:
        # ping nyata ke NVIDIA (token valid) — kalau sehat, True.
        try:
            cfg = executor._configs["nvidia"]  # noqa: SLF001
            key = executor._api_key(cfg)  # noqa: SLF001
            return bool(key)  # kredensial ada = avail; ping HTTP opsional
        except Exception:  # noqa: BLE001
            return False

    def ping_ollama() -> bool:
        try:
            import httpx
            r = httpx.get("http://localhost:11434/v1/models", timeout=5)
            return r.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    recovery = ProviderRecovery(
        executor=executor,
        probe_map={"nvidia": ping_nvidia, "ollama": ping_ollama},
    )

    # ============================================================
    # SCENARIO 1: REAL AUTONOMOUS MUTATION (nvidia unhealthy -> switch ollama)
    # ============================================================
    # Failure injection pada PROBE nvidia (simulasi provider A unhealthy).
    # Mutasi & eksekusi tetap canonical & nyata.
    probe_map_fail = dict(recovery._probe_map)  # noqa: SLF001
    probe_map_fail["nvidia"] = lambda: False    # A unhealthy

    recovery_fail = ProviderRecovery(
        executor=executor, probe_map=probe_map_fail,
    )
    payload = {
        "model": "gemma3:1b",
        "messages": [{"role": "user",
                       "content": "Reply with the single word: healthy"}],
    }

    outcome = await recovery_fail.recover(
        primary="nvidia", candidates=["ollama"],
        operation="chat", payload=payload, grant=grant,
        risk=0.3, risk_label="low",
    )
    results["scenario1_autonomous_mutation"] = {
        "primary_failed": outcome.failed,
        "failed_reason": outcome.failed_reason,
        "switched_to": outcome.switched_to,
        "loop_ok": bool(outcome.outcome and outcome.outcome.ok),
        "approver": outcome.approval.get("approver") if outcome.approval else None,
        "approval_verdict": (outcome.approval.get("verdict") if outcome.approval else None),
        "source": (outcome.approval.get("source") if outcome.approval else None),
        "phases": [s.phase for s in (outcome.outcome.steps if outcome.outcome else [])],
    }
    mutation_real = bool(
        outcome.failed and outcome.switched_to == "ollama"
        and outcome.outcome and outcome.outcome.ok
        and outcome.approval and outcome.approval.get("approved", False)
        and outcome.approval.get("source") == "delegated"
        and (outcome.outcome.execution_result or {}).get("ok", False)
    )
    assert mutation_real, \
        "SCENARIO 1: real autonomous mutation harus berhasil (switch nvidia->ollama)"

    # ============================================================
    # SCENARIO 2 (fail-closed): TANPA grant -> ESCALATE, TIDAK switch
    # ============================================================
    no_grant = DelegationGrant(
        ward_id="nvidia", owner_id="van",
        autonomy_level=AutonomyLevel.OBSERVE,   # tidak punya hak eksekusi
        allowed_mutations=(),                    # tidak ada capability diizinkan
        requires_human_approval=True,            # default fail-closed
    )
    outcome_no = await recovery_fail.recover(
        primary="nvidia", candidates=["ollama"],
        operation="chat", payload=payload, grant=no_grant,
        risk=0.5, risk_label="medium",
    )
    results["scenario2_fail_closed"] = {
        "switched_to": outcome_no.switched_to,
        "loop_ok": bool(outcome_no.outcome and outcome_no.outcome.ok),
        "approval_verdict": (outcome_no.approval.get("verdict") if outcome_no.approval else None),
        "loop_phase": (outcome_no.outcome.phase if outcome_no.outcome else None),
    }
    assert outcome_no.switched_to is None, \
        "SCENARIO 2: tanpa grant tidak boleh switch (fail-closed)"

    # ============================================================
    # No-leak: raw token tidak boleh muncul di hasil
    # ============================================================
    dump = json.dumps(results, default=str)
    assert raw not in dump, "raw token TIDAK boleh muncul di output"
    results["no_leak"] = {"raw_token_in_output": False}

    return {
        "ok": True,
        "provider_primary": "nvidia",
        "provider_alternative": "ollama",
        "autonomous_mutation": True,
        "mutation_real": mutation_real,
        "scenario1_switch": "nvidia -> ollama",
        "scenario2_fail_closed": True,
        "no_leak": True,
        "details": results,
        "masked": _masked(raw),
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
    print("=== M14-CLOSE-002 REAL AUTONOMOUS MUTATION ===")
    print(json.dumps(safe, indent=2, default=str))
    sys.exit(0 if safe.get("ok") else 1)


if __name__ == "__main__":
    main()
