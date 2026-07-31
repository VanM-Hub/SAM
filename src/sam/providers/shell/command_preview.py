"""Shell Command Preview — preview command tanpa eksekusi.

Sprint 146 — Shell Provider.
Menghasilkan preview eksekusi (simulasi). Tidak menjalankan apa pun.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .command_builder import ShellCommand


@dataclass(frozen=True)
class ShellPreview:
    """Preview eksekusi command (immutable)."""
    command_id: str
    command_text: str
    preview: bool = True
    executed: bool = False
    external_calls: int = 0
    notes: List[str] = field(default_factory=list)


class ShellCommandPreview:
    """Preview command shell — external_calls selalu 0."""

    def preview(self, command: ShellCommand) -> ShellPreview:
        return ShellPreview(
            command_id=command.command_id,
            command_text=command.render(),
            preview=True,
            executed=False,
            external_calls=0,
            notes=["dry-run: no execution performed"],
        )
