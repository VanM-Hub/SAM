"""Execution Metadata (Sprint 250).

Program C - Real Execution Runtime.
Immutable metadata captured at request / execution time.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ExecutionMetadata:
    """Metadata eksekusi (immutable)."""
    owner_id: str
    source_runtime: str = "execution"
    mode: str = "preview"  # preview | execute | rollback
    preview_only: bool = True
    approved: bool = False
    executed: bool = False
    rolled_back: bool = False
    external_calls: int = 0
    synchronous: bool = True
    determinism_check: bool = True
    audit_event: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "owner_id": self.owner_id,
            "source_runtime": self.source_runtime,
            "mode": self.mode,
            "preview_only": self.preview_only,
            "approved": self.approved,
            "executed": self.executed,
            "rolled_back": self.rolled_back,
            "external_calls": self.external_calls,
            "synchronous": self.synchronous,
            "determinism_check": self.determinism_check,
            "audit_event": self.audit_event,
        }
