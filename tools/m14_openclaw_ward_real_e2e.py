r"""M14 Real E2E — OpenClaw Ward terhadap runtime OpenClaw NYATA (gateway).

Menutup gap M14-CLOSE OpenClaw Ward real E2E (jembatan health.json -> runtime):

  Sebelumnya BLOCKED: collector hanya membaca file .openclaw/health.json
  (tak ada di mesin) lalu fallback simulated health (bukan bukti nyata).

  Sekarang: OpenClawHealthCollector mendukung gateway_url -> live HTTP GET
  <gateway>/health dari runtime OpenClaw nyata. Tool ini membuktikan SAM
  mengobserve health OpenClaw NYATA via runtime, bukan simulasi.

Alur (read-only, no mutation):
  - observe:  collector(gateway_url=<nyata>).collect(workspace) -> status
              runtime + komponen dari data gateway NYATA.
  - bukti:    collector.gateway_ok == True (sumber live, bukan simulated).
  - diagnose: OpenClawWard.diagnose() gabungan health (gateway nyata) + log
              (best-effort; bila tak ada log -> honest "unavailable").

Hasil = evidence + audit artifact (JSON di Real_E2E_M14/).

Cara pakai:
  python tools/m14_openclaw_ward_real_e2e.py [--gateway http://127.0.0.1:18789]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.openclaw.health import OpenClawHealthCollector
from sam.delegated_authority.real_openclaw_ward import OpenClawWard
from sam.openclaw.models import OpenClawStatus

DEFAULT_GATEWAY = "http://127.0.0.1:18789"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run(gateway: str, workspace: str) -> dict:
    started = time.time()

    collector = OpenClawHealthCollector(gateway_url=gateway)
    health = await collector.collect(workspace)
    gateway_ok = collector.gateway_ok

    # Ward diagnostic (read-only) — memakai collector yang sama (gateway nyata)
    ward = OpenClawWard(workspace, collector=collector)
    diag = await ward.diagnose()

    result = {
        "milestone": "M14-CLOSE",
        "item": "OpenClaw Ward real E2E (gateway bridge)",
        "timestamp": _now(),
        "gateway": gateway,
        "workspace": workspace,
        "evidence_source": "gateway-http" if gateway_ok else "fallback",
        "gateway_ok": gateway_ok,
        "runtime_status": health.runtime.value if health.runtime else "unknown",
        "components": [
            {"name": c.name, "status": c.status.value, "message": c.message}
            for c in health.components
        ],
        "diagnosis": {
            "runtime_status": diag.runtime_status,
            "component_issues": list(diag.component_issues),
            "log_issues": list(diag.log_issues),
            "detections": list(diag.detections),
            "healthy": diag.healthy,
        },
        "verdict": "PROVEN" if gateway_ok else "BLOCKED",
        "note": (
            "Sumber health NYATA dari runtime OpenClaw (gateway /health). "
            "Bukan simulated. Read-only, tanpa mutation."
            if gateway_ok else
            "Gateway tidak reachable -> dan bukan bukti real (jujur)."
        ),
        "elapsed_s": round(time.time() - started, 2),
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="M14 Real E2E OpenClaw Ward")
    ap.add_argument("--gateway", default=DEFAULT_GATEWAY,
                    help="Base URL gateway OpenClaw (default %(default)s)")
    ap.add_argument("--workspace", default=".",
                    help="Workspace path utk diagnosis (default cwd)")
    args = ap.parse_args()

    result = asyncio.run(run(args.gateway, args.workspace))

    out_dir = os.path.join(os.path.dirname(__file__), "..", "Real_E2E_M14")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "openclaw_ward_gateway_e2e.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\nEvidence:", out_path)
    return 0 if result["gateway_ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
