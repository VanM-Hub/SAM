"""
Brain Package — Operational Brain Foundation (Sprint 19, OP-241 to OP-250).

Pipeline: Observation → Rules → Analyzer → Recommendation → Proposal → DTO

Tidak mengubah Domain Layer, Repository, MissionController, Decision Engine,
Approval Engine, atau Conversation API. Semua output berupa DTO/Proposal,
tidak ada auto-execution.
"""

from __future__ import annotations

from .observation_engine import ObservationEngine, ObservationSnapshot
from .rule_engine import RuleEngine, TriggeredRule, RuleDef
from .analyzer import OperationalAnalyzer, OperationalFinding, Severity
from .recommendation import RecommendationBuilder, MissionRecommendation
from .proposal import ProposalService, MissionProposal
from .conversation import BrainConversationBridge, BrainConversationRequest, BrainConversationResponse
from .integration import BrainPipeline

__all__ = [
    "ObservationEngine",
    "ObservationSnapshot",
    "RuleEngine",
    "TriggeredRule",
    "RuleDef",
    "OperationalAnalyzer",
    "OperationalFinding",
    "Severity",
    "RecommendationBuilder",
    "MissionRecommendation",
    "ProposalService",
    "MissionProposal",
    "BrainConversationBridge",
    "BrainConversationRequest",
    "BrainConversationResponse",
    "BrainPipeline",
]
