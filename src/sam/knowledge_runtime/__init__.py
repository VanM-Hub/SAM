"""Knowledge Runtime — Phase XVIII.

Knowledge Runtime mengelola deskripsi, model, builder, runtime, catalog,
monitoring, sertifikasi — deterministik, tanpa inferensi, no write.
"""
from .foundation import (
    KnowledgeDescriptor,
    KnowledgeCapability,
    KnowledgeContract,
    KnowledgeContractCompliance,
    KnowledgeMetadata,
    KnowledgeRegistry,
    KnowledgeRegistrySummary,
    ConversationKnowledgeBridge,
    DashboardKnowledgeBridge,
)
from .dashboard import ExecutionCard
from .model import (
    KnowledgeRecord,
    KnowledgeFact,
    KnowledgeRelation,
    KnowledgeContext,
    KnowledgeTag,
    KnowledgeValidator,
    KnowledgeValidation,
    ConversationModelBridge,
    DashboardModelBridge,
)
from .builder import (
    KnowledgeBuilder,
    KnowledgeBuildResult,
    FactBuilder,
    RelationBuilder,
    ContextBuilder,
    PreviewBuilder,
    KnowledgePreviewDTO,
    ConversationBuilderBridge,
    DashboardBuilderBridge,
)

__all__ = [
    "KnowledgeDescriptor",
    "KnowledgeCapability",
    "KnowledgeContract",
    "KnowledgeContractCompliance",
    "KnowledgeMetadata",
    "KnowledgeRegistry",
    "KnowledgeRegistrySummary",
    "ConversationKnowledgeBridge",
    "DashboardKnowledgeBridge",
    "ExecutionCard",
    "KnowledgeRecord",
    "KnowledgeFact",
    "KnowledgeRelation",
    "KnowledgeContext",
    "KnowledgeTag",
    "KnowledgeValidator",
    "KnowledgeValidation",
    "ConversationModelBridge",
    "DashboardModelBridge",
    "KnowledgeBuilder",
    "KnowledgeBuildResult",
    "FactBuilder",
    "RelationBuilder",
    "ContextBuilder",
    "PreviewBuilder",
    "KnowledgePreviewDTO",
    "ConversationBuilderBridge",
    "DashboardBuilderBridge",
]
