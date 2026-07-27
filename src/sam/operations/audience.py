"""
AudienceProfile — Cara bercerita berbeda untuk manusia berbeda.

ConversationObject sama.
Yang berubah: verbosity, fokus, bahasa teknis.
"""

from dataclasses import dataclass, field
from typing import List


class AudienceType:
    ADMINISTRATOR = "administrator"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    OBSERVER = "observer"
    AUTOMATION = "automation"


@dataclass
class AudienceProfile:
    """Profil audiens — menentukan cara cerita disampaikan.

    BUKAN filter data.
    BUKAN akses kontrol.
    Hanya cara bercerita.
    """
    audience_type: str = AudienceType.ADMINISTRATOR
    verbosity: str = "normal"          # "brief" | "normal" | "detailed"
    technical_level: int = 1           # 1=low, 2=medium, 3=high
    default_focus: str = "status"      # "status" | "progress" | "technical" | "changes"
    show_predictions: bool = True
    show_evidence: bool = False
    show_technical: bool = False
    action_verbosity: str = "normal"   # "brief" | "normal" | "detailed"
    label: str = "Administrator"


# Profile defaults untuk setiap tipe
PROFILES = {
    AudienceType.ADMINISTRATOR: AudienceProfile(
        audience_type=AudienceType.ADMINISTRATOR,
        label="Administrator",
        verbosity="normal",
        technical_level=1,
        default_focus="status",
        show_predictions=True,
        show_evidence=False,
        show_technical=False,
        action_verbosity="normal",
    ),
    AudienceType.DEVELOPER: AudienceProfile(
        audience_type=AudienceType.DEVELOPER,
        label="Developer",
        verbosity="normal",
        technical_level=2,
        default_focus="progress",
        show_predictions=True,
        show_evidence=True,
        show_technical=True,
        action_verbosity="detailed",
    ),
    AudienceType.OPERATOR: AudienceProfile(
        audience_type=AudienceType.OPERATOR,
        label="Operator",
        verbosity="brief",
        technical_level=2,
        default_focus="status",
        show_predictions=True,
        show_evidence=False,
        show_technical=False,
        action_verbosity="normal",
    ),
    AudienceType.OBSERVER: AudienceProfile(
        audience_type=AudienceType.OBSERVER,
        label="Observer",
        verbosity="brief",
        technical_level=1,
        default_focus="status",
        show_predictions=False,
        show_evidence=False,
        show_technical=False,
        action_verbosity="brief",
    ),
    AudienceType.AUTOMATION: AudienceProfile(
        audience_type=AudienceType.AUTOMATION,
        label="Automation",
        verbosity="brief",
        technical_level=3,
        default_focus="status",
        show_predictions=False,
        show_evidence=False,
        show_technical=True,
        action_verbosity="brief",
    ),
}


def get_profile(audience_type: str) -> AudienceProfile:
    """Dapatkan profil audiens."""
    return PROFILES.get(audience_type, PROFILES[AudienceType.ADMINISTRATOR])
