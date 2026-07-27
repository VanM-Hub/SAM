"""
Kategori aktivitas manusia — untuk Operator Context di OP-2.
"""

from enum import Enum


class HumanActivityCategory(str, Enum):
    """Kategori aktivitas yang dilakukan operator manusia."""

    # Observasi / Monitoring
    MONITORING = "monitoring"
    INSPECTION = "inspection"
    AUDIT = "audit"

    # Tindakan / Eksekusi
    EXECUTION = "execution"
    CONFIGURATION = "configuration"
    DEPLOYMENT = "deployment"

    # Diagnosa
    DIAGNOSE = "diagnose"
    INVESTIGATE = "investigate"
    ROOT_CAUSE = "root_cause"

    # Keputusan
    APPROVAL = "approval"
    REJECTION = "rejection"
    OVERRIDE = "override"

    # Komunikasi
    REPORT = "report"
    ESCALATION = "escalation"
    FEEDBACK = "feedback"

    # Pembelajaran
    LEARNING = "learning"
    EXPERIMENT = "experiment"
    TRAINING = "training"

    @classmethod
    def list_all(cls) -> list:
        return [c.value for c in cls]
