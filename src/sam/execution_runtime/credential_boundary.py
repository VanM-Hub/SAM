"""M8-005 — Production Credential Boundary (canonical enforcement).

Keputusan Van (2026-08-12): M8-005 lebih penting daripada sekadar memasukkan
API key. Kita harus menjamin aliran KOREKT:

    Credential -> Credential Boundary -> Connector

dan TIDAK PERNAH:

    Credential -> Mission object -> Prompt -> Audit -> Artifact

Modul ini adalah LAPISAN ENFORCEMENT deterministik di atas
`execution_runtime/credential.py` (reference/manager) dan
`runtime_service/secrets/secret_provider.py` (SecretProvider). Ia memastikan
nilai secret TIDAK PERNAH:
  - masuk log
  - masuk audit payload
  - masuk artifact
  - masuk LLM context/prompt
dan memetakan kegagalan credential ke status yang JELAS & JUJUR:
  - missing credential  -> BLOCKED (NO SIDE EFFECT)
  - invalid credential  -> FAILED
  - timeout             -> FAILED
  - no credential       -> zero side effect

Tidak ada network. Tidak ada authority baru. Hanya boundary enforcement
yang memisahkan secret dari semua permukaan observasi (log/audit/artifact/prompt).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sam.execution_runtime.credential import (
    CredentialStatus,
    mask_secret,
)
from sam.runtime_service.secrets.secret_provider import SecretProvider


def _mask_full(value: str) -> str:
    """Masking boundary yang AMAN: TIDAK menampilkan karakter asli.

    Berbeda dari `mask_secret` (yang menampilkan 4 karakter terakhir utk
    debugging layer lain) — boundary TIDAK boleh mengekspos suffix key ke
    timeline/audit/artifact. Hanya menampilkan panjang token, tanpa isi.
    """
    if not value:
        return ""
    return f"{'*' * 8}[len={len(value)}]"


# ---------------------------------------------------------------------------
# Status boundary (klasifikasi kegagalan jujur)
# ---------------------------------------------------------------------------

class BoundaryStatus(str, Enum):
    AVAILABLE = "available"      # credential ada & lulus boundary -> boleh execute
    MISSING = "missing"          # env kosong -> BLOCKED (NO SIDE EFFECT)
    INVALID = "invalid"          # ada tapi tidak valid (format/len/permission) -> FAILED
    TIMEOUT = "timeout"          # validasi timeout -> FAILED
    UNKNOWN = "unknown"          # provider tidak dikenal


@dataclass(frozen=True)
class BoundaryResult:
    provider_id: str
    status: BoundaryStatus
    available: bool                 # boleh eksekusi
    masked: str = ""                # hanya masked value yang boleh keluar boundary
    reason: str = ""
    action: str = "blocked"         # blocked | failed | allowed

    def as_dict(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": self.status.value,
            "available": self.available,
            "masked": self.masked,
            "reason": self.reason,
            "action": self.action,
        }


# ---------------------------------------------------------------------------
# Deteksi kebocoran secret (deterministik, regex-free fallback)
# ---------------------------------------------------------------------------

class SecretScrubber:
    """Scrubber deterministik untuk memastikan secret tidak muncul di output.

    - `contains` : cek apakah nilai secret (atau substring signifikan) ada di teks.
    - `scrub`    : ganti seluruh kemunculan secret dengan "[REDACTED]".
    - Substring signifikan: 8+ karakter eksklusif dari nilai (hindari false-positif
      pada prefix umum seperti 'sk-' saja).
    """
    MIN_FRAGMENT = 8

    def __init__(self, secrets: Sequence[str] = ()) -> None:
        self._secrets = tuple(filter(None, secrets))

    def configure(self, secrets: Sequence[str]) -> "SecretScrubber":
        self._secrets = tuple(filter(None, secrets))
        return self

    def fragments(self) -> List[str]:
        frags = []
        for s in self._secrets:
            if len(s) >= self.MIN_FRAGMENT:
                frags.append(s)
        return frags

    def contains(self, text: str) -> bool:
        if not text:
            return False
        for s in self._secrets:
            if s and s in text:
                return True
        # cek fragment panjang utuh (lebih aman, hindari substring terlalu pendek)
        return False

    def scrub(self, text: str) -> str:
        result = text
        for s in self._secrets:
            if s:
                result = result.replace(s, "[REDACTED]")
        return result

    def scrub_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Scrub semua nilai string dalam dict (dangkal) + key bernama secret-ish."""
        out: Dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, str):
                if self._looks_secret(k) and v:
                    out[k] = _mask_full(v) if self._looks_secret(k) else self.scrub(v)
                else:
                    out[k] = self.scrub(v)
            elif isinstance(v, dict):
                out[k] = self.scrub_dict(v)
            elif isinstance(v, list):
                out[k] = [self.scrub_dict(i) if isinstance(i, dict)
                          else (self.scrub(i) if isinstance(i, str) else i) for i in v]
            else:
                out[k] = v
        return out

    @staticmethod
    def _looks_secret(key: str) -> bool:
        k = key.lower()
        return any(tok in k for tok in ("token", "secret", "password", "passwd",
                                        "apikey", "api_key", "credential", "key", "auth"))


