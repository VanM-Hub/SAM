"""Compliance check framework — all check types, factory, and placeholder registry.

Package structure:
    base/         — BaseComplianceCheck, CompositeComplianceCheck, CheckContext, CheckResult
    registry/     — CheckRegistration (auto-registration into P1-002 engine)
    factory/      — CheckFactory (build checks from config)
    evidence/     — CheckEvidenceBuilder (CheckResult → ComplianceEvidence)
    filesystem/   — FileExistsCheck, FileAbsentCheck
    source/       — SourceContainsCheck, SourceAbsentCheck
    import_rules/ — ImportLegalCheck, ImportIllegalCheck
    lifecycle/    — LifecycleCheck
    traceability/ — TraceabilityCheck
    helpers/      — TestResultCheck

Provides:
    - 10 reusable checker types (framework)
    - Factory for config-driven check construction
    - Auto-registration into ComplianceRegistry
    - 99 placeholder checks (P1-001 baseline, no execution_fn)
"""

# -- Framework base -----------------------------------------------------------
from .base import (
    BaseComplianceCheck,
    CheckContext,
    CheckResult,
    CompositeComplianceCheck,
    CompositeMode,
)

# -- Framework registry -------------------------------------------------------
from .registry import CheckRegistration

# -- Framework factory --------------------------------------------------------
from .factory import CheckFactory, CheckFactoryError

# -- Framework evidence -------------------------------------------------------
from .evidence import CheckEvidenceBuilder

# -- Check types --------------------------------------------------------------
from .filesystem import FileExistsCheck, FileAbsentCheck
from .source import SourceContainsCheck, SourceAbsentCheck
from .import_rules import ImportLegalCheck, ImportIllegalCheck
from .lifecycle import LifecycleCheck
from .traceability import TraceabilityCheck
from .helpers import TestResultsCheck

# -- Placeholder registry (99 checks from P1-001) ----------------------------
from ._placeholders import register_placeholder_checks

# -- Auto-register all 10 check types with the factory ------------------------
def _auto_register_types():
    """Register all built-in check types with the CheckFactory."""
    try:
        CheckFactory.register_type("FileExistsCheck", FileExistsCheck)
        CheckFactory.register_type("FileAbsentCheck", FileAbsentCheck)
        CheckFactory.register_type("SourceContainsCheck", SourceContainsCheck)
        CheckFactory.register_type("SourceAbsentCheck", SourceAbsentCheck)
        CheckFactory.register_type("ImportLegalCheck", ImportLegalCheck)
        CheckFactory.register_type("ImportIllegalCheck", ImportIllegalCheck)
        CheckFactory.register_type("LifecycleCheck", LifecycleCheck)
        CheckFactory.register_type("TraceabilityCheck", TraceabilityCheck)
        CheckFactory.register_type("TestResultsCheck", TestResultsCheck)
    except CheckFactoryError:
        pass  # Already registered


_auto_register_types()

__all__ = [
    # Base
    "BaseComplianceCheck",
    "CheckContext",
    "CheckResult",
    "CompositeComplianceCheck",
    "CompositeMode",
    # Registry
    "CheckRegistration",
    # Factory
    "CheckFactory",
    "CheckFactoryError",
    # Evidence
    "CheckEvidenceBuilder",
    # Check types
    "FileExistsCheck",
    "FileAbsentCheck",
    "SourceContainsCheck",
    "SourceAbsentCheck",
    "ImportLegalCheck",
    "ImportIllegalCheck",
    "LifecycleCheck",
    "TraceabilityCheck",
    "TestResultsCheck",
    # Placeholder
    "register_placeholder_checks",
]
