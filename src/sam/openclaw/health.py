"""
OpenClaw Health Collector — Phase 1

Membaca health OpenClaw (worker, gateway, provider, runtime).
Integrasi dengan Telemetry Service SAM.
"""

import structlog
from typing import List, Dict, Any, Optional
from .models import OpenClawHealth, OpenClawStatus, OpenClawComponent

logger = structlog.get_logger()


class OpenClawHealthCollector:
    """Collector health OpenClaw — membaca status komponen runtime OpenClaw."""

    def __init__(self):
        self._last_health: Optional[OpenClawHealth] = None

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

        Saat ini simulated, akan diganti dengan actual health check ke OpenClaw API.
        """
        # Simulasi — nanti akan baca actual health
        # 1. Cek apakah ada file .openclaw/health.json
        import json
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

        # Fallback: simulated health
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
