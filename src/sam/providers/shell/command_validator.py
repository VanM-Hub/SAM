"""Shell Command Validator — validasi command shell (deterministik).

Sprint 146 — Shell Provider.
Memvalidasi command tanpa eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .command_builder import ShellCommand

# Blokir command yang memicu eksekusi nyata (defensive, preview tetap 0)
BLOCKED_EXECUTABLES = {
    "exec", "system", "popen", "os.system", "subprocess",
    "sh", "bash", "cmd", "powershell", "eval",
}


@dataclass(frozen=True)
class ShellCommandValidation:
    """Hasil validasi command shell (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class ShellCommandValidator:
    """Validator command shell. Deterministik, build-only."""

    def validate(self, command: ShellCommand) -> ShellCommandValidation:
        issues = []
        if not command.command_id:
            issues.append("command_id required")
        if not command.executable:
            issues.append("executable required")
        if command.executable.lower() in BLOCKED_EXECUTABLES:
            issues.append(f"executable {command.executable} is forbidden (no-execution policy)")
        return ShellCommandValidation(valid=not issues, issues=issues)
