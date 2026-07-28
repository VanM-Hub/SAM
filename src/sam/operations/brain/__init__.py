"""
Brain Package — Operational Brain Foundation (Sprint 19-21).

Sprint 19 (v4.20.0): Observation -> Rules -> Analyzer -> Recommendation -> Proposal -> DTO
Sprint 20 (v4.22.0): +Scheduler, MultiSource, Correlation, Priority, Orchestrator,
                     ProposalQueue, Health, ConversationV2, IntegrationV2
Sprint 21 (v4.23.0): +PatternMiner, SuccessEstimator, Optimizer, FeedbackCollector,
                     LearningPipeline, DashboardBrainV2, Integration21, Validation21

Tidak mengubah Domain Layer, Repository, MissionController, Decision Engine,
Approval Engine, atau Conversation API. Semua output berupa DTO/Proposal,
tidak ada auto-execution.
"""

from __future__ import annotations

# -- Sprint 19 -- Foundation --------------------------------------------

from .observation_engine import ObservationEngine, ObservationSnapshot
from .rule_engine import RuleEngine, TriggeredRule, RuleDef
from .analyzer import OperationalAnalyzer, OperationalFinding, Severity
from .recommendation import RecommendationBuilder, MissionRecommendation
from .proposal import ProposalService, MissionProposal
from .conversation import BrainConversationBridge as BrainConversationBridgeV1
from .conversation import BrainConversationRequest, BrainConversationResponse
from .integration import BrainPipeline

# -- Sprint 20 -- Proactive Orchestration -------------------------------

from .scheduler import (
    ObservationScheduler,
    SchedulerConfig,
    SchedulerState,
    VersionedSnapshot,
    create_scheduler,
)
from .multi_source import (
    MultiSourceObserver,
    MultiSourceSnapshot,
    SourceResult,
    observe_all,
    observe_sources,
)
from .correlation import (
    CorrelationEngine,
    CorrelationDef,
    CorrelatedFinding,
    correlate_findings,
    build_finding_dict,
)
from .priority import (
    PriorityEngine,
    PriorityScore,
    PriorityCategory,
    PriorityConfig,
    prioritize,
    build_rec_for_priority,
)
from .orchestrator import (
    MissionOrchestrator,
    OperationalPackage,
    OrchestratorConfig,
    auto_orchestrate,
)
from .proposal_queue import (
    ProposalQueue,
    QueueItem,
    ProposalState,
    InvalidTransitionError,
    create_draft,
)
from .health import (
    OperationalHealthEngine,
    OperationalHealthDTO,
    DimensionHealth,
    evaluate_health,
)
from .conversation_v2 import (
    BrainConversationBridgeV2,
    ConversationContext,
    BrainQuery,
    BrainAnswer,
    QueryType,
    ask_brain_v2,
    classify_query,
)
from .integration_v2 import (
    ProactivePipeline,
    ProactivePipelineResult,
    run_proactive_pipeline,
    pipeline_summary,
)

# -- Sprint 21 -- Learning & Optimization -------------------------------

from .pattern_miner import (
    PatternMiner,
    PatternDiscoveryResult,
    OperationalRecord,
    DiscoveredPattern,
    discover_patterns,
    build_record,
)
from .success_estimator import (
    SuccessEstimator,
    SuccessEstimate,
    EvidencePiece,
    HistoricalOutcome,
    EstimatorConfig,
    estimate_success,
)
from .optimizer import (
    RecommendationOptimizer,
    OptimizerResult,
    OptimizationReport,
    optimize_recommendation,
    adjust_recommendations,
)
from .feedback_collector import (
    FeedbackCollector,
    FeedbackEvent,
    FeedbackSummary,
    collect_feedback,
)
from .learning_pipeline import (
    LearningPipeline,
    KnowledgeSnapshot,
    LearningPipelineResult,
    learn,
    create_knowledge_snapshot,
)
from .dashboard_brain import (
    DashboardBrainV2,
    DashboardStateV2,
    Insight,
    compute_dashboard,
)
from .integration21 import (
    LearningIntegration,
    LearningAndOptimizationResult,
    run_learning_integration,
)
from .validation21 import (
    Sprint21Validator,
    Sprint21ValidationResult,
    validate_sprint21,
)

__all__ = [
    # Sprint 19
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
    "BrainConversationBridgeV1",
    "BrainConversationRequest",
    "BrainConversationResponse",
    "BrainPipeline",
    # Sprint 20
    "ObservationScheduler",
    "SchedulerConfig",
    "SchedulerState",
    "VersionedSnapshot",
    "create_scheduler",
    "MultiSourceObserver",
    "MultiSourceSnapshot",
    "SourceResult",
    "observe_all",
    "observe_sources",
    "CorrelationEngine",
    "CorrelationDef",
    "CorrelatedFinding",
    "correlate_findings",
    "build_finding_dict",
    "PriorityEngine",
    "PriorityScore",
    "PriorityCategory",
    "PriorityConfig",
    "prioritize",
    "build_rec_for_priority",
    "MissionOrchestrator",
    "OperationalPackage",
    "OrchestratorConfig",
    "auto_orchestrate",
    "ProposalQueue",
    "QueueItem",
    "ProposalState",
    "InvalidTransitionError",
    "create_draft",
    "OperationalHealthEngine",
    "OperationalHealthDTO",
    "DimensionHealth",
    "evaluate_health",
    "BrainConversationBridgeV2",
    "ConversationContext",
    "BrainQuery",
    "BrainAnswer",
    "QueryType",
    "ask_brain_v2",
    "classify_query",
    "ProactivePipeline",
    "ProactivePipelineResult",
    "run_proactive_pipeline",
    "pipeline_summary",
    # Sprint 21
    "PatternMiner",
    "PatternDiscoveryResult",
    "OperationalRecord",
    "DiscoveredPattern",
    "discover_patterns",
    "build_record",
    "SuccessEstimator",
    "SuccessEstimate",
    "EvidencePiece",
    "HistoricalOutcome",
    "EstimatorConfig",
    "estimate_success",
    "RecommendationOptimizer",
    "OptimizerResult",
    "OptimizationReport",
    "optimize_recommendation",
    "adjust_recommendations",
    "FeedbackCollector",
    "FeedbackEvent",
    "FeedbackSummary",
    "collect_feedback",
    "LearningPipeline",
    "KnowledgeSnapshot",
    "LearningPipelineResult",
    "learn",
    "create_knowledge_snapshot",
    "DashboardBrainV2",
    "DashboardStateV2",
    "Insight",
    "compute_dashboard",
    "LearningIntegration",
    "LearningAndOptimizationResult",
    "run_learning_integration",
    "Sprint21Validator",
    "Sprint21ValidationResult",
    "validate_sprint21",
]
