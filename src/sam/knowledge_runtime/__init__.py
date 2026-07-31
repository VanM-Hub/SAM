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
]
