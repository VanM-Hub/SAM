# -*- coding: utf-8 -*-
"""Test M5 - Canonical Agent Governance (universal_agent -> RealExecutionHarness).

Membuktikan agent bertindak HANYA lewat canonical governed execution
(RealExecutionHarness) — bukan memegang adapter sendiri. Contract
`universal_agent.AgentInteractionContract` diserap sebagai kontrak canonical.

Cara jalan:
    python -m pytest tests/execution_runtime/test_m5_canonical_agent_governance.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.execution_runtime.canonical_agent_governance import (
    CanonicalAgentContract,
    RealCanonicalAgent,
    build_agent,
    from_universal_agent_contract,
)
from sam.execution_runtime.real_harness import (
    AuditTrail,
    RealExecutionHarness,
)


@pytest.fixture()
def harness_with_tool():
    h = RealExecutionHarness(audit=AuditTrail())
    from sam.execution_runtime.canonical_tool_contract import (
        TOOL_KIND_READ,
        build_tool_contract,
        contract_to_registry_dict,
    )

    c = build_tool_contract(
        tool_id="agent_tool", contract_id="ct-agent-tool",
        supported_kinds=(TOOL_KIND_READ,),
        entry_points=("read", "meta"),
        requires_approval=True, requires_governance=True,
    )
    h.register_capability("tool", contract_to_registry_dict(c), c.to_contract_dict(), "ALLOW")
    return h


def test_m5_from_universal_agent_contract_dict():
    """Serap kontrak agent universal_agent (dict / objek) -> canonical."""
    legacy = {"agent_id": "a1", "contract_id": "ct-a1", "capabilities": ["read"], "governed": True}
    cc = from_universal_agent_contract(legacy)
    assert cc is not None
    assert cc.allows("read")
    assert not cc.allows("write")
    assert cc.governed is True

    class _LegacyAgentContract:
        agent_id = "a2"
        contract_id = "ct-a2"
        capabilities = ("read", "meta")
        governed = True

    cc2 = from_universal_agent_contract(_LegacyAgentContract())
    assert cc2 is not None
    assert cc2.allows("read") and cc2.allows("meta")


def test_m5_invalid_contract_none():
    assert from_universal_agent_contract(None) is None
    assert from_universal_agent_contract({"foo": "bar"}) is None


def test_m5_agent_real_read_via_canonical(target_file, harness_with_tool):
    """Agent bertindak via canonical request_capability -> real read (bukan mock)."""
    audit = harness_with_tool._audit  # noqa: SLF001
    contract = CanonicalAgentContract("agent-x", "ct-x", ("read", "meta"))
    agent = build_agent("agent-x", harness_with_tool, contract=contract, audit=audit)

    result = agent.request_capability(
        capability="read", action="read", target=target_file,
        approval_reason="M5 agent read",
    )
    assert result.outcome.get("ok") is True
    assert not result.outcome.get("blocked")
    assert "M5 agent content" in str(result.outcome.get("content", ""))
    # audit mencatat aksi agent via harness
    assert any("agent" in e.action or "harness" in e.action for e in audit.entries)


def test_m5_agent_contract_violation_denied(harness_with_tool):
    """Agent minta capability di luar kontrak -> DITOLAK (no external effect)."""
    audit = harness_with_tool._audit  # noqa: SLF001
    contract = CanonicalAgentContract("agent-y", "ct-y", ("read",))  # HANYA read
    agent = build_agent("agent-y", harness_with_tool, contract=contract, audit=audit)

    result = agent.request_capability(
        capability="write", action="write", target="/nonexistent.txt",
        approval_reason="M5 should be denied by contract",
    )
    assert result.outcome.get("ok") is False
    assert result.outcome.get("blocked") is True
    assert "contract" in result.outcome.get("blocked_by", [])
    assert result.external_effect is False
    # audit mencatat penolakan kontrak
    assert any("denied" in e.action for e in audit.entries)


def test_m5_agent_no_direct_adapter_access():
    """Agent tak punya jalur adapter langsung (hanya harness canonical)."""
    h = RealExecutionHarness(audit=AuditTrail())
    agent = RealCanonicalAgent("agent-z", h)
    # Tidak ada atribut adapter/executor — hanya harness + kontrak
    assert not hasattr(agent, "_adapter")
    assert not hasattr(agent, "_executor")
    assert agent._harness is h
    assert agent.is_bypassed("read") is False  # tidak ada jalur bypass


@pytest.fixture()
def target_file(tmp_path) -> str:
    p = tmp_path / "m5_agent.txt"
    p.write_text("M5 agent content", encoding="utf-8")
    return str(p)
