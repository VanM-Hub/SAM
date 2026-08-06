"""ENG-G-001 · G11 — Conversation Capability tests.

Menguji struktur & wiring Conversation (G1–G2, G4–G10):
- ViewModel/Command/Composition immutable & read-only (G1)
- Wiring ke runtime_service.api (0 import langsung runtime; G2)
- Workflow/Policy/Audit/Preview/Knowledge/Memory/Artifact via gateway (G4–G9)
- Approval pass-through (G9)
- Integration 8 capability, Mission pending (G10)
Semua tanpa mengeksekusi runtime (preview). Tidak bergantung pada jaringan.
"""
from __future__ import annotations

import pytest

import sam.runtime_service.api as api
from sam.presentation.conversation import (
    ConversationViewModel,
    ConversationCommand,
    ConversationComposition,
    compose_conversation,
    ConversationIntegration,
    wire_conversation_runtime,
)

COMMAND_COUNT = 9


# ---------------------------------------------------------------------------
# G1 — Structure (ViewModel/Command/Composition, immutable, read-only)
# ---------------------------------------------------------------------------
class TestG1_Structure:
    def test_viewmodel_lists_nine_capabilities_not_attached(self):
        vm = ConversationViewModel()
        assert len(vm.capability_list()) == 9
        assert all(v == "not_attached" for v in vm.capabilities.values())

    def test_viewmodel_read_only(self):
        vm = ConversationViewModel()
        with pytest.raises(Exception):
            vm.conversation_id = "other"  # frozen dataclass -> error

    def test_command_registers_nine_specs(self):
        cmd = ConversationCommand()
        assert len(cmd.names()) == COMMAND_COUNT
        assert cmd.has_handler("mission") is False  # belum di-attach

    def test_composition_read_only(self):
        vm = ConversationViewModel()
        cmd = ConversationCommand()
        comp = compose_conversation(vm, cmd)
        assert len(comp.command_specs) == COMMAND_COUNT
        with pytest.raises(Exception):
            comp.command_names = []  # frozen


# ---------------------------------------------------------------------------
# G2 — Wiring (via runtime_service.api, 0 direct runtime import)
# ---------------------------------------------------------------------------
class TestG2_Wiring:
    def test_wiring_attaches_all_capabilities(self):
        api_obj = api.RuntimeAPI()
        gw = api.ConversationPreviewGateway(api_obj)
        gw.configure(provider_id="filesystem")
        cmd = ConversationCommand()
        wire_conversation_runtime(gw, cmd, ConversationViewModel())
        assert all(cmd.has_handler(n) for n in cmd.names())


# ---------------------------------------------------------------------------
# G4–G9 — Capability via gateway (preview, no-execute)
# ---------------------------------------------------------------------------
class _Consumer:
    """Consumer stub: mengembalikan objek dengan as_dict() (komposisi)."""

    def resolve_knowledge(self, i):
        return type("X", (), {"as_dict": lambda s: {"knowledge": i}})()

    def resolve_memory(self, i):
        return type("X", (), {"as_dict": lambda s: {"memory": i}})()

    def resolve_workflow(self, i):
        return type("X", (), {"as_dict": lambda s: {"workflow": i}})()

    def resolve_artifact(self, n):
        return type("X", (), {"as_dict": lambda s: {"artifact": n}})()

    def resolve_policy(self, i):
        return type("X", (), {"as_dict": lambda s: {"policy": i}})()

    def resolve_audit(self, i):
        return type("X", (), {"as_dict": lambda s: {"audit": i}})()


class TestCapabilities:
    @pytest.fixture()
    def wired(self):
        api_obj = api.RuntimeAPI()
        gw = api.ConversationPreviewGateway(api_obj)
        gw.configure(provider_id="filesystem")
        cmd = ConversationCommand()
        wire_conversation_runtime(gw, cmd, ConversationViewModel())
        return cmd

    def test_preview_is_noexec(self, wired):
        ctx = api.ConversationExecutionContext(conversation_id="c", request="r")
        r = wired._handlers["preview"](ctx, None, "p_1", "e1")
        assert r["executed"] is False  # preview murni, tidak eksekusi

    @pytest.mark.parametrize(
        "capability,expected",
        [
            ("workflow", "workflow"),
            ("policy", "policy"),
            ("audit", "audit"),
            ("knowledge", "knowledge"),
            ("memory", "memory"),
            ("artifact", "artifact"),
        ],
    )
    def test_capability_resolves_via_consumer(self, wired, capability, expected):
        ctx = api.ConversationExecutionContext(conversation_id="c", request="r")
        stub = _Consumer()
        r = wired._handlers[capability](ctx, stub, f"{expected}_1", "e9")
        assert expected in r
        assert r[expected][expected] == f"{expected}_1"


# ---------------------------------------------------------------------------
# G10 — Integration (8 capability; Mission pending)
# ---------------------------------------------------------------------------
class TestG10_Integration:
    def test_run_integrates_active_capabilities(self):
        api_obj = api.RuntimeAPI()
        gw = api.ConversationPreviewGateway(api_obj)
        gw.configure(provider_id="filesystem")
        cmd = ConversationCommand()
        vm = ConversationViewModel()
        wire_conversation_runtime(gw, cmd, vm)

        stub = _Consumer()
        consumers = {k: stub for k in ("workflow", "policy", "audit", "knowledge", "memory", "artifact")}
        ctx = api.ConversationExecutionContext(conversation_id="c", request="r")
        itg = ConversationIntegration(vm, cmd, lambda req: ctx, consumers, lambda: {"status": "pass_through"})

        result = itg.run("hello", "e10")
        assert all(v == "ok" for v in result.capability_status.values())
        assert result.executed() is False
        assert result.approval == {"status": "pass_through"}  # G9 pass-through
        assert result.mission is None  # G3 pending

    def test_run_without_consumer_reports_no_consumer(self):
        api_obj = api.RuntimeAPI()
        gw = api.ConversationPreviewGateway(api_obj)
        gw.configure(provider_id="filesystem")
        cmd = ConversationCommand()
        vm = ConversationViewModel()
        wire_conversation_runtime(gw, cmd, vm)
        ctx = api.ConversationExecutionContext(conversation_id="c", request="r")
        itg = ConversationIntegration(vm, cmd, lambda req: ctx, consumers=None)
        result = itg.run("hello", "e20")
        # tanpa consumer -> capability selain preview dilaporkan no_consumer/unwired
        assert result.capability_status["workflow"] == "no_consumer"
        assert result.capability_status["preview"] == "ok"  # preview tak butuh consumer
