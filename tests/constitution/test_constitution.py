"""Constitution test suite — enforce Violations as code.

Menutup gap review B8: setiap Article di Constitution punya "Violations" tapi
tidak ada test yang menguatkannya. Satu test per Article (I-XVI), masing-masing
memetakan Prinsip ke properti yang bisa diverifikasi sebagai kode.

Catatan: beberapa Article bersifat deklaratif (XIII, XV) — test di sana
memastikan artefak kanonik ada & utuh, bukan meniru dokumen.
"""
from __future__ import annotations

import dataclasses
import importlib
import inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = ROOT / "docs" / "foundation" / "CONSTITUTION.md"


# --- Article I — Governance over Intelligence ------------------------------- #
def test_article_i_governance_exists():
    from sam.execution_runtime.approval_gate import ApprovalGate
    from sam.audit_runtime.foundation.audit_registry import AuditRegistry
    from sam.policy_runtime.foundation.policy_registry import PolicyRegistry
    assert ApprovalGate is not None
    assert AuditRegistry is not None
    assert PolicyRegistry is not None


# --- Article II — Trust is the Primary Output ------------------------------ #
def test_article_ii_immutable_dto():
    from sam.execution_runtime.approval_gate import ApprovalDecision
    assert dataclasses.is_dataclass(ApprovalDecision)
    assert ApprovalDecision.__dataclass_params__.frozen


# --- Article III — Capability is the Universal Language -------------------- #
def test_article_iii_capability_language():
    from sam.citizen.capability.models import CitizenCapability
    c = CitizenCapability.new("memory.lookup")
    assert c.capability_id.startswith("cap-")


# --- Article IV — Registry over Direct Dependency -------------------------- #
def test_article_iv_registry_wired():
    from sam.citizen.wiring import citizen_registry
    assert citizen_registry.count() > 0


# --- Article V — Approval before Execution --------------------------------- #
def test_article_v_no_execution_without_approval():
    from sam.execution_runtime.approval_gate import ApprovalGate
    from sam.execution_runtime.execution_request import ExecutionRequest
    gate = ApprovalGate()
    req = ExecutionRequest(execution_id="c1", provider_id="p", operation="op",
                           mode="execute", approved=False)
    assert gate.evaluate(req).approved is False
    assert gate.may_execute(req) is False


# --- Article VI — Immutable Contracts -------------------------------------- #
def test_article_vi_immutable_contracts():
    from sam.execution_runtime.approval_gate import ApprovalDecision
    from sam.citizen.descriptor.descriptor import CitizenDescriptor
    for cls in (ApprovalDecision, CitizenDescriptor):
        assert dataclasses.is_dataclass(cls)
        assert cls.__dataclass_params__.frozen


# --- Article VII — Deterministic by Default -------------------------------- #
def test_article_vii_deterministic_identity():
    from sam.citizen.identity.models import CitizenIdentity
    a = CitizenIdentity.new("runtime", "execution-runtime")
    b = CitizenIdentity.new("runtime", "execution-runtime")
    assert a.identity_id == b.identity_id


# --- Article VIII — Provider Agnostic -------------------------------------- #
def test_article_viii_governance_provider_agnostic():
    from sam.execution_runtime import approval_gate
    src = inspect.getsource(approval_gate).lower()
    for provider in ("openai", "anthropic", "gemini", "deepseek", "ollama",
                     "openclaw"):
        assert provider not in src


# --- Article IX — Runtime Independence ------------------------------------- #
def test_article_ix_runtime_independence_no_circular():
    importlib.import_module("sam.runtime_service.api")
    importlib.import_module("sam.execution_runtime.execution_engine")
    importlib.import_module("sam.mission_runtime.mission_runtime")


# --- Article X — Citizen Equality ------------------------------------------ #
def test_article_x_citizen_equality():
    from sam.citizen.wiring import citizen_registry
    from sam.citizen.identity.models import CitizenIdentity
    entries = citizen_registry.all()
    assert entries
    assert all(isinstance(e.identity, CitizenIdentity) for e in entries)


# --- Article XI — Audit Everything ----------------------------------------- #
def test_article_xi_audit_exists():
    from sam.audit_runtime.foundation.audit_registry import AuditRegistry
    assert AuditRegistry is not None


# --- Article XII — Separation of Responsibility ---------------------------- #
def test_article_xii_approval_does_not_execute():
    from sam.execution_runtime.approval_gate import ApprovalGate
    assert not hasattr(ApprovalGate, "execute")


# --- Article XIII — Evolution without Breaking Foundation ------------------ #
def test_article_xiii_constitution_present():
    assert CONSTITUTION.exists()


# --- Article XIV — Explainability before Optimization ---------------------- #
def test_article_xiv_explainability_basis():
    from sam.citizen.descriptor.descriptor import build_descriptor
    from sam.citizen.identity.models import CitizenIdentity
    d = build_descriptor(CitizenIdentity.new("runtime", "explainable"))
    assert d.basis  # descriptor membawa alasan/basis (explainable)


# --- Article XV — Constitution over Implementation ------------------------- #
def test_article_xv_constitution_canonical():
    text = CONSTITUTION.read_text(encoding="utf-8")
    assert "Canonical: true" in text
    assert "Article XVI" in text  # 16 Articles utuh


# --- Article XVI — Presentation Principle ---------------------------------- #
def test_article_xvi_presentation_has_no_business_logic():
    from sam.api.routes import ux as ux_mod
    src = inspect.getsource(ux_mod)
    assert "ExecutionEngine" not in src
    assert "execution_engine" not in src
    assert "execution_runtime" not in src
