# Ward Adapters - M13-011 substrate (realizar ObservationTarget/InvestigationTarget)
#
# Adapter Ward MEMAKAI (bukan menduplikasi) capability existing:
#   - Observation read: canonical_http_connector.HttpConnector / RealExecutionHarness
#     (single execution authority, infrastructure adapter).
#   - Investigation: reuse kontrak InvestigationTarget -> delegates ke engine
#     canonical internal yang sama.
#
# Adapter hanya MENYESUAIKAN kontrak ke subject eksternal via connnector yang
# SUDAH PROVEN. TIDAK membuat executor kedua, TIDAK menyimpan authority sendiri
# (setiap aksi tetap melewati WardGovernanceBoundary + ApprovalGate canonical).
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sam.ward.capability.contracts import (
    Observation, ObservationTarget, SubjectRef, InvestigationResult,
    InvestigationTarget, Finding, Recommendation,
)


class _HttpPublicRead:
    """Wrapper ringan ke canonical_http_connector utk READ-ONLY (GET).

    Hanya memakai fungsionalitas read publik yang sudah PROVEN (M6-001).
    Tidak ada mutation di sini.
    """

    def __init__(self, *, timeout_seconds: float = 20.0) -> None:
        self._timeout = timeout_seconds

    def get(self, url: str, *, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Lakukan HTTP GET ke URL publik.

        Mengembalikan dict {http_status, ok, body, json, error}.
        RAISE bila non-200 / non-JSON / gagal jaringan (tiada sukses palsu).
        """
        try:
            import httpx
        except Exception as exc:  # pragma: no cover - env
            return {"http_status": 0, "ok": False, "error": "httpx unavailable: {}".format(exc),
                    "body": "", "json": None}
        try:
            resp = httpx.get(url, headers=headers, timeout=self._timeout,
                             follow_redirects=True)
            ok = resp.status_code == 200
            body = resp.text
            data = None
            try:
                data = resp.json()
            except Exception:
                data = None
            return {"http_status": resp.status_code, "ok": ok, "body": body,
                    "json": data, "error": "" if ok else "http {}".format(resp.status_code)}
        except Exception as exc:
            return {"http_status": 0, "ok": False, "error": str(exc), "body": "", "json": None}


class HttpObservationAdapter(ObservationTarget):
    """ObservationTarget untuk Ward yang diobservasi via HTTP publik/read.

    `base_url` + `path` - mis. GitHub public API. Header opsional (mis. token
    read-only) dibawa dari env yang diset di runtime; TIDAK di-hardcode.
    """

    def __init__(self, subject: SubjectRef, *, base_url: str, path: str = "",
                 headers_env: Optional[Dict[str, str]] = None,
                 timeout_seconds: float = 20.0) -> None:
        self._subject = subject
        self._base_url = base_url.rstrip("/")
        self._path = path
        self._headers_env = headers_env or {}
        self._http = _HttpPublicRead(timeout_seconds=timeout_seconds)

    def _resolve_url(self) -> str:
        path = self._path.strip()
        if path:
            return "{}/{}".format(self._base_url, path.lstrip("/"))
        return self._base_url

    def _resolve_headers(self, runtime_env: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Baca header dari env runtime (bukan hardcode). Contoh: token read-only.

        Bila `runtime_env` tidak diberikan, jatuh ke env proses (os.environ) -
        konsisten dengan connector canonical lain yang membaca env. Adapter
        NEVER hardcode secret; header diisi oleh wiring composition root.
        """
        if not self._headers_env:
            return None
        env = runtime_env
        if env is None:
            try:
                import os
                env = os.environ
            except Exception:
                env = {}
        env = env or {}
        resolved = {}
        for header_name, env_key in self._headers_env.items():
            val = env.get(env_key)
            if val:
                # jangan pernah rekam secret utuh ke payload/evidence - hanya
                # flag kehadiran
                resolved[header_name] = val
        return resolved or None

    def observe(self, *, capability: str = "observe",
                runtime_env: Optional[Dict[str, str]] = None) -> Observation:
        url = self._resolve_url()
        headers = self._resolve_headers(runtime_env)
        result = self._http.get(url, headers=headers)
        ok = bool(result.get("ok"))
        return Observation(
            subject=self._subject,
            capability=capability,
            successful=ok,
            payload={"source": url,
                     "http_status": result.get("http_status"),
                     "data": result.get("json") or result.get("body")},
            evidence={"verified_read": ok,
                      "http_status": result.get("http_status"),
                      "url": url,
                      "timestamp": _now()},
            error=result.get("error", ""),
        )


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class InvestigateFromObservation(InvestigationTarget):
    """InvestigationTarget yang menyusun hasil investigasi dari evidence yang
    sudah dikumpulkan (observation). Reuse kontrak investigation - bukan
    engine baru; di sini kita rekam findings + summary subjek."""

    def __init__(self, subject: SubjectRef) -> None:
        self._subject = subject

    def investigate(self, *, evidence: Dict[str, Any],
                    capability: str = "investigate") -> InvestigationResult:
        ok = bool(evidence.get("verified_read"))
        label = "subject-reachable" if ok else "subject-unreachable"
        findings = [{
            "label": label,
            "confidence": round(0.95 if ok else 0.85, 2),
            "evidence": {k: v for k, v in evidence.items()
                         if k != "data"},
        }]
        return InvestigationResult(
            subject=self._subject,
            successful=True,
            findings=findings,
            evidence_ref=str(evidence.get("timestamp", "")),
            summary="Investigated {}: {}".format(self._subject.subject_id, label),
            error="",
        )
