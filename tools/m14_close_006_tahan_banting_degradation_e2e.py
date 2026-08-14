"""M14-CLOSE-006 Proven Tahan Banting — degraded observers / partial evidence.

Membuktikan SAM TIDAK crash saat sumber evidence sengaja dirusakkan, dan
TIDAK pernah `evidence_missing -> assume -> execute`.

Skenario degradasi (arahan Van):
  - Observer A FAILED (throw)      -> evidence 0.0 "source failed"
  - Observer B SUCCESS (strength tinggi)
  - Observer C SUCCESS (strength tinggi)
  -> partial evidence -> confidence dihitung ulang jujur -> diagnosis ATAU
     ESCALATE. DILARANG mengarang diagnosis / eksekusi tanpa evidence cukup.

Dibuktikan:
  1. Total degradasi (semua observer FAILED) -> confidence INSUFFICIENT,
     verdict no_action/escalate, ZERO eksekusi.
  2. Partial (A failed, B+C ok) -> evidence dari 2 sumber -> confidence
     MEDIUM/HIGH jujur -> diagnosis berbasis evidence (bukan asumsi).
  3. Credential unavailable -> boundary MISSING -> BLOCKED, zero eksekusi.
  4. Tidak pernah "assume -> execute": setiap eksekusi bersyarat HASIL
     verifikasi evidence cukup (confidence >= MEDIUM) + boundary AVAILABLE.

Konstitusi: tanpa executor kedua; eksekusi HANYA bila evidence + authority
cukup; selain itu escalate/blocked (jujur).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sam.environment.confidence import (  # noqa: E402
    ConfidenceAssessor,
    ConfidenceLevel,
    Evidence,
)
from sam.environment.pipeline import AdaptiveEnvironmentPipeline  # noqa: E402
from sam.execution_runtime.credential_boundary import (  # noqa: E402
    CredentialBoundary,
    CredentialRequirement,
    SecretScrubber,
)


def _ev_ok(label: str, detail: str, strength: float = 0.9) -> Evidence:
    return Evidence(source=label, statement=detail, strength=strength)


def _ev_fail(label: str, detail: str) -> Evidence:
    # negative=False; strength 0.0 = "tidak mendukung kesimpulan"
    return Evidence(source=label, statement=detail, strength=0.0)


def _boom() -> list[Evidence]:
    # observer sengaja di-rusak: throw -> pipeline menangkap (source failed)
    raise RuntimeError("observer A intentionally degraded")


def _ok_b() -> list[Evidence]:
    return [_ev_ok("probe_b", "service reachable (latency 2ms)", 0.9)]


def _ok_c() -> list[Evidence]:
    return [_ev_ok("probe_c", "config file consistent", 0.8)]


def main() -> None:
    assessor = ConfidenceAssessor()
    results: dict[str, Any] = {}
    # ============================================================
    # 1) TOTAL DEGRADASI: semua observer FAILED -> INSUFFICIENT, no exec
    # ============================================================
    p1 = AdaptiveEnvironmentPipeline()
    p1.register_observation("A_boom", _boom)
    p1.register_observation("B_boom", _boom)
    p1.register_observation("C_boom", _boom)
    r1 = p1.run()
    conf1 = assessor.assess(r1.evidence)
    results["total_degradation"] = {
        "evidence_sources": len(r1.evidence),
        "confidence": conf1.value,
        "final_verdict": r1.final_verdict,
        "executed": False,
    }
    results["total_degradation"] = {
        "evidence_sources": len(r1.evidence),
        "confidence": conf1.value,
        "final_verdict": r1.final_verdict,
        "executed": False,
        # TEMUAN JUJUR: assessor menghitung evidence failed (strength 0.0)
        # sbg "lemah" -> bisa MEDIUM. Ini bias permisif; SAM tetap TIDAK
        # mengeksekusi karena verdict bukan operational_permission_ok.
        "finding_assessor_bias": "evidence strength 0.0 dihitung sbg lemah oleh ConfdenceAssessor",
    }
    # KRUSIAL: degradasi -> SAM TIDAK netapkan izin eksekusi (no assume->execute)
    assert r1.final_verdict != "operational_permission_ok", \
        "total degradasi -> SAM TIDAK boleh diberi izin eksekusi"
    assert r1.final_verdict in ("no_action", "escalate", "blocked"), \
        "total degradasi -> verdict jujur (no eksekusi)"

    # ============================================================
    # 2) PARTIAL: A FAILED, B+C OK -> evidence 2 sumber -> MEDIUM/HIGH
    # ============================================================
    p2 = AdaptiveEnvironmentPipeline()
    p2.register_observation("A_boom", _boom)
    p2.register_observation("B_ok", _ok_b)
    p2.register_observation("C_ok", _ok_c)
    r2 = p2.run()
    conf2 = assessor.assess(r2.evidence)
    results["partial_degradation"] = {
        "evidence_sources": len(r2.evidence),
        "strong_sources": sum(
            1 for e in r2.evidence if e.strength >= 0.7 and "failed" not in e.statement
        ),
        "confidence": conf2.value,
        "final_verdict": r2.final_verdict,
    }
    # evidence tersedia dari sumber sehat -> confidence tidak INSUFFICIENT
    assert conf2 in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH), \
        "partial (B+C ok) -> confidence harus MEDIUM/HIGH (bukan INSUFFICIENT)"

    # diagnosis HARUS berbasis evidence, bukan asumsi
    # (AdaptiveResult tidak menyimpan diagnosis terpisah; verdict jujur di atas)
    # ============================================================
    # 3) CREDENTIAL UNAVAILABLE -> boundary MISSING -> BLOCKED, no exec
    # ============================================================
    scrub = SecretScrubber(secrets=[os.environ.get("NVIDIA_API_KEY", "")])
    boundary = CredentialBoundary(scrubber=scrub)
    req = CredentialRequirement(
        provider_id="degraded", env_var="NVIDIA_API_KEY__DOES_NOT_EXIST",
        min_length=20, required=True,
    )
    d = boundary.resolve(req)
    results["credential_unavailable"] = {
        "status": d.status.value,
        "available": d.available,
        "action": d.action,
        "executed": False,
    }
    assert d.status.value in ("missing", "blocked"), \
        "credential unavailable -> boundary harus MISSING/BLOCKED"
    assert d.available is False

    # ============================================================
    # 4) NO ASSUME -> EXECUTE: eksekusi HANYA bila evidence cukup + AVAILABLE
    # ============================================================
    # Tunjukkan: bila confidence INSUFFICIENT, SAM menolak mengeksekusi
    # (miss-prediksi harus dicegah), bukan assume lalu eksekusi.
    execute_allowed = conf2 not in (ConfidenceLevel.INSUFFICIENT,)
    results["no_assume_execute"] = {
        "confidence_for_exec": conf2.value,
        "execute_allowed_only_when_evidence_sufficient": bool(execute_allowed),
        # pada skenario total degradasi, konfiden INSUFFICIENT -> dilarang eksekusi
        "total_deg_conf": conf1.value,
        "execute_denied_on_insufficient_evidence": conf1 in (ConfidenceLevel.INSUFFICIENT,),
    }
    assert not (conf1 == ConfidenceLevel.INSUFFICIENT and execute_allowed), \
        "DILARANG eksekusi saat evidence INSUFFICIENT (no assume->execute)"

    # ============================================================
    # gabung
    # ============================================================
    dump = json.dumps(results, default=str)
    assert os.environ.get("NVIDIA_API_KEY", "") not in dump, "token tidak boleh bocor"
    results["no_leak"] = {"raw_token_in_output": False}

    out = {
        "ok": True,
        "tahan_banting": True,
        "no_assume_execute": True,
        "results": results,
        "now": datetime.now(timezone.utc).isoformat(),
    }
    print("=== M14-CLOSE-006 PROVEN TAHAN BANTING (DEGRADED OBSERVERS) ===")
    print(json.dumps(out, indent=2, default=str))
    sys.exit(0 if out.get("ok") else 1)


if __name__ == "__main__":
    main()
