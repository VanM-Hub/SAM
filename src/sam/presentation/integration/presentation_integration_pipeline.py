"""Sprint 279 - Desktop Integration: pipeline (service, tanpa IO)."""
from __future__ import annotations

from dataclasses import dataclass

from ..certification import PresentationCertifier
from ..certification.presentation_cert_report import PresentationCertReport
from ..conversation.bridge import ConversationBridge
from ..dashboard_bridge.bridge import DashboardBridge
from ..foundation import PresentationContract
from ..monitoring.presentation_health import PresentationHealth
from ..monitoring.presentation_monitor import PresentationMonitor
from ..composition.presentation_pipeline import PresentationPipeline
from ..presentation_layer import PresentationLayer
from ..viewmodels.presentation_summary import PresentationSummary


@dataclass(frozen=True)
class PresentationIntegrationResult:
    """Hasil integrasi desktop (immutable, read-only)."""

    summary: PresentationSummary
    health: PresentationHealth
    cert_report: PresentationCertReport
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


class PresentationIntegrationPipeline:
    """Pipeline integrasi: verifikasi + sertifikasi (tanpa eksekusi)."""

    @staticmethod
    def run(
        runtime: PresentationLayer,
        contract: PresentationContract,
        conversation: ConversationBridge,
        dashboard: DashboardBridge,
    ) -> PresentationIntegrationResult:
        pipeline = PresentationPipeline()
        summary = runtime.snapshot_summary()
        health = PresentationMonitor.check(pipeline)
        dims = PresentationCertifier.validate_desktop(
            runtime=runtime,
            contract=contract,
            conversation=conversation,
            dashboard=dashboard,
        )
        cert = PresentationCertReport.from_list(dims)
        return PresentationIntegrationResult(
            summary=summary,
            health=health,
            cert_report=cert,
        )

    @staticmethod
    def certified(result: PresentationIntegrationResult) -> bool:
        return result.cert_report.passed and result.health.is_healthy()
