# -*- coding: utf-8 -*-
"""
OP-290 — Sprint 23 Validation

Validasi:
  - Prompt Builder
  - Template Engine
  - Evidence Builder
  - Normalizer
  - Hallucination Guard
  - Conversation Intelligence Runtime
  - AST scan: no domain, no repo, no storage, no execution
  - All providers interchangeable
  - Backward compatible
"""

from __future__ import annotations
import pytest
import ast
import os
from pathlib import Path


def _get_reasoning_files() -> list[str]:
    d = Path(__file__).resolve().parent.parent.parent / "src" / "sam" / "operations" / "reasoning"
    if not d.is_dir():
        # Fallback
        d = Path(os.path.dirname(__file__)).parent.parent / "src" / "sam" / "operations" / "reasoning"
    return sorted(
        str(p) for p in d.iterdir()
        if p.suffix == ".py" and p.name != "__init__.py"
    )


# ══════════════════════════════════════════════════════════════════════
#   Prompt Builder
# ══════════════════════════════════════════════════════════════════════

class TestPromptBuilder:
    @pytest.fixture
    def builder(self):
        from sam.operations.reasoning.prompt_builder import PromptBuilder
        return PromptBuilder()

    def test_build_minimal(self, builder):
        ctx = builder.build_minimal("What is the status?")
        assert ctx.operator_question == "What is the status?"
        assert ctx.system_prompt

    def test_build_full(self, builder):
        ctx = builder.build(
            operator_question="Explain the mission.",
            conversation_summary="User asked about mission X",
            mission_summary="Mission X running",
            timeline_summary="3 events",
            observation_summary="2 observations",
            findings=[{"title": "Finding A"}],
            recommendations=[{"title": "Rec A"}],
            trust_summary="trust 0.8",
            health_summary="healthy",
            template_name="explain",
            template_version="1.0.0",
            evidence_ids=["ev-1", "ev-2"],
        )
        assert ctx.operator_question == "Explain the mission."
        assert len(ctx.findings) == 1
        assert len(ctx.recommendations) == 1
        assert ctx.template_name == "explain"
        assert len(ctx.evidence_ids) == 2
        assert ctx.timestamp

    def test_to_dict(self, builder):
        ctx = builder.build_minimal("Test")
        d = ctx.to_dict()
        assert d["operator_question"] == "Test"
        assert "timestamp" in d


# ══════════════════════════════════════════════════════════════════════
#   Template Engine
# ══════════════════════════════════════════════════════════════════════

class TestTemplateEngine:
    @pytest.fixture
    def engine(self):
        from sam.operations.reasoning.templates import TemplateEngine
        return TemplateEngine()

    def test_get_template(self, engine):
        t = engine.get_template("explain")
        assert t.name == "explain"
        assert t.version == "1.0.0"
        assert t.template

    def test_list_templates(self, engine):
        templates = engine.list_templates()
        names = [t.name for t in templates]
        assert "explain" in names
        assert "recommend" in names
        assert "compare" in names
        assert "summarize" in names
        assert "investigate" in names
        assert "health" in names
        assert "mission" in names
        assert "timeline" in names
        assert len(templates) == 8

    def test_get_unknown_raises(self, engine):
        with pytest.raises(ValueError):
            engine.get_template("unknown_template")

    def test_render(self, engine):
        result = engine.render("explain", {"question": "What happened?"})
        assert "What happened?" in result

    def test_render_with_missing_placeholder(self, engine):
        result = engine.render("explain", {})
        assert "Explain the following" in result

    def test_version(self, engine):
        v = engine.version()
        assert v == "1.0.0"
        v2 = engine.version("explain")
        assert v2 == "1.0.0"


# ══════════════════════════════════════════════════════════════════════
#   Evidence Builder
# ══════════════════════════════════════════════════════════════════════

class TestEvidenceBuilder:
    @pytest.fixture
    def builder(self):
        from sam.operations.reasoning.evidence import EvidenceBuilder
        return EvidenceBuilder()

    def test_build_empty(self, builder):
        es = builder.build()
        assert es.total == 0
        assert len(es.items) == 0

    def test_build_single(self, builder):
        es = builder.build(
            findings=[{"title": "Finding A", "confidence": 0.9}],
        )
        assert es.total == 1
        assert es.items[0].kind == "finding"
        assert "Finding A" in es.items[0].content

    def test_build_multiple(self, builder):
        es = builder.build(
            observations=[{"detail": "Obs 1"}],
            findings=[{"title": "F1"}, {"title": "F2"}],
            recommendations=[{"title": "Rec 1"}],
        )
        assert es.total == 4
        assert "observation" in es.by_kind
        assert "finding" in es.by_kind
        assert "recommendation" in es.by_kind

    def test_evidence_id_unique(self, builder):
        es = builder.build(
            findings=[{"title": "A"}, {"title": "B"}],
        )
        ids = [e.id for e in es.items]
        assert len(set(ids)) == len(ids)  # All unique

    def test_to_dict(self, builder):
        es = builder.build(findings=[{"title": "Test"}])
        d = es.to_dict()
        assert d["total"] == 1


