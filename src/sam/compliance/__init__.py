"""Compliance package — compliance engine for verifying Runtime implementations.

This package implements the Compliance Engine defined in P1-002
based on the Compliance Suite framework (P1-001).

The engine is independent of the target Runtime per ADR-006.
It does NOT contain individual checker implementations — those
are registered through the registry as callable check functions.
"""

from .models import (
    ComplianceLevel,
    ComplianceCategory,
    Severity,
    FindingClassification,
    EvidenceType,
    SessionState,
    VerdictGrade,
    ComplianceVerdict,
    ComplianceCheck,
    ComplianceEvidence,
    ComplianceFinding,
    LevelSummary,
    CategorySummary,
    ComplianceReport,
    SessionIdentity,
)
from .registry.check_registry import ComplianceRegistry
from .engine.runner import ComplianceRunner
from .engine.compliance_engine import ComplianceEngine
from .reporters.text_reporter import TextReporter
from .lifecycle.session_lifecycle import SessionLifecycle
from .validation.engine_validator import EngineValidator

__all__ = [
    # Models
    "ComplianceLevel",
    "ComplianceCategory",
    "Severity",
    "FindingClassification",
    "EvidenceType",
    "SessionState",
    "VerdictGrade",
    "ComplianceVerdict",
    "ComplianceCheck",
    "ComplianceEvidence",
    "ComplianceFinding",
    "LevelSummary",
    "CategorySummary",
    "ComplianceReport",
    "SessionIdentity",
    # Core
    "ComplianceRegistry",
    "ComplianceRunner",
    "ComplianceEngine",
    # Supporting
    "TextReporter",
    "SessionLifecycle",
    "EngineValidator",
]
