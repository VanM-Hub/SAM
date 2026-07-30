"""Audit Logger — pencatat audit."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_security import AuditEntry


class AuditLogger:
    """Logger audit — preview-only."""

    def __init__(self) -> None:
        self._log: Dict[str, AuditEntry] = {}

    def log(self, entry: AuditEntry) -> None:
        self._log[entry.entry_id] = entry

    def get(self, entry_id: str) -> AuditEntry | None:
        return self._log.get(entry_id)

    def find_by_subject(self, subject: str) -> List[AuditEntry]:
        return [e for e in self._log.values() if e.subject == subject]

    def find_by_action(self, action: str) -> List[AuditEntry]:
        return [e for e in self._log.values() if e.action == action]

    def count(self) -> int:
        return len(self._log)

    def list_all(self) -> List[AuditEntry]:
        return list(self._log.values())