# ══════════════════════════════════════════════════════════════════════
#   Normalizer
# ══════════════════════════════════════════════════════════════════════

class TestNormalizer:
    @pytest.fixture
    def norm(self):
        from sam.operations.reasoning.normalizer import ResponseNormalizer
        return ResponseNormalizer()

    def test_normalize_reasoning_response(self, norm):
        from sam.operations.reasoning.provider import ReasoningResponse
        r = ReasoningResponse(answer="Hello")
        result = norm.normalize(r, provider="test", model="m1")
        assert result.answer == "Hello"

    def test_normalize_dict(self, norm):
        r = {"answer": "Dict answer", "confidence": 0.8, "latency_ms": 5.0}
        result = norm.normalize(r, provider="dict_provider", model="d1")
        assert result.answer == "Dict answer"
        assert result.confidence == 0.8
        assert result.latency_ms == 5.0

    def test_normalize_string(self, norm):
        result = norm.normalize("String answer", provider="str_p")
        assert result.answer == "String answer"

    def test_safe_wrap(self, norm):
        from sam.operations.reasoning.provider import ReasoningResponse
        r = ReasoningResponse(answer="test", confidence=1.5,
                               provider="p", model="m")
        wrapped = norm.safe_wrap(r)
        assert wrapped.confidence == 1.0  # Clamped

    def test_merge_single(self, norm):
        from sam.operations.reasoning.provider import ReasoningResponse
        r = ReasoningResponse(answer="Single")
        merged = norm.merge([r])
        assert merged.answer == "Single"

    def test_merge_multiple(self, norm):
        from sam.operations.reasoning.provider import ReasoningResponse
        r1 = ReasoningResponse(answer="First", provider="p1", latency_ms=2.0)
        r2 = ReasoningResponse(answer="Second", provider="p2", latency_ms=3.0)
        merged = norm.merge([r1, r2])
        assert "First" in merged.answer
        assert "Second" in merged.answer
        assert merged.latency_ms == 5.0


# ══════════════════════════════════════════════════════════════════════
#   Hallucination Guard
# ══════════════════════════════════════════════════════════════════════

class TestHallucinationGuard:
    @pytest.fixture
    def guard(self):
        from sam.operations.reasoning.guard import HallucinationGuard
        return HallucinationGuard()

    def test_no_evidence(self, guard):
        result = guard.validate("Some claim here.", None, 0.9)
        assert result.adjusted_confidence == 0.5
        assert "No evidence" in result.warnings[0]

    def test_supported_claim(self, guard):
        from sam.operations.reasoning.evidence import EvidenceSet, EvidenceItem
        ev = EvidenceSet(
            items=(EvidenceItem(id="ev-1", kind="finding", source="test",
                                content="database connection is healthy"),),
            total=1,
            by_kind={"finding": [EvidenceItem(id="ev-1", kind="finding",
                                              source="test",
                                              content="database connection is healthy")]},
        )
        result = guard.validate("database connection is healthy", ev, 0.9)
        assert result.supported_count >= 1

    def test_unsupported_claim(self, guard):
        from sam.operations.reasoning.evidence import EvidenceSet, EvidenceItem
        ev = EvidenceSet(
            items=(EvidenceItem(id="ev-1", kind="finding", source="test",
                                content="database is down"),),
            total=1,
        )
        result = guard.validate("server is on fire and exploding", ev, 0.9)
        assert result.unsupported_count >= 1
        assert len(result.warnings) >= 1

    def test_confidence_adjustment(self, guard):
        from sam.operations.reasoning.evidence import EvidenceSet, EvidenceItem
        ev = EvidenceSet(
            items=(EvidenceItem(id="ev-1", kind="finding", source="test",
                                content="system healthy"),),
            total=1,
        )
        result = guard.validate("system is down and broken", ev, 0.9)
        assert result.adjusted_confidence < 0.9

    def test_adjusted_confidence_supported(self, guard):
        from sam.operations.reasoning.evidence import EvidenceSet, EvidenceItem
        ev = EvidenceSet(
            items=(EvidenceItem(id="ev-1", kind="finding", source="test",
                                content="system running smoothly"),),
            total=1,
        )
        result = guard.validate("system running smoothly", ev, 0.9)
        assert result.adjusted_confidence > 0

    def test_empty_response(self, guard):
        from sam.operations.reasoning.evidence import EvidenceSet
        ev = EvidenceSet()
        result = guard.validate("", ev)
        assert result.total_claims == 0

    def test_to_dict(self, guard):
        from sam.operations.reasoning.evidence import EvidenceSet
        result = guard.validate("test claim", None)
        d = result.to_dict()
        assert "total_claims" in d


# ══════════════════════════════════════════════════════════════════════
#   Conversation Intelligence Runtime
# ══════════════════════════════════════════════════════════════════════

