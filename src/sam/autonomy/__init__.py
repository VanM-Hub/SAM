"""Autonomous Runtime & Operational Safety — Sprint 32.

Components:
  - models: AutonomyLevel enum, shared data types
  - controller: dynamic autonomy level management
  - safety: bounded operational boundaries
  - guardrails: prevent unsafe autonomous actions
  - escalation: human escalation protocol
  - degradation: graceful autonomy degradation
  - assessment: before/after action evaluation
"""

from sam.autonomy.models import AutonomyLevel, AutonomyConfig
from sam.autonomy.controller import AutonomyController
from sam.autonomy.safety import SafetyEnvelope, SafetyBoundary
from sam.autonomy.guardrails import Guardrails, GuardrailRule, GuardrailResult
from sam.autonomy.escalation import EscalationManager, EscalationRequest
from sam.autonomy.degradation import GracefulDegradation
from sam.autonomy.assessment import SelfAssessment, AssessmentResult

__all__ = [
    "AssessmentResult",
    "AutonomyConfig",
    "AutonomyController",
    "AutonomyLevel",
    "EscalationManager",
    "EscalationRequest",
    "GracefulDegradation",
    "GuardrailResult",
    "GuardrailRule",
    "Guardrails",
    "SafetyBoundary",
    "SafetyEnvelope",
    "SelfAssessment",
]
