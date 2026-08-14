"""Delegated Authority — M14 (SAM becomes useful).

Jembatan authority: menghubungkan delegated authority (Entrustment owner)
ke ApprovalGate canonical, TANPA menurunkan semantik approval, TANPA
executor kedua, TANPA bypass ApprovalGate.

Model referensi M14:
    Intent -> Subject -> Entrustment -> Observation -> Investigation
    -> Diagnosis -> Plan -> Policy -> Risk -> Evidence
    -> Autonomous Authority -> Guardrails -> ApprovalGate
    -> Canonical Execution -> Verification -> Audit -> Learning

M14 menambah SATU hal: apakah delegated authority mengizinkan approval
diberikan secara otomatis untuk tindakan ini. Semua keputusan eksekusi
tetap milik ApprovalGate + RealExecutionHarness (canonical).

Larangan M14 (dipertahankan di setiap lapisan):
    - TIDAK menghapus approval semantics.
    - TIDAK memberikan dirinya sendiri authority.
    - TIDAK menaikkan authority melalui learning.
    - TIDAK mengubah credential tanpa CredentialBoundary.
    - TIDAK mengeksekusi connector secara langsung.
    - TIDAK membuat executor kedua.
    - TIDAK melakukan mutation di luar Ward scope.
"""

from .authority import (
    AutonomousAuthority,
    AuthoritySource,
    AuthorityVerdict,
    DelegationGrant,
)
from .evaluation import AuthorityEvaluation
from .provider import DelegatedApprovalProvider
from .scope import ScopedAutonomy
from .escalation import AutomaticEscalation
from .recovery import AutonomousRecoveryLoop
from .real_provider_recovery import (
    ProviderProbe,
    ProviderHealthProbe,
    ProviderRecovery,
    ProviderRecoveryResult,
)
from .real_credential_remediation import (
    CredentialRemediationResult,
    RealCredentialRemediation,
)
from .real_openclaw_ward import (
    OpenClawWard,
    OpenClawWardResult,
    OpenClawDiagnosis,
)
from .real_windows_pc_ward import (
    WindowsPCWard,
    PCWardResult,
    PCDiagnosis,
    FileProbe,
)
from .real_word_investigation import (
    WordInvestigator,
    WordInvestigation,
)
from .real_pdf_investigation import (
    PDFPerformanceInvestigator,
    PDFPerformanceInvestigation,
)

__all__ = [
    "AutonomousAuthority",
    "AuthoritySource",
    "AuthorityVerdict",
    "DelegationGrant",
    "AuthorityEvaluation",
    "DelegatedApprovalProvider",
    "ScopedAutonomy",
    "AutomaticEscalation",
    "AutonomousRecoveryLoop",
    "ProviderProbe",
    "ProviderHealthProbe",
    "ProviderRecovery",
    "ProviderRecoveryResult",
    "CredentialRemediationResult",
    "RealCredentialRemediation",
    "OpenClawWard",
    "OpenClawWardResult",
    "OpenClawDiagnosis",
    "WindowsPCWard",
    "PCWardResult",
    "PCDiagnosis",
    "FileProbe",
    "WordInvestigator",
    "WordInvestigation",
    "PDFPerformanceInvestigator",
    "PDFPerformanceInvestigation",
]
