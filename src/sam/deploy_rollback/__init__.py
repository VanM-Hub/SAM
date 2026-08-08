"""
Deployment Rollback (H3/Program D — gap D3-G1).

Mekanisme rollback deployment terstandar: riwayat deployment ber-version,
pointer aktif, snapshot state deployment, dan rollback ke versi sebelumnya
yang deterministik & terverifikasi.

Stand-alone capability — TIDAK mengubah runtime existing (constraint EA-002).
Hanya mengelola metadata deployment; tidak melakukan efek eksternal.
"""
from .audit import DeploymentAuditLog, DeploymentAuditRecord
from .manifest import (
    CorruptDeploymentError,
    DeploymentIndex,
    DeploymentNotFound,
)
from .rollback import DeploymentManager
from .state import DeploymentSnapshot, DeploymentVersion

__all__ = [
    "CorruptDeploymentError",
    "DeploymentAuditLog",
    "DeploymentAuditRecord",
    "DeploymentIndex",
    "DeploymentManager",
    "DeploymentNotFound",
    "DeploymentSnapshot",
    "DeploymentVersion",
]
