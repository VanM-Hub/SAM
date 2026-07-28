"""
DeploymentProvider — Observasi deployment.

Observation untuk menjawab:
  - Did deployment succeed?
  - What changed?
  - Should we rollback?
  - Did deployment affect runtime?

Saat ini: stateless — data dari metadata atau event eksternal.
Future: integrasi dengan deployment trigger.
"""

import structlog
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


logger = structlog.get_logger()


@dataclass
class DeploymentObservation:
    """Satu observasi deployment."""
    version: str
    status: str                 # success, failed, rollback, in_progress
    duration_seconds: float = 0.0
    initiator: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    changes: List[str] = field(default_factory=list)
    runtime_impact: List[str] = field(default_factory=list)

    def to_text(self) -> str:
        return "Deployment v{}: {} (by {}, {:.0f}s)".format(
            self.version, self.status, self.initiator, self.duration_seconds
        )


class DeploymentProvider:
    """Observasi deployment — dari metadata atau event.

    Saat ini: membaca dari environment atau data yang tersedia.
    Jika tidak ada data, mengatakan 'No deployment data available.'
    """

    def __init__(self):
        self._deployments: List[DeploymentObservation] = []
        self._read_metadata()

    def _read_metadata(self):
        """Baca metadata deployment yang tersedia."""
        try:
            from sam import __version__
            ver = __version__
        except (ImportError, AttributeError):
            ver = "unknown"

        # Simpan sebagai deployment awal
        deploy = DeploymentObservation(
            version=ver,
            status="success" if ver != "unknown" else "unknown",
            initiator="setup",
            changes=["Initial deployment v{}".format(ver)],
        )
        self._deployments.append(deploy)

    def record_deployment(self, version: str, status: str = "success",
                          initiator: str = "unknown",
                          changes: Optional[List[str]] = None):
        """Catat deployment baru secara manual."""
        deploy = DeploymentObservation(
            version=version,
            status=status,
            initiator=initiator,
            changes=changes or [],
        )
        self._deployments.append(deploy)
        logger.info("deployment_recorded", version=version, status=status)

    def get_latest(self) -> Optional[DeploymentObservation]:
        """Ambil deployment terbaru."""
        if not self._deployments:
            return None
        return self._deployments[-1]

    def get_all(self) -> List[DeploymentObservation]:
        """Semua deployment."""
        return self._deployments

    def get_summary(self) -> str:
        """Ringkasan status deployment."""
        if not self._deployments:
            return "No deployment data available."

        latest = self._deployments[-1]
        if latest.status == "failed":
            return "Latest deployment failed: v{} (by {})".format(latest.version, latest.initiator)
        elif latest.status == "rollback":
            return "Latest deployment rolled back: v{}".format(latest.version)
        elif latest.status == "in_progress":
            return "Deployment in progress: v{}".format(latest.version)
        return "Latest deployment successful: v{}".format(latest.version)
