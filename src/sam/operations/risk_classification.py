"""
Risk classification untuk semua execution capability.

5 levels: SAFE, LOW, MEDIUM, HIGH, CRITICAL.
Setiap level punya aturan approval, verification, audit, rollback.
"""

from dataclasses import dataclass
from typing import List
from enum import Enum


class RiskLevel(str, Enum):
    SAFE = "safe"          # Auto-approve, no human needed
    LOW = "low"            # Log only
    MEDIUM = "medium"      # Once approval + verification
    HIGH = "high"          # Always approval + verification + rollback
    CRITICAL = "critical"  # Always approval + always rollback + always audit


@dataclass(frozen=True)
class RiskRule:
    """Aturan untuk satu risk level.

    approval:
      auto      — tidak butuh approval
      once      — approve sekali untuk sesi ini
      always    — approve setiap kali
      escalate  — butuh approval lebih tinggi
    verification:
      auto      — otomatis berdasarkan metric
      evidence  — butuh bukti konkret
    rollback:
      none      — tidak ada rollback
      optional  — rollback jika mungkin
      required  — rollback wajib
    audit:
      log       — log ke console
      file      — simpan ke file
      detailed  — simpan dengan evidence lengkap
    """

    level: RiskLevel
    approval: str
    verification: str
    rollback: str
    audit: str
    can_auto_execute: bool
    requires_human: bool
    max_retries: int
    description: str


RISK_RULES = {
    RiskLevel.SAFE: RiskRule(
        level=RiskLevel.SAFE,
        approval="auto",
        verification="auto",
        rollback="none",
        audit="log",
        can_auto_execute=True,
        requires_human=False,
        max_retries=0,
        description="No side effects. Auto-execute. Log only.",
    ),
    RiskLevel.LOW: RiskRule(
        level=RiskLevel.LOW,
        approval="auto",
        verification="auto",
        rollback="none",
        audit="file",
        can_auto_execute=True,
        requires_human=False,
        max_retries=1,
        description="Minimal side effects. Auto-execute. File audit.",
    ),
    RiskLevel.MEDIUM: RiskRule(
        level=RiskLevel.MEDIUM,
        approval="once",
        verification="evidence",
        rollback="optional",
        audit="file",
        can_auto_execute=False,
        requires_human=False,
        max_retries=1,
        description="Moderate side effects. Once approval. Evidence verification.",
    ),
    RiskLevel.HIGH: RiskRule(
        level=RiskLevel.HIGH,
        approval="always",
        verification="evidence",
        rollback="required",
        audit="detailed",
        can_auto_execute=False,
        requires_human=True,
        max_retries=0,
        description="Major side effects. Always approval. Evidence verification. Rollback required.",
    ),
    RiskLevel.CRITICAL: RiskRule(
        level=RiskLevel.CRITICAL,
        approval="always",
        verification="evidence",
        rollback="required",
        audit="detailed",
        can_auto_execute=False,
        requires_human=True,
        max_retries=0,
        description="System-level impact. Always approval. Evidence verification. Rollback required. Escalation possible.",
    ),
}


def get_risk_rule(risk_level: RiskLevel) -> RiskRule:
    """Dapatkan aturan untuk satu risk level."""
    return RISK_RULES.get(risk_level, RISK_RULES[RiskLevel.MEDIUM])


# Capability → Risk mapping
CAPABILITY_RISK = {
    # Filesystem
    "free_disk_space": RiskLevel.LOW,
    "write_file": RiskLevel.MEDIUM,
    "delete_file": RiskLevel.HIGH,
    "backup_file": RiskLevel.LOW,
    "restore_file": RiskLevel.MEDIUM,
    # Command
    "execute_command": RiskLevel.CRITICAL,
    "restart_service": RiskLevel.HIGH,
    "scale_workers": RiskLevel.MEDIUM,
    "run_cleanup": RiskLevel.MEDIUM,
    "run_diagnostic": RiskLevel.LOW,
    # Process
    "restart_process": RiskLevel.HIGH,
    "kill_process": RiskLevel.CRITICAL,
    "start_process": RiskLevel.MEDIUM,
    "stop_process": RiskLevel.MEDIUM,
    # Workspace
    "clear_workspace_cache": RiskLevel.LOW,
    "archive_workspace_files": RiskLevel.LOW,
    "restore_workspace_snapshot": RiskLevel.HIGH,
    "recalculate_workspace_manifest": RiskLevel.LOW,
    # Network
    "test_connection": RiskLevel.SAFE,
    "reconnect_service": RiskLevel.MEDIUM,
    "flush_dns_cache": RiskLevel.LOW,
    # Database
    "restart_database": RiskLevel.CRITICAL,
    "reconnect_database_pool": RiskLevel.LOW,
    "vacuum_database": RiskLevel.MEDIUM,
}


def classify_risk(capability_id: str) -> RiskLevel:
    """Klasifikasikan satu capability."""
    return CAPABILITY_RISK.get(capability_id, RiskLevel.MEDIUM)


def get_risk_approval_type(capability_id: str) -> str:
    """Jenis approval yang dibutuhkan."""
    level = classify_risk(capability_id)
    return get_risk_rule(level).approval
