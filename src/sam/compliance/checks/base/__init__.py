"""Base check framework — abstract base class, composite, context, and result."""

from .check_context import CheckContext
from .check_result import CheckResult
from .base_check import BaseComplianceCheck
from .composite_check import CompositeComplianceCheck, CompositeMode

__all__ = [
    "CheckContext",
    "CheckResult",
    "BaseComplianceCheck",
    "CompositeComplianceCheck",
    "CompositeMode",
]
