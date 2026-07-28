"""
Sprint 23 — Conversation Intelligence & LLM Integration Layer (OP-281 – OP-290)

LLM adalah Reasoning Provider — bukan Domain, bukan Decision Maker.
LLM hanya menghasilkan reasoning berdasarkan evidence dari SAM.
Tidak ada akses storage, domain, repository, atau execution path.
"""

from __future__ import annotations

from .provider import (
    ReasoningProvider, ReasoningRequest, ReasoningResponse,
    ProviderMetadata, UsageMetrics,
)
from .gateway import (
    LLMGateway, MockProvider, OpenAIProvider, GeminiProvider,
    OllamaProvider, ClaudeProvider,
)
from .prompt_builder import PromptBuilder, PromptContext
from .templates import PromptTemplate, TemplateEngine
from .evidence import EvidenceBuilder, EvidenceSet, EvidenceItem
from .normalizer import ResponseNormalizer
from .guard import HallucinationGuard, ClaimStatus, ClaimVerdict
from .runtime import ConversationIntelligenceRuntime

__all__ = [
    "ReasoningProvider", "ReasoningRequest", "ReasoningResponse",
    "ProviderMetadata", "UsageMetrics",
    "LLMGateway", "MockProvider", "OpenAIProvider", "GeminiProvider",
    "OllamaProvider", "ClaudeProvider",
    "PromptBuilder", "PromptContext",
    "PromptTemplate", "TemplateEngine",
    "EvidenceBuilder", "EvidenceSet", "EvidenceItem",
    "ResponseNormalizer",
    "HallucinationGuard", "ClaimStatus", "ClaimVerdict",
    "ConversationIntelligenceRuntime",
]
