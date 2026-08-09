"""Adaptive Governance Integration - MISSION-5.6.

Adaptive Governance adalah lapisan evaluasi/pembelajaran DI ATAS seluruh
capability SAM 5. Hanya menghasilkan Learning, Simulation, Impact, dan
Recommendation. Authority tetap di manusia.

IP-5.6-001: Universal Governance Orchestration (Learning foundation + Workspace).
IP-5.6-002: Universal Governance Policy Engine (Effectiveness Intelligence).
IP-5.6-003: Evidence & Decision Intelligence (Simulation).
IP-5.6-004: Compliance & Trust (Impact Assessment).
IP-5.6-005: Recommendation & Universal Governance Certification.
"""
from __future__ import annotations

# WP-01..10 - Learning Foundation
from .learning import (
    Correlation,
    ExperienceClassifier,
    ExperienceSample,
    LearningComplianceChecker,
    LearningContext,
    LearningDataset,
    LearningExplainability,
    LearningHistory,
    LearningHistoryEntry,
    LearningSource,
    OutcomeClass,
    OutcomeCorrelator,
    Pattern,
    PatternDetector,
)

# WP-11..20 - Effectiveness Intelligence
from .effectiveness import (
    EffectivenessAnalyzer,
    EffectivenessComplianceChecker,
    EffectivenessExplainability,
    EffectivenessMetric,
    EffectivenessRecommendation,
    EffectivenessRecommender,
    EffectivenessReport,
    FailurePattern,
    FailurePatternAnalyzer,
    GovernanceRisk,
    RiskAnalyzer,
    RiskLevel,
)

# WP-21..30 - Simulation
from .simulation import (
    GovernanceChangeProposal,
    SimulationComplianceChecker,
    SimulationContext,
    SimulationEngine,
    SimulationExplainability,
    SimulationResult,
    SimulationStatus,
    SimulationType,
)

# WP-31..40 - Impact Assessment
from .impact import (
    ImpactAnalyzer,
    ImpactAssessment,
    ImpactComplianceChecker,
    ImpactSeverity,
    ImpactTarget,
)

# WP-41..50 - Recommendation
from .recommendation import (
    AlternativeStrategy,
    ApprovalContext,
    ApprovalContextBuilder,
    EvidenceRef,
    GovernanceRecommendation,
    Prioritizer,
    RecommendationComplianceChecker,
    RecommendationEngine,
    RecommendationExplainability,
    RecommendationStatus,
    StrategyAnalyzer,
)

# WP-51..60 - Evolution Workspace
from .evolution_workspace import (
    EvolutionWorkspaceComplianceChecker,
    GovernanceEvolutionWorkspace,
    WorkspaceVisit,
)

# WP-61..70 - Certification
from .adaptive_certification import (
    AdaptiveCertEvidence,
    AdaptiveCertStatus,
    AdaptiveGovernanceCertification,
)

__all__ = [
    "Correlation", "ExperienceClassifier", "ExperienceSample",
    "LearningComplianceChecker", "LearningContext", "LearningDataset",
    "LearningExplainability", "LearningHistory", "LearningHistoryEntry",
    "LearningSource", "OutcomeClass", "OutcomeCorrelator", "Pattern",
    "PatternDetector",
    "EffectivenessAnalyzer", "EffectivenessComplianceChecker",
    "EffectivenessExplainability", "EffectivenessMetric",
    "EffectivenessRecommendation", "EffectivenessRecommender",
    "EffectivenessReport", "FailurePattern", "FailurePatternAnalyzer",
    "GovernanceRisk", "RiskAnalyzer", "RiskLevel",
    "GovernanceChangeProposal", "SimulationComplianceChecker",
    "SimulationContext", "SimulationEngine", "SimulationExplainability",
    "SimulationResult", "SimulationStatus", "SimulationType",
    "ImpactAnalyzer", "ImpactAssessment", "ImpactComplianceChecker",
    "ImpactSeverity", "ImpactTarget",
    "AlternativeStrategy", "ApprovalContext", "ApprovalContextBuilder",
    "EvidenceRef", "GovernanceRecommendation", "Prioritizer",
    "RecommendationComplianceChecker", "RecommendationEngine",
    "RecommendationExplainability", "RecommendationStatus", "StrategyAnalyzer",
    "EvolutionWorkspaceComplianceChecker", "GovernanceEvolutionWorkspace",
    "WorkspaceVisit",
    "AdaptiveCertEvidence", "AdaptiveCertStatus", "AdaptiveGovernanceCertification",
]
