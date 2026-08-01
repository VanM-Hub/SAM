"""Sprint 279 - Desktop Integration: pipeline (service, tanpa IO)."""
from __future__ import annotations

from dataclasses import dataclass

from ..certification import DesktopCertifier
from ..certification.desktop_cert_report import DesktopCertReport
from ..conversation.bridge import ConversationBridge
from ..dashboard_bridge.bridge import DashboardBridge
from ..foundation import DesktopContract
from ..monitoring.desktop_health import DesktopHealth
from ..monitoring.desktop_monitor import DesktopMonitor
from ..runtime.desktop_pipeline import DesktopPipeline
from ..runtime.desktop_runtime import DesktopRuntime
from ..runtime.desktop_summary import DesktopSummary


@dataclass(frozen=True)
class DesktopIntegrationResult:
    """Hasil integrasi desktop (immutable, read-only)."""

    summary: DesktopSummary
    health: DesktopHealth
    cert_report: DesktopCertReport
    preview_only: bool = True

    def as_dict(self) -> dict:
        return {
            "summary": self.summary.as_dict(),
            "health": self.health.as_dict() if self.health is not None else None,
            "certification": (
                self.cert_report.as_dict()
                if self.cert_report is not None
                else None
            ),
            "preview_only": self.preview_only,
        }


class DesktopIntegrationPipeline:
    """Pipeline integrasi: verifikasi + sertifikasi (tanpa eksekusi)."""

    @staticmethod
    def run(
        runtime: DesktopRuntime,
        contract: DesktopContract,
        conversation: ConversationBridge,
        dashboard: DashboardBridge,
    ) -> DesktopIntegrationResult:
        pipeline = DesktopPipeline()
        summary = runtime.snapshot_summary()
        health = DesktopMonitor.check(pipeline)
        dims = DesktopCertifier.validate_desktop(
            runtime=runtime,
            contract=contract,
            conversation=conversation,
            dashboard=dashboard,
        )
        cert = DesktopCertReport.from_list(dims)
        return DesktopIntegrationResult(
            summary=summary,
            health=health,
            cert_report=cert,
        )

    @staticmethod
    def certified(result: DesktopIntegrationResult) -> bool:
        return result.cert_report.passed and result.health.is_healthy()
