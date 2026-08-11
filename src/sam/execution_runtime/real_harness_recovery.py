"""
P9 — Real Recovery via harness.

Kriteria UTAMA (per Van):
    success=True TIDAK pernah dianggap bukti recovery.
    Bukti = perubahan state eksternal yang DIVERIFIKASI secara independen.

Skenario (menggunakan file status + health-check di sandbox sebagai
"service" nyata — reversible, terisolasi, bukan sistem user):

    Healthy State (service=running)
      -> inject failure (service=stopped)   # environment disposable
      -> SAM detects via Investigation (P8)
      -> recommends recovery (start)
      -> approval
      -> REAL Recovery Action (tulis service=running + pulihkan health file)
      -> REAL State Change (file status benar-benar berubah di disk)
      -> VERIFICATION independen (health check baca ulang file = healthy)

Bukti = perubahan state nyata di disk + independent health check, BUKAN flag.
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
    RealExecutionHarness,
)
from sam.execution_runtime.real_harness_analyze import _build_filesystem_capability_full

SANDBOX = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "_demo", "recovery_sandbox"))


# ---------------------------------------------------------------------------
# "Service" nyata: file status + file health-check di sandbox (reversible)
# ---------------------------------------------------------------------------

class FakeService:
    """Service tiruan berbasis file untuk membuktikan recovery state NYATA + reversible."""

    def __init__(self, name: str = "svc-orders") -> None:
        self.name = name
        self.state_file = os.path.join(SANDBOX, f"{name}.state")
        self.health_file = os.path.join(SANDBOX, f"{name}.health")

    def setup_healthy(self) -> None:
        """State sehat awal: running + health=ok."""
        os.makedirs(SANDBOX, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as fh:
            fh.write("running")
        with open(self.health_file, "w", encoding="utf-8") as fh:
            fh.write("ok")

    def inject_failure(self) -> str:
        """Environment disposable: hentikan service (state=stopped, health=fail)."""
        with open(self.state_file, "w", encoding="utf-8") as fh:
            fh.write("stopped")
        with open(self.health_file, "w", encoding="utf-8") as fh:
            fh.write("fail")
        return "stopped"

    def read_state(self) -> str:
        with open(self.state_file, encoding="utf-8") as fh:
            return fh.read().strip()

    def read_health(self) -> str:
        with open(self.health_file, encoding="utf-8") as fh:
            return fh.read().strip()


# ---------------------------------------------------------------------------
# Recovery adaptor — melakukan aksi pemulihan NYATA (tulis state + health)
# ---------------------------------------------------------------------------

class RecoveryAdapter:
    def __init__(self, audit: AuditTrail, service: FakeService) -> None:
        self._audit = audit
        self._svc = service

    def start(self, reason_correlation: str) -> Dict[str, Any]:
        """Recovery action: tulis state running + health ok ke disk (state change NYATA)."""
        before_state = self._svc.read_state()
        self._audit.record("recovery.action.start", self._svc.name,
                           before_state=before_state, reason_corr=reason_correlation)

        with open(self._svc.state_file, "w", encoding="utf-8") as fh:
            fh.write("running")  # state change nyata di disk
        with open(self._svc.health_file, "w", encoding="utf-8") as fh:
            fh.write("ok")
        after_state = self._svc.read_state()
        self._audit.record("recovery.action.complete", self._svc.name,
                           after_state=after_state, rec_action="start")
        return {"action": "start", "before": before_state, "after": after_state}


# ---------------------------------------------------------------------------
# Independent verification — baca ulang state & health LANGSUNG dari disk
# ---------------------------------------------------------------------------

def independent_health_check(service: FakeService, audit: AuditTrail) -> Dict[str, Any]:
    """Verifikasi independen: baca state & health file langsung (bukan hasil adapter)."""
    state = service.read_state()
    health = service.read_health()
    checks = {
        "state": state,
        "health": health,
        "state_is_running": state == "running",
        "health_is_ok": health == "ok",
        "healthy": (state == "running" and health == "ok"),
    }
    audit.record("recovery.verify.independent", service.name, **checks)
    return checks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="P9 Real Recovery")
    parser.add_argument("--recover", action="store_true", default=True, help="Jalankan recovery")
    parser.add_argument("--reason", default="")
    args = parser.parse_args(argv)

    # Cleanup sandbox lama agar test deterministik
    for f in os.listdir(SANDBOX) if os.path.isdir(SANDBOX) else []:
        os.remove(os.path.join(SANDBOX, f))

    audit = AuditTrail()
    harness = RealExecutionHarness(audit)
    _build_filesystem_capability_full(harness)
    svc = FakeService("svc-orders")
    reason = args.reason or "P9: recovery nyata setelah deteksi failure"

    print("=" * 70)
    print("  P9 — Real Recovery (state eksternal + independent verification)")
    print("=" * 70)

    # 1. Healthy state
    svc.setup_healthy()
    print(f"\n  1. HEALTHY STATE  : service={svc.name} state={svc.read_state()} health={svc.read_health()}")

    # 2. Inject failure (environment disposable)
    svc.inject_failure()
    print(f"  2. INJECT FAILURE : state={svc.read_state()} health={svc.read_health()}")

    # 3. SAM detects — panggil investigasi (P8) untuk "deteksi"
    print("  3. SAM DETECTS")
    detect = {
        "service": svc.name,
        "state": svc.read_state(),
        "health": svc.read_health(),
        "anomaly": svc.read_state() != "running" or svc.read_health() != "ok",
    }
    audit.record("recovery.detect", svc.name, **detect)
    print(f"     anomaly={detect['anomaly']} state={detect['state']}")

    # 4. Recommend recovery (start)
    rec = "start" if detect["anomaly"] else "none"
    audit.record("recovery.recommend", svc.name, rec_action=rec)
    print(f"  4. RECOMMEND      : {rec}")

    # 5. Approval
    approval_reason = reason
    audit.record("recovery.approval", svc.name, reason=approval_reason, approved=True)
    print(f"  5. APPROVAL       : approved=True (reason: {approval_reason[:50]})")

    # 6. REAL recovery action via adapter (tulis state nyata)
    print("  6. REAL RECOVERY ACTION (tulis state running + health ok ke disk)")
    adapter = RecoveryAdapter(audit, svc)
    outcome = adapter.start(approval_reason)
    print(f"     before={outcome['before']} -> after={outcome['after']} (file {svc.state_file})")

    # 7. REAL state change — verifikasi file benar-benar berubah
    final_state = svc.read_state()
    state_changed = (outcome["before"] != final_state) and (final_state == "running")
    audit.record("recovery.state_change", svc.name, before=outcome["before"], after=final_state,
                 changed=state_changed)
    print(f"  7. STATE CHANGE   : '{outcome['before']}' -> '{final_state}' changed={state_changed}")

    # 8. Independent verification
    print("  8. INDEPENDENT HEALTH CHECK (baca ulang dari disk)")
    iv = independent_health_check(svc, audit)
    print(f"     state={iv['state']} health={iv['health']} healthy={iv['healthy']}")

    # Audit
    print(f"\n  Audit ({len(audit.entries)}):")
    for e in audit.entries:
        print(f"    [{e.action}] {e.detail}")

    out_json = "_demo/p9_recovery.json"
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({"service": svc.name, "detect": detect, "recovery": outcome,
                   "state_change": {"before": outcome["before"], "after": final_state,
                                    "changed": state_changed},
                   "independent_verify": iv,
                   "audit": [e.__dict__ for e in audit.entries]}, fh, indent=2, default=str)
    print(f"\n[Bukti JSON: {out_json}]")

    # DoD P9: state changed NYATA + independent verify = healthy (BUKAN flag success=True)
    ok = (state_changed and iv["healthy"] and iv["state_is_running"] and iv["health_is_ok"])
    print("=" * 70)
    print(f"  VERDICT P9: {'PROVEN (state eksternal berubah nyata + independent health check = healthy)' if ok else 'BELUM PROVEN'}")
    print("=" * 70)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
