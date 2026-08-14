"""M14-008 Real Credential Remediation — real E2E proof (NVIDIA provider).

Bukti jujur end-to-end:
  1) DETEKSI credential sehat (key owner valid  -> AVAILABLE, boleh eksekusi).
  2) DETEKSI credential rusak (env kosong      -> MISSING, BLOCKED, NO SIDE EFFECT).
  3) REMEDIASI NYATA: mendeteksi MISSING -> owner menyuplai nilai baru VALID
     (owner_supplied=True, keputusan pemilik) -> boundary SET -> verifikasi
     ulang -> AVAILABLE -> remediated=True. SAM TIDAK menebak secret.
  4) FAIL-CLOSED: remediasi TANPA otorisasi (owner_supplied=False, grant
     requires_human_approval=True) -> ESCALATED, TIDAK remediated (no self-grant).
  5) BUKTI TIDAK BOCOR: raw token TIDAK muncul di output.

Aturan M14: TIDAK mengubah credential tanpa CredentialBoundary; TIDAK
self-grant; jujur (no fake success).

Token dibaca dari env `NVIDIA_API_KEY` oleh shell pemanggil (SAME exec,
bukan hardcode file ini). Evidence JSON ditulis ke luar repo.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

# PYTHONPATH di-set oleh pemanggil; tambah guard bila gagal.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sam.delegated_authority.authority import DelegationGrant  # noqa: E402
from sam.delegated_authority.real_credential_remediation import (  # noqa: E402
    RealCredentialRemediation,
)
from sam.execution_runtime.credential import mask_secret  # noqa: E402
from sam.execution_runtime.credential_boundary import (  # noqa: E402
    BoundaryStatus,
    CredentialBoundary,
    CredentialRequirement,
    SecretScrubber,
)
from sam.runtime_service.secrets.secret_provider import SecretProvider  # noqa: E402


def _masked(token: str) -> str:
    return mask_secret(token)


def _has_any_secret_fragment(output_dump: str, raw: str) -> bool:
    """Bila raw ≥ 8 karakter utuh muncul di output -> bocor."""
    return bool(raw and len(raw) >= 8 and raw in output_dump)


async def run() -> dict[str, Any]:
    raw = os.environ.get("NVIDIA_API_KEY", "")
    if not raw or len(raw) < 20:
        return {
            "ok": False,
            "stage": "setup",
            "reason": "NVIDIA_API_KEY tidak tersedia di env (token belum di-supply)",
            "credential_status": "MISSING",
        }

    # Environment dikontrol (dict) agar remediasi NYATA bisa diverifikasi
    # via boundary tanpa menyentuh env proses global.
    env = dict(os.environ)
    # Hapus env token dari dict uji untuk memulai dari state "rutak/kosong".
    env.pop("NVIDIA_API_KEY", None)

    provider = SecretProvider(env=env)
    boundary = CredentialBoundary(provider=provider)
    rem = RealCredentialRemediation(boundary=boundary)

    results: dict[str, Any] = {}

    req = CredentialRequirement(
        provider_id="nvidia",
        env_var="NVIDIA_API_KEY",
        label="NVIDIA AI API key",
        min_length=20,
        required=True,
    )

    # --- 1) DETEKSI credential sehat (key owner valid di env) ---
    # Simulasikan key valid tersedia di env uji.
    env["NVIDIA_API_KEY"] = raw
    detected = rem.detect(req)
    results["detect_valid"] = {
        "status": detected.status.value,
        "available": detected.available,
        "action": detected.action,
        "reason": detected.reason,
    }
    assert detected.status == BoundaryStatus.AVAILABLE, "key valid harus AVAILABLE"

    # --- 2) REMEDIASI NYATA: kembalikan ke MISSING, lalu owner supply nilai baru ---
    env.pop("NVIDIA_API_KEY", None)               # jadi MISSING
    pre = rem.detect(req)                          # bukti status sebelum remediasi
    results["remediate_missing_pre"] = {
        "status": pre.status.value,
        "action": pre.action,
        "reason": pre.reason,
    }
    assert pre.status == BoundaryStatus.MISSING, "env kosong harus MISSING (BLOCKED)"

    remediated = await rem.remediate(
        req=req,
        grant=DelegationGrant(
            ward_id="nvidia",
            owner_id="van",
            allowed_mutations=("protect",),
            requires_human_approval=True,     # default fail-closed tetap dihormati
        ),
        new_value=raw,
        owner_supplied=True,                  # nilai dari pemilik, bukan SAM menebak
    )
    results["remediate_owner_supplied"] = {
        "detected_status": remediated.detected_status,
        "remediated": remediated.remediated,
        "verified_status": remediated.verified_status,
        "reason": remediated.reason,
        "phase": remediated.phase,
        "masked": remediated.masked,
    }
    assert remediated.remediated is True, \
        "remediasi owner-supplied harus berhasil (MISSING->AVAILABLE)"

    # --- 3) FAIL-CLOSED: remediasi TANPA otorisasi -> ESCALATED (bukan sukses) ---
    env.pop("NVIDIA_API_KEY", None)               # MISSING lagi, supaya logika remediasi jalan
    no_auth = await rem.remediate(
        req=req,
        grant=DelegationGrant(
            ward_id="nvidia",
            owner_id="van",
            allowed_mutations=("protect",),
            requires_human_approval=True,     # belum diizinkan owner
        ),
        new_value=raw,
        owner_supplied=False,                 # SAM tidak boleh self-grant
    )
    results["remediate_no_auth"] = {
        "remediated": no_auth.remediated,
        "phase": no_auth.phase,
        "reason": no_auth.reason,
    }
    assert no_auth.remediated is False, "tanpa otorisasi tidak boleh remediated (fail-closed)"

    # --- 4) DETEKSI key kosong -> MISSING (BLOCKED, NO SIDE EFFECT) ---
    empty_req = CredentialRequirement(
        provider_id="nvidia_empty",
        env_var="NVIDIA_API_KEY__EMPTY",
        min_length=20,
        required=True,
    )
    missing = rem.detect(empty_req)
    results["detect_empty"] = {
        "provider": missing.provider_id,
        "status": missing.status.value,
        "available": missing.available,
        "action": missing.action,
        "reason": missing.reason,
    }
    assert missing.status == BoundaryStatus.MISSING

    # --- 5) BUKTI TIDAK BOCOR: raw token TIDAK muncul di output ---
    dump = json.dumps(results, default=str)
    leaked = _has_any_secret_fragment(dump, raw)
    results["no_leak"] = {"raw_token_in_output": leaked}
    assert leaked is False, "raw token TIDAK boleh muncul di output"

    # --- audit boundary (append-only, tanpa raw) ---
    audit = boundary.audit_log()
    results["audit_entry_count"] = len(audit)

    return {
        "ok": True,
        "provider": "nvidia",
        "credential_status": "REMEDIATED (MISSING->AVAILABLE)",
        "remediated": True,
        "no_leak": True,
        "steps": results,
        "masked_preview": _masked(raw),
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

    # selalu scrub keluar (double safety)
    scrub = SecretScrubber(secrets=[raw])
    safe = scrub.scrub_dict(result)
    print("=== M14-008 REAL CREDENTIAL REMEDIATION ===")
    print(json.dumps(safe, indent=2, default=str))
    sys.exit(0 if safe.get("ok") else 1)


if __name__ == "__main__":
    main()
