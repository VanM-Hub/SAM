"""Compliance engine protocol interface.

Defines the contract that any compliance engine must fulfill.
"""

from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from ..models.check_model import ComplianceCheck
from ..models.evidence import ComplianceEvidence
from ..models.finding import ComplianceFinding
from ..models.report import ComplianceReport
from ..models.verdict import ComplianceVerdict
from ..models.session_identity import SessionIdentity
from ..models.session_state import SessionState


@runtime_checkable
class CheckRunnerProtocol(Protocol):
    """Protocol for running compliance checks."""

    def run_check(self, check: ComplianceCheck) -> ComplianceEvidence:
        """Run a single check and return evidence."""
        ...

    def run_all(self) -> List[ComplianceEvidence]:
        """Run all registered checks and return all evidence."""
        ...


@runtime_checkable
class ComplianceRegistryProtocol(Protocol):
    """Protocol for the check registry."""

    def register(self, check: ComplianceCheck) -> None:
        """Register a compliance check."""
        ...

    def unregister(self, check_id: str) -> bool:
        """Unregister a check by ID. Returns True if removed."""
        ...

    def find(self, check_id: str) -> Optional[ComplianceCheck]:
        """Find a check by ID."""
        ...

    def list_all(self) -> List[ComplianceCheck]:
        """List all registered checks."""
        ...

    def list_by_level(self, level) -> List[ComplianceCheck]:
        """List checks by compliance level."""
        ...

    def list_by_category(self, category) -> List[ComplianceCheck]:
        """List checks by compliance category."""
        ...

    def count(self) -> int:
        """Return total number of registered checks."""
        ...


@runtime_checkable
class ComplianceEngineProtocol(Protocol):
    """Protocol for the main compliance engine."""

    def run_session(self, target_runtime: str, baseline_commit: str) -> ComplianceReport:
        """Run a complete compliance session against a target Runtime."""
        ...

    def get_state(self) -> SessionState:
        """Get current session state."""
        ...

    def get_identity(self) -> Optional[SessionIdentity]:
        """Get current session identity."""
        ...
