"""
Sprint 24 — Operational Reasoning Runtime

brain/reasoning/
├── session.py        — OP-291: Reasoning Session Manager
├── context_builder.py — OP-292: Context Assembler
├── strategy.py       — OP-293: Prompt Strategy Engine
├── scheduler.py      — OP-294: Provider Scheduler
├── validator.py      — OP-295: Response Validator V2
├── pipeline.py       — OP-296: Reasoning Pipeline
├── conversation.py   — OP-297: Conversation Integration
├── dashboard_reasoning.py — OP-298: Dashboard Integration
"""

from .session import ReasoningSession, ReasoningContext, ReasoningHistory, SessionSnapshot, ReasoningRecord
from .context_builder import ContextAssembler, ObservationSnapshot, MissionDashboardDTO, BrainDashboardDTO, TimelineSummary, MissionSummary
from .strategy import StrategyEngine, ReasoningMode, PromptStrategy
from .scheduler import ProviderScheduler, ProviderSlot, CircuitBreaker
from .validator import ResponseValidator, ValidationReport, ValidationIssue
from .pipeline import ReasoningPipeline, PipelineResult
from .conversation import (
    ConversationReasoningIntegration,
    AskOperationalQuestion, AskMissionQuestion, AskHealthQuestion,
    AskEvidenceQuestion, AskRecommendationQuestion,
    ReasoningResult,
)
from .dashboard_reasoning import (
    DashboardReasoningService,
    ReasoningWidget, ProviderStatus, ReasoningStatus, ReasoningHistoryView,
)
