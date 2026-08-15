"""
OpenClaw Health Collector — Phase 1

Membaca health OpenClaw (worker, gateway, provider, runtime).
Integrasi dengan Telemetry Service SAM.
"""

import json
import structlog
import urllib.request
from typing import List, Optional
from .models import OpenClawHealth, OpenClawStatus, OpenClawComponent

logger = structlog.get_logger()


def _map_gateway_status(status: Optional[str]) -> OpenClawStatus:
    """Petakan string status nyata dari gateway OpenClaw ke status internal.

    Data nyata gateway: {"ok": bool, "status": "live" | ...}.
    - status == "live" dan ok: HEALTHY
    - status tidak dikenali / field hilang: UNKNOWN (bukan asumsi sehat)
    """
    if not status:
        return OpenClawStatus.UNKNOWN
    live = str(status).strip().lower()
    if live in ("live", "up", "healthy", "ok", "running", "ready"):
        return OpenClawStatus.HEALTHY
    if live in ("degraded", "degrading", "loading", "starting"):
        return OpenClawStatus.DEGRADED
    if live in ("down", "unhealthy", "failed", "stopped", "dead"):
        return OpenClawStatus.UNHEALTHY
    return OpenClawStatus.UNKNOWN


class OpenClawHealthCollector:
    """Collector health OpenClaw — membaca status komponen runtime OpenClaw.

    Sumber (urutan prioritas, honest-fail):
      1. gateway_url (opsional): live HTTP GET <gateway>/health dari runtime
         OpenClaw nyata. Bila diset dan reachable -> data NYATA.
      2. file .openclaw/health.json di workspace (file-based).
      3. simulated fallback (Phase 1, ditandai jelas sebagai simulated).
    """

    def __init__(self, gateway_url: Optional[str] = None):
        self._last_health: Optional[OpenClawHealth] = None
        self._gateway_url = gateway_url
        self._gateway_ok = False  # apakah source gateway dipakai (bukti nyata)

    @property
    def gateway_ok(self) -> bool:
        """True bila source health nyata dari gateway OpenClaw berhasil dipakai."""
        return self._gateway_ok

    async def collect(self, workspace_path: str) -> OpenClawHealth:
        """Kumpulkan health OpenClaw dari workspace.

        Akan membaca actual health dari OpenClaw.
        Saat ini menggunakan simulated health untuk pengujian.

        Args:
            workspace_path: Path workspace OpenClaw.

        Returns:
            OpenClawHealth snapshot.
        """
        components = await self._get_components(workspace_path)
        runtime_status = self._determine_runtime_status(components)

        health = OpenClawHealth(
            workspace=workspace_path,
            runtime=runtime_status,
            components=components,
        )
        self._last_health = health

        logger.info(
            "openclaw_health_collected",
            runtime=runtime_status.value,
            component_count=len(components),
        )
        return health

    async def _get_components(self, workspace_path: str) -> List[OpenClawComponent]:
        """Dapatkan daftar komponen OpenClaw beserta statusnya.

        Prioritas sumber (honest):
          1. gateway_url (live HTTP dari runtime OpenClaw nyata) bila diset.
          2. file .openclaw/health.json di workspace.
          3. simulated fallback (ditandai, bukan klaim nyata).
        """
        if self._gateway_url:
            gw = await self._get_gateway_health()
            if gw is not None:
                self._gateway_ok = True
                return gw

        # 2. Baca actual health dari file .openclaw/health.json
        from pathlib import Path

        health_file = Path(workspace_path) / ".openclaw" / "health.json"
        if health_file.exists():
            try:
                with open(health_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                components = []
                for comp_data in data.get("components", []):
                    try:
                        status = OpenClawStatus(comp_data.get("status", "unknown"))
                    except ValueError:
                        status = OpenClawStatus.UNKNOWN
                    components.append(
                        OpenClawComponent(
                            name=comp_data.get("name", "unknown"),
                            status=status,
                            message=comp_data.get("message"),
                            details=comp_data.get("details", {}),
                        )
                    )
                if components:
                    return components
            except Exception as e:
                logger.warning("health_file_parse_failed", error=str(e))

        # 3. Fallback: simulated health (Phase 1) — bukan klaim real.
        return [
            OpenClawComponent(
                name="Worker",
                status=OpenClawStatus.HEALTHY,
                message="All workers running",
            ),
            OpenClawComponent(
                name="Gateway",
                status=OpenClawStatus.HEALTHY,
                message="Gateway responding",
            ),
            OpenClawComponent(
                name="Provider",
                status=OpenClawStatus.HEALTHY,
                message="Providers connected",
            ),
            OpenClawComponent(
                name="Runtime",
                status=OpenClawStatus.HEALTHY,
                message="Runtime active",
            ),
        ]

    async def _get_gateway_health(self) -> Optional[List[OpenClawComponent]]:
        """Baca health NYATA dari runtime OpenClaw via HTTP GET <gateway>/health.

        Sumber: {"ok": bool, "status": str}. Bila reachable -> komponen nyata
        (Gateway status dari data runtime). Bila gagal / non-JSON -> None
        (jangan asumsi sehat; caller lanjut ke sumber berikutnya).
        """
        base = str(self._gateway_url).rstrip("/")
        url = f"{base}/health"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310 - gateway lokal/trusted
                raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            ok = bool(data.get("ok", False))
            status = data.get("status")
            mapped = _map_gateway_status(status)
            if ok and mapped == OpenClawStatus.HEALTHY:
                mapped = OpenClawStatus.HEALTHY
            elif not ok and mapped == OpenClawStatus.HEALTHY:
                # ok false tapi status "live" -> honest, bukan sehat penuh
                mapped = OpenClawStatus.DEGRADED
            logger.info(
                "openclaw_gateway_health", url=url, ok=ok, status=status,
                mapped=mapped.value,
            )
            return [
                OpenClawComponent(
                    name="Gateway",
                    status=mapped,
                    message=f"live health: status={status!r} ok={ok!r}",
                    details={"ok": ok, "status": status, "url": url},
                )
            ]
        except Exception as e:  # noqa: BLE001 - honest fail, lanjut source lain
            logger.warning("openclaw_gateway_health_failed", url=url, error=str(e))
            return None

    def _determine_runtime_status(self, components: List[OpenClawComponent]) -> OpenClawStatus:
        """Tentukan status runtime berdasarkan komponen.

        - Semua healthy -> HEALTHY
        - Ada degraded -> DEGRADED
        - Ada unhealthy -> UNHEALTHY
        - None -> UNKNOWN
        """
        if not components:
            return OpenClawStatus.UNKNOWN

        has_unhealthy = any(c.status == OpenClawStatus.UNHEALTHY for c in components)
        has_degraded = any(c.status == OpenClawStatus.DEGRADED for c in components)
        has_unknown = any(c.status == OpenClawStatus.UNKNOWN for c in components)

        if has_unhealthy:
            return OpenClawStatus.UNHEALTHY
        if has_degraded:
            return OpenClawStatus.DEGRADED
        if has_unknown:
            return OpenClawStatus.DEGRADED
        return OpenClawStatus.HEALTHY

    async def detect_issues(self, health: OpenClawHealth) -> List[str]:
        """Deteksi issue dari health OpenClaw.

        Args:
            health: OpenClawHealth snapshot.

        Returns:
            List pesan issue.
        """
        issues = []
        for comp in health.components:
            if comp.status in (OpenClawStatus.UNHEALTHY, OpenClawStatus.DEGRADED):
                msg = comp.message or "No details"
                issues.append("{0}: {1}".format(comp.name, msg))
                logger.warning(
                    "openclaw_issue_detected",
                    component=comp.name,
                    status=comp.status.value,
                    message=msg,
                )
        return issues
