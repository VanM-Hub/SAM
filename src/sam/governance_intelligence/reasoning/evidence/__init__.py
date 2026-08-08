"""WP-04 — Evidence Resolver (IP-3.1-001).

Pipeline: Question -> Evidence -> Answer -> Citation.

This module does NOT use AI. Per directive: NOT a LLM. Instead it uses
deterministic lookup rules (keyword mapping, section match, key match)
against an ``EvidenceRepository`` (WP-02). Each claim it produces is traced
back to the underlying knowledge items so a Citation can be generated.

Public methods (per directive):
    resolve(question) -> EvidenceChain
    trace(claim)      -> List[Citation]
    collect(claims)   -> EvidenceChain
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import EvidenceRepository, QueryOnlyRepository


@dataclass(frozen=True)
class Citation:
    """Single source attribution for a claim."""

    item_key: str
    source: str
    section: str
    title: str
    signature: str

    def public_dict(self) -> dict:
        return {
            "item_key": self.item_key,
            "source": self.source,
            "section": self.section,
            "title": self.title,
            "signature": self.signature,
        }


@dataclass(frozen=True)
class Claim:
    """A single fact derived from evidence. Carries its citations."""

    statement: str
    citations: List[Citation] = field(default_factory=list)
    confidence: float = 1.0

    def public_dict(self) -> dict:
        return {
            "statement": self.statement,
            "citations": [c.public_dict() for c in self.citations],
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class Answer:
    """Final deterministic answer to the question."""

    question: str
    claims: List[Claim] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {"question": self.question, "claims": [c.public_dict() for c in self.claims]}


@dataclass(frozen=True)
class EvidenceChain:
    """End-to-end deterministic output of the resolver."""

    question: str
    evidence: List[KnowledgeItem] = field(default_factory=list)
    answer: Optional[Answer] = None

    def public_dict(self) -> dict:
        return {
            "question": self.question,
            "evidence": [e.public_dict() for e in self.evidence],
            "answer": None if self.answer is None else self.answer.public_dict(),
        }


class EvidenceResolver:
    """WP-04 implementation. Read-only; uses repositories for everything."""

    def __init__(self, evidence_repo: EvidenceRepository) -> None:
        self._evidence_repo = evidence_repo

    # --- resolve: question -> evidence -> answer -------------------------
    def resolve(self, question: str) -> EvidenceChain:
        evidence = self._collect(question)
        answer = self._answer(question, evidence)
        return EvidenceChain(question=question, evidence=evidence, answer=answer)

    # --- collect: explicit claim(s) -> evidence ----------------------------
    def collect(self, claims: Sequence[str]) -> EvidenceChain:
        evidence: List[KnowledgeItem] = []
        for c in claims:
            evidence.extend(self._collect(c))
        answer = self._answer(" ".join(claims), evidence)
        return EvidenceChain(question=" ".join(claims), evidence=evidence, answer=answer)

    # --- trace: claim -> citations ----------------------------------------
    def trace(self, claim: str) -> List[Citation]:
        return [self._cite(it) for it in self._collect(claim)]

    # --- internal: collect evidence for a question/claim ------------------
    def _collect(self, text: str) -> List[KnowledgeItem]:
        text_low = text.lower()
        out: List[KnowledgeItem] = []
        seen: set = set()
        for it in self._evidence_repo.all():
            if (
                text_low in it.key.lower()
                or text_low in it.section.lower()
                or text_low in it.title.lower()
                or text_low in it.content.lower()
            ):
                if it.id not in seen:
                    seen.add(it.id)
                    out.append(it)
        return out

    # --- internal: deterministic answer from collected evidence ----------
    def _answer(self, question: str, evidence: Iterable[KnowledgeItem]) -> Answer:
        items = list(evidence)
        if not items:
            return Answer(question=question, claims=[])
        claims: List[Claim] = []
        for it in items:
            citations = [self._cite(it)]
            text = (it.content or it.section or it.title).strip().splitlines()[0] if (it.content or it.section) else it.title
            claims.append(Claim(statement=text, citations=citations, confidence=1.0))
        return Answer(question=question, claims=claims)

    @staticmethod
    def _cite(it: KnowledgeItem) -> Citation:
        return Citation(
            item_key=it.key,
            source=it.source,
            section=it.section,
            title=it.title,
            signature=it.signature,
        )