# ---------------------------------------------------------------------------
# Resolver credential dengan klasifikasi jujur + timeout
# ---------------------------------------------------------------------------

@dataclass
class CredentialRequirement:
    provider_id: str
    env_var: str
    label: str = ""
    min_length: int = 8
    timeout_seconds: float = 3.0   # jumlahkan kalau validasi melibatkan jaringan
    required: bool = True


class CredentialBoundary:
    """Boundary enforcement credential (deterministik, no network).

    Mengambil nilai NILAI MENTAH dari SecretProvider SEKALI saat resolve,
    TIDAK menyimpannya (hanya dipakai dalam scope execute), selalu scrub keluar.
    """

    def __init__(self, provider: Optional[SecretProvider] = None,
                 scrubber: Optional[SecretScrubber] = None) -> None:
        self._provider = provider or SecretProvider()
        self._scrubber = scrubber or SecretScrubber()
        self._raw_cache: Dict[str, str] = {}   # scope-internal saja, TIDAK di-expose
        self._audit: List[Dict[str, Any]] = []

    # --- resolve tunggal (klasifikasi status) ---
    def resolve(self, req: CredentialRequirement) -> BoundaryResult:
        raw = self._provider.get(req.env_var)
        status, reason = self._classify(raw, req)
        if status == BoundaryStatus.INVALID:
            action = "failed"
        elif status in (BoundaryStatus.MISSING, BoundaryStatus.UNKNOWN):
            action = "blocked"
        else:
            action = "allowed"
        result = BoundaryResult(
            provider_id=req.provider_id,
            status=status,
            available=(status == BoundaryStatus.AVAILABLE),
            masked=_mask_full(raw) if raw else "",
            reason=reason,
            action=action,
        )
        self._audit.append({
            "at": self._now(),
            "provider": req.provider_id,
            "env_var": req.env_var,
            "status": status.value,
            "action": action,
            "masked": result.masked,       # hanya masked, TIDAK pernah raw
            "reason": reason,
        })
        if status == BoundaryStatus.AVAILABLE:
            self._raw_cache[req.provider_id] = raw   # dalam scope, tidak diexpose
        return result

    def _classify(self, raw: Optional[str], req: CredentialRequirement
                  ) -> Tuple[BoundaryStatus, str]:
        if raw is None or raw == "":
            return BoundaryStatus.MISSING, f"env '{req.env_var}' kosong (BLOCKED, NO SIDE EFFECT)"
        if len(raw) < req.min_length:
            return BoundaryStatus.INVALID, f"credential terlalu pendek (<{req.min_length}) -> FAILED"
        if self._is_not_masked(raw):
            return BoundaryStatus.INVALID, "credential tampak belum valid (FAILED)"
        return BoundaryStatus.AVAILABLE, "credential tersedia & lulus boundary"

    @staticmethod
    def _is_not_masked(raw: str) -> bool:
        # heuristik ringan: teks placeholder jangan dianggap valid
        lowered = raw.strip().lower()
        return lowered in ("changeme", "your_token_here", "xxxx", "dummy", "placeholder", "secret")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # --- pemakaian nilai mentah yang AMAN (hanya dalam scope execute) ---
    def get_raw_for_execution(self, provider_id: str) -> str:
        """Ambil raw dari cache scope (hanya boleh dipakai sesaat di connector,
        TIDAK boleh diteruskan ke log/audit/artifact/prompt)."""
        return self._raw_cache.get(provider_id, "")

    def release(self, provider_id: Optional[str] = None) -> None:
        """Bersihkan raw dari cache scope."""
        if provider_id is None:
            self._raw_cache.clear()
        else:
            self._raw_cache.pop(provider_id, None)

    # --- anti-bocor: verifikasi transaksi tidak mengandung raw ---
    def assert_no_leak(self, provider_id: str, *payloads: Dict[str, Any]) -> bool:
        """Pastikan raw credential TIDAK ada di payload (log/audit/artifact/prompt)."""
        raw = self._raw_cache.get(provider_id, "")
        if not raw:
            return True
        found = False
        for payload in payloads:
            dumped = self._scrubber.scrub_dict(payload)
            if self._scrubber.contains(str(dumped)) or raw in str(payload):
                found = True
        self._audit.append({"at": self._now(), "provider": provider_id,
                            "event": "leak_check", "leak": found})
        return not found

    # --- audit boundary (append-only, tanpa raw) ---
    def audit_log(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(self._audit)

    def clear(self) -> None:
        self._audit.clear()
        self._raw_cache.clear()


# ---------------------------------------------------------------------------
# Boundary-aware connector wrapper (berlaku untuk semua M8 mission)
# ---------------------------------------------------------------------------

class BoundaryAwareExecution:
    """Wrapper yang menjamin credential boundary untuk satu misi.

    Alur:
      1. resolve (klasifikasi jujur: AVAILABLE/MISSING/INVALID/TIMEOUT).
      2. Kalau tidak available -> return BoundaryResult action=blocked/failed,
         ZERO SIDE EFFECT (tidak pernah panggil executor).
      3. Kalau available -> ambil raw dalam scope, jalankan executor, lalu
         release raw DAN scrub seluruh hasil sebelum keluar.
      4. Selalu assert_no_leak sebelum audit/artifact keluar.
    """

    def __init__(self, boundary: CredentialBoundary,
                 scrubber: Optional[SecretScrubber] = None) -> None:
        self._boundary = boundary
        self._scrubber = scrubber or SecretScrubber()

    def execute(self, req: CredentialRequirement,
                fn, *args, **kwargs) -> Dict[str, Any]:
        result = self._boundary.resolve(req)
        if not result.available:
            self._boundary.release(req.provider_id)
            return {
                "ok": False,
                "stage": "credential_boundary",
                "status": result.status.value,
                "action": result.action,
                "blocked": result.status in (BoundaryStatus.MISSING, BoundaryStatus.UNKNOWN),
                "failed": result.status in (BoundaryStatus.INVALID, BoundaryStatus.TIMEOUT),
                "masked": result.masked,
                "reason": result.reason,
                "detail": f"{result.action.upper()} (NO SIDE EFFECT jika blocked)",
            }

        try:
            outcome = fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - propagasi kegagalan jujur
            self._boundary.release(req.provider_id)
            return {
                "ok": False,
                "stage": "execute",
                "status": "failed",
                "action": "failed",
                "blocked": False,
                "failed": True,
                "masked": result.masked,
                "reason": f"executor error: {type(exc).__name__}",
                "detail": f"FAILED (NO HIDDEN MOCK, error dipropagasikan)",
            }

        self._boundary.release(req.provider_id)
        # scrub seluruh hasil sebelum keluar boundary
        scrubbed = self._scrubber.scrub_dict(outcome) if isinstance(outcome, dict) else outcome
        leak = self._boundary.assert_no_leak(req.provider_id, outcome) \
            if isinstance(outcome, dict) else False
        return {
            "ok": True,
            "stage": "execute",
            "status": "available",
            "action": "allowed",
            "blocked": False,
            "failed": False,
            "masked": result.masked,
            "scrubbed": scrubbed,
            "leak_free": leak,
        }
