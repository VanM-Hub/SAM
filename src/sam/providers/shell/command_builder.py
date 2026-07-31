"""Shell Command Builder — membangun command shell (preview).

Sprint 146 — Shell Provider.
Menyusun representasi command tanpa eksekusi. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ShellCommand:
    """Representasi command shell (immutable, tidak pernah dijalankan)."""
    command_id: str
    executable: str
    args: List[str] = field(default_factory=list)
    cwd: Optional[str] = None
    env: List[str] = field(default_factory=list)

    def render(self) -> str:
        """Reproduksi command sebagai string (preview, bukan eksekusi)."""
        parts = [self.executable] + list(self.args)
        return " ".join(parts)


class ShellCommandBuilder:
    """Builder command shell — deterministic, build-only."""

    def build(
        self,
        command_id: str,
        executable: str,
        args: List[str] = None,
        cwd: Optional[str] = None,
    ) -> ShellCommand:
        return ShellCommand(
            command_id=command_id,
            executable=executable,
            args=list(args or []),
            cwd=cwd,
        )
