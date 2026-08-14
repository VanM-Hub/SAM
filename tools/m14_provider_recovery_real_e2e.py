"""M14 Real E2E - Real Provider Recovery (M14-007) via Ollama lokal NYATA.

Membuktikan M14-007 terhadap provider NYATA: Ollama lokal (127.0.0.1:11434).

  - ProviderHealthProbe: probe health Ollama nyata (read-only via /api/tags).
  - ProviderRecovery:
      * Kasus A (REAL healthy): primary=ollama sehat -> failed=False,
        "primary healthy" (bukti probe real, TANPA recovery palsu).
      * Kasus B (failover delegated): primary dipaksa gagal via ping_fn False;
        alternatif = ollama (satu-satunya provider AVAILABLE di mesin ini) ->
        AutonomousRecoveryLoop dieksekusi dgn grant default OBSERVE+human ->
        TIDAK auto-approve -> honest (escalate/failed), membuktikan alur
        delegated + fail-closed tanpa sukses palsu.

JUJUR: mesin ini hanya punya 1 provider available (Ollama). Failover antar
provider BERBEDA tidak bisa diuji penuh di sini. Yang ter-buktikan REAL =
probe health provider + alur delegated loop + fail-closed honest.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from typing import Callable

import httpx

from sam.delegated_authority.real_provider_recovery import ProviderRecovery
from sam.providers.execution.provider_executor import (
    ProviderExecutionConfig,
    ProviderExecutor,
)

# Executor dgn 2 config valid (ollama + ollama_alt) keduanya menunjuk server
# Ollama nyata - supaya alternatif punya credentials/base_url (available=True).
_OLLAMA_BASE = "http://localhost:11434/v1"
def make_executor() -> ProviderExecutor:
    return ProviderExecutor(configs={
        "ollama": ProviderExecutionConfig(
            provider_id="ollama", base_url=_OLLAMA_BASE, api_key_env=""),
        "ollama_alt": ProviderExecutionConfig(
            provider_id="ollama_alt", base_url=_OLLAMA_BASE, api_key_env=""),
    })


def make_ping() -> Callable[[], bool]:
    """Buat ping_fn real ke Ollama (read-only)."""
    def ping() -> bool:
        try:
            r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:  # noqa: BLE001
            return False
    return ping


async def run_async() -> dict:
    result = {
        "milestone": "M14-007",
        "claim": "REAL_E2E_PROVIDER_RECOVERY",
        "environment": {
            "host": os.environ.get("COMPUTERNAME", "unknown"),
            "python": sys.version.split()[0],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
        "cases": {},
    }

    executor = make_executor()
    ping_ollama = make_ping()

    # ---------- Kasus A: primary sehat (REAL) ----------
    rec_a = ProviderRecovery(executor, probe_map={"ollama": ping_ollama})
    a = await rec_a.recover(
        primary="ollama",
        candidates=["ollama"],
        operation="chat",
        payload={"message": "ping", "model": "qwen2.5-coder:7b"},
    )
    result["cases"]["A_primary_healthy"] = a.as_dict()

    # ---------- Kasus B: primary dipaksa gagal -> failover delegated ----------
    probe_map_b = {"ollama": lambda: False}   # simulasi primary down utk probe
    # alternatif = ollama bila provokasi berubah sehat; tapi di sini probe sama,
    # jadi tidak ada alternatif sehat -> honest "no healthy alternative".
    rec_b = ProviderRecovery(executor, probe_map=probe_map_b)
    b = await rec_b.recover(
        primary="ollama",
        candidates=["ollama"],
        operation="chat",
        payload={"message": "ping", "model": "qwen2.5-coder:7b"},
    )
    result["cases"]["B_failover_delegated"] = b.as_dict()

    # Kasus C: failover nyata ke alternatif SEHAT (primary gagal di probe saja,
    # alternatif=ollama sehat). Ini membuktikan loop + authority + eksekusi
    # canonical menuju provider yang benar-benar hidup.
    # Kasus C: failover nyata ke alternatif SEHAT (primary gagal di probe saja,
    # alternatif=ollama_alt yg available & ping True -> menuju server hidup).
    probe_map_c = {"ollama": lambda: False, "ollama_alt": ping_ollama}
    rec_c = ProviderRecovery(executor, probe_map=probe_map_c)
    c = await rec_c.recover(
        primary="ollama",
        candidates=["ollama_alt"],
        operation="chat",
        payload={"message": "ping", "model": "qwen2.5-coder:7b"},
    )
    result["cases"]["C_failover_to_live_alt"] = c.as_dict()

    return result


def main() -> int:
    import asyncio
    result = asyncio.run(run_async())

    for key, cas in result["cases"].items():
        print(f"[{key}] failed={cas['failed']} reason={cas['failed_reason']!r} "
              f"switched_to={cas['switched_to']!r}")
        print("    probes:", [(p["provider_id"], p["available"], p["healthy"])
                              for p in cas["probes"]])
        oc = cas.get("outcome") or {}
        print("    outcome.reason:", oc.get("reason"))

    out_dir = "docs/engineering/state/M14"
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "M14_PROVIDER_RECOVERY_real_evidence.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Evidence saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
