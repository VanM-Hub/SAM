"""Knowledge Validator — validasi model knowledge (Sprint 181).

Phase XVIII — Knowledge Runtime.
validate, validate_fact, validate_relation, validate_context. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .knowledge_record import KnowledgeRecord
from .knowledge_fact import KnowledgeFact
from .knowledge_relation import KnowledgeRelation
from .knowledge_context import KnowledgeContext


@dataclass(frozen=True)
class KnowledgeValidation:
    """Hasil validasi knowledge (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class KnowledgeValidator:
    """Validator model knowledge. Deterministik."""

    def validate(self, record: KnowledgeRecord) -> KnowledgeValidation:
        issues = []
        if not record.record_id:
            issues.append("record_id required")
        if not record.knowledge_id:
            issues.append("knowledge_id required")
        return KnowledgeValidation(valid=not issues, issues=issues)

    def validate_fact(self, fact: KnowledgeFact) -> KnowledgeValidation:
        issues = []
        if not fact.fact_id:
            issues.append("fact_id required")
        if not fact.subject:
            issues.append("subject required")
        return KnowledgeValidation(valid=not issues, issues=issues)

    def validate_relation(self, relation: KnowledgeRelation) -> KnowledgeValidation:
        issues = []
        if not relation.relation_id:
            issues.append("relation_id required")
        if not relation.source_id:
            issues.append("source_id required")
        return KnowledgeValidation(valid=not issues, issues=issues)

    def validate_context(self, context: KnowledgeContext) -> KnowledgeValidation:
        issues = []
        if not context.context_id:
            issues.append("context_id required")
        return KnowledgeValidation(valid=not issues, issues=issues)