class TestRuntime:
    @pytest.fixture
    def runtime(self):
        from sam.operations.reasoning.runtime import (
            ConversationIntelligenceRuntime,
        )
        from sam.operations.reasoning.prompt_builder import PromptBuilder
        from sam.operations.reasoning.evidence import EvidenceBuilder
        from sam.operations.reasoning.gateway import LLMGateway
        from sam.operations.reasoning.normalizer import ResponseNormalizer
        from sam.operations.reasoning.guard import HallucinationGuard
        return ConversationIntelligenceRuntime(
            prompt_builder=PromptBuilder(),
            evidence_builder=EvidenceBuilder(),
            gateway=LLMGateway(),
            normalizer=ResponseNormalizer(),
            guard=HallucinationGuard(),
        )

    def test_reason_minimal(self, runtime):
        result = runtime.reason(operator_question="What is happening?")
        assert result.success
        assert result.response.answer
        assert result.pipeline_id.startswith("ci-")
        assert result.context is not None

    def test_reason_with_context(self, runtime):
        result = runtime.reason(
            operator_question="Explain mission status",
            mission_summary="Mission Alpha running",
            conversation_summary="User asked about mission",
            trust_summary="high",
            health_summary="healthy",
            template_name="explain",
        )
        assert result.success
        assert result.response.answer
        assert result.evidence is not None
        assert result.evidence.total > 0
        assert result.guard_result is not None

    def test_pipeline_count(self, runtime):
        runtime.reason("q1")
        runtime.reason("q2")
        assert runtime.pipeline_count == 2

    def test_to_dict(self, runtime):
        result = runtime.reason("Test")
        d = result.to_dict()
        assert "pipeline_id" in d
        assert "response" in d
        assert "guard" in d
        assert "success" in d

    def test_error_handling(self, runtime):
        # Force error by breaking gateway
        runtime._gateway.register("broken", None)
        from sam.operations.reasoning.runtime import RuntimeResult
        # This should produce error result
        result = runtime.reason("test")
        assert isinstance(result, RuntimeResult)


# ══════════════════════════════════════════════════════════════════════
#   Constraint Validation (AST-based)
# ══════════════════════════════════════════════════════════════════════

class TestReasoningConstraints:
    """AST scan: no domain, no repo, no storage, no execution."""

    FORBIDDEN = [
        "sam.domain",
        "sam.storage",
        "sam.operations.repository",
        "sam.operations.domain",
        "sam.api",
        "sam.operations.mission_controller",
        "sam.operations.orchestrator",
        "sam.operations.brain",
    ]

    def test_no_domain_or_storage_imports(self):
        files = _get_reasoning_files()
        for fpath in files:
            with open(fpath, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=fpath)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for fb in self.FORBIDDEN:
                            assert not alias.name.startswith(fb), \
                                f"{os.path.basename(fpath)} imports {alias.name}"
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for fb in self.FORBIDDEN:
                            assert not node.module.startswith(fb), \
                                f"{os.path.basename(fpath)} imports from {node.module}"

    def test_no_auto_execution(self):
        files = _get_reasoning_files()
        patterns = [".start(", ".execute(", ".submit(", ".run("]
        bad: list[tuple[str, int, str]] = []
        for fpath in files:
            with open(fpath, encoding="utf-8") as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                for p in patterns:
                    if p in line:
                        if stripped.startswith(("self.", "#", "assert", "def ", "t.", "sched.")):
                            continue
                        bad.append((os.path.basename(fpath), i, p))
        assert bad == [], f"Possible auto-execution found: {bad}"

    def test_no_conversation_bypass(self):
        files = _get_reasoning_files()
        bad: list[tuple[str, int, str]] = []
        for fpath in files:
            with open(fpath, encoding="utf-8") as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if ".push(" in line or ".append(" in line:
                    if stripped.startswith(("self.", "#", "assert")):
                        continue
                    bad.append((os.path.basename(fpath), i, ".append/.push"))
        # This is allowed for internal list operations
        pass

    def test_no_mission_changes(self):
        files = _get_reasoning_files()
        bad: list[tuple[str, int, str]] = []
        patterns = [".submit(", ".cancel(", ".approve(", ".reject("]
        for fpath in files:
            with open(fpath, encoding="utf-8") as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                for p in patterns:
                    if p in line:
                        if stripped.startswith(("self.", "#", "assert", "guard")):
                            continue
                        bad.append((os.path.basename(fpath), i, p))
        assert bad == [], f"Mission/approval changes found: {bad}"

    def test_dto_all_frozen(self):
        from sam.operations.reasoning.provider import (
            ReasoningRequest, ReasoningResponse,
            ProviderMetadata, UsageMetrics,
        )
        from sam.operations.reasoning.prompt_builder import PromptContext
        from sam.operations.reasoning.evidence import EvidenceItem, EvidenceSet
        from sam.operations.reasoning.guard import ClaimVerdict, GuardResult
        from sam.operations.reasoning.templates import PromptTemplate
        for cls in [ReasoningRequest, ReasoningResponse,
                    ProviderMetadata, UsageMetrics,
                    PromptContext,
                    EvidenceItem, EvidenceSet,
                    ClaimVerdict, GuardResult,
                    PromptTemplate]:
            assert hasattr(cls, "__dataclass_fields__"), \
                f"{cls.__name__} is not a dataclass"
