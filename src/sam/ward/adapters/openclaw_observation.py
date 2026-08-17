# OpenClaw Observation Adapter - W1 (Ward Lab pertama)
#
# Setara EnvironmentObservationAdapter (R1-002), tapi untuk Ward OpenClaw.
# Prinsip Van #9 W1: "Gunakan existing real OpenClaw integration (M14) —
# Jangan membuat OpenClaw adapter kedua. Audit dan wire health->runtime hanya
# sejauh diperlukan."
#
# Adapter ini BUKAN integrasi OpenClaw kedua: ia MEMAKAI OpenClawHealthCollector
# (src/sam/openclaw/health.py, M14 canonical) sebagai sumber data, dan hanya
# MENYESUAIKAN hasilnya ke port `ObservationTarget` (ward.capability.contracts)
# yang sama dengan adapter environment lain. TIDAK membuat executor/engine baru.
#
# Read-only (produksi): observasi OpenClaw TIDAK mengubah state eksternal.
# Evidence = status komponen NYATA dari gateway health / .openclaw/health.json
# (bukan fixture). Bila tak tersedia -> honest NOT READY (bukan fake success).
from __future__ import annotations

import os
from typing import Optional

from sam.ward.capability.contracts import Observation, ObservationTarget, SubjectRef


def _default_workspace() -> str:
    """Workspace OpenClaw default (env override, lalu home .openclaw)."""
    override = os.environ.get("SAM_OPENCLAW_WORKSPACE")
    if override:
        return override
    return os.path.join(os.path.expanduser("~"), ".openclaw")


def _default_gateway() -> Optional[str]:
    """Gateway OpenClaw URL (env override; kosong -> file-based/simulated)."""
    return os.environ.get("SAM_OPENCLAW_GATEWAY") or None


class OpenClawObservationAdapter(ObservationTarget):
    """ObservationTarget utk Ward OpenClaw (read-only, W1).

    Membungkus OpenClawHealthCollector (M14 canonical) menjadi Observation
    dgn evidence status komponen NYATA + runtime_status.

    subject: SubjectRef(subject_type="ward", kind="application",
                        name="OpenClaw"), di-resolve oleh WardManager.

    Hasil:
      - payload : ringkasan komponen (name, status, message).
      - evidence: komponen nyata + runtime_status + workspace + gateway_used.
      - successful: True bila health terkumpul (gateway/file), False bila
        tak ada sumber nyata (honest NOT READY).
      - error   : deskripsi bila gagal total.
    """

    def __init__(self, subject: SubjectRef,
                 collector=None,
                 workspace: Optional[str] = None,
                 gateway_url: Optional[str] = None) -> None:
        self._subject = subject
        if collector is None:
            from sam.openclaw.health import OpenClawHealthCollector
            collector = OpenClawHealthCollector(
                gateway_url=gateway_url or _default_gateway())
        self._collector = collector
        self._workspace = workspace or _default_workspace()

    async def _collect(self):
        """Kumpulkan health OpenClaw (async collector M14)."""
        return await self._collector.collect(self._workspace)

    def observe(self, *, capability: str = "observe") -> Observation:
        # Collector M14 async; jalankan synchronous tanpa memicu DeprecationWarning.
        try:
            import asyncio
            try:
                health = asyncio.run(self._collect())
            except RuntimeError:
                # loop sedang berjalan (mis. dlm async context) -> jalankan di loop tsb.
                health = _asyncio_run_in_current_loop(self._collect())
        except Exception as exc:  # noqa: BLE001 - fail jujur, bukan sukses palsu
            return Observation(
                subject=self._subject,
                capability=capability,
                successful=False,
                payload={"error": str(exc), "component_count": 0,
                         "runtime_status": "unknown"},
                evidence={"verified_read": False, "component_count": 0,
                          "runtime_status": "unknown", "workspace": self._workspace,
                          "gateway_used": self._collector.gateway_ok},
                error="observasi OpenClaw gagal total: " + str(exc),
            )

        components = list(getattr(health, "components", None) or [])
        runtime = getattr(health, "runtime", None)
        runtime_status = getattr(runtime, "value", "unknown") if runtime else "unknown"

        comps = [
            {
                "name": getattr(c, "name", "unknown"),
                "status": getattr(c.status, "value", str(getattr(c, "status", "unknown"))),
                "message": getattr(c, "message", "") or "",
                "details": dict(getattr(c, "details", None) or {}),
            }
            for c in components
        ]

        ok = bool(components)  # ada komponen nyata dari gateway/file
        return Observation(
            subject=self._subject,
            capability=capability,
            successful=ok,
            payload={
                "component_count": len(comps),
                "components": comps,
                "runtime_status": runtime_status,
                "workspace": self._workspace,
                "gateway_used": self._collector.gateway_ok,
            },
            evidence={
                "verified_read": ok,
                "component_count": len(comps),
                "components": comps,
                "runtime_status": runtime_status,
                "workspace": self._workspace,
                "gateway_used": self._collector.gateway_ok,
                "timestamp": _utc_now(),
            },
            error="" if ok else "OpenClaw health tidak tersedia (workspace kosong / gateway unreachable) — NOT READY",
        )


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _asyncio_run_in_current_loop(coro):
    """Jalankan coroutine di loop yang sedang berjalan (async context).

    Fallback bila `asyncio.run` gagal karena loop aktif. HANYA dipakai dalam
    konteks sync adapter yg dipanggil dari jalur synchronous (runner);
    coroutine ringan (health collect) aman dijalankan di loop saat ini.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # loop sudah running (mis. handler FastAPI async). `run_until_complete`
        # TIDAK bisa dipakai -> jalankan coroutine di thread terpisah dgn loop
        # mandiri agar tidak berebut event loop yang sedang berjalan.
        import threading
        result = {}
        def _run():
            try:
                result["value"] = asyncio.run(coro)
            except Exception as exc:  # noqa: BLE001
                result["error"] = exc
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join()
        if "error" in result:
            raise result["error"]
        return result["value"]
    return loop.run_until_complete(coro)
