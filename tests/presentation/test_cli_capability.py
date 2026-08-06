"""Unit test Program I - CLI Structure & RuntimeService Wiring (I1, I2)."""
import sys
import dataclasses

import pytest

from sam.presentation.cli import (
    CLIApplication,
    CLICommand,
    CLICommandSpec,
    CLICommandRegistry,
    CLIFormatter,
    CLI_CORE_COMMANDS,
    build_command,
)
from sam.presentation.cli.wiring import wire_cli_runtime, _make_handler
from sam.runtime_service.api import (
    ConversationPreviewGateway,
    ConversationPreviewResult,
    APIStatus,
    APIHealth,
)


# ----------------------------------------------------------------------
# I1 - CLI Structure
# ----------------------------------------------------------------------

class TestCLIStructure:
    def test_command_frozen(self):
        cmd = build_command("policy", "Policy check", arguments=("policy_id",))
        assert dataclasses.is_dataclass(cmd)
        with pytest.raises(dataclasses.FrozenInstanceError):
            cmd.handler = object()
        assert cmd.spec.arguments == ("policy_id",)

    def test_command_spec_normalizes_tuple(self):
        cmd = build_command("x", arguments=["a", "b"])
        assert cmd.spec.arguments == ("a", "b")

    def test_registry_register_get(self):
        reg = CLICommandRegistry()
        reg.register(build_command("workflow", "w"))
        reg.register_all([build_command("policy", "p"), build_command("audit", "a")])
        assert reg.has("workflow")
        assert reg.get("policy").name == "policy"
        assert reg.names() == ["audit", "policy", "workflow"]
        assert reg.count() == 3

    def test_registry_rejects_non_command(self):
        reg = CLICommandRegistry()
        with pytest.raises(TypeError):
            reg.register("not-a-command")

    def test_application_dispatch_requires_handler(self):
        reg = CLICommandRegistry([build_command("preview", "preview")])
        app = CLIApplication(registry=reg)
        with pytest.raises(NotImplementedError):
            app.execute("preview")

    def test_application_unknown_command(self):
        app = CLIApplication()
        with pytest.raises(KeyError):
            app.execute("nope")

    def test_formatter_kv_and_dict(self):
        f = CLIFormatter()
        assert f.kv("Status", "OK") == "  Status:  OK"
        out = f.render(f.dict_rows({"a": 1, "b": "x"}))
        assert "a" in out and "b" in out

    def test_core_commands_catalogue(self):
        names = [c.name for c in CLI_CORE_COMMANDS]
        assert "workflow" in names
        assert "policy" in names
        assert "audit" in names
        assert "preview" in names
        assert "knowledge" in names
        assert "memory" in names
        assert "artifact" in names
        assert "approval" in names
        assert "runtime" in names and "health" in names and "status" in names

    def test_no_direct_runtime_import(self):
        # Pastikan tidak ada import ke runtime/operations pada modul presentation
        import sam.presentation.cli.commands as cmds
        import sam.presentation.cli.application as app_module
        import sam.presentation.cli.formatter as fmt
        src = (open(cmds.__file__).read() + open(app_module.__file__).read()
               + open(fmt.__file__).read())
        for bad in ("sam.runtime.", "sam.operations", "sam.registry",
                    "sam.providers", "sam.connectors", "sam.execution_runtime"):
            assert bad not in src, "illegal import: " + bad


# ----------------------------------------------------------------------
# I2 - RuntimeService Wiring (handler memanggil jalur resmi)
# ----------------------------------------------------------------------

class _FakeAPI:
    def status(self):
        return APIStatus(services={"runtime": "up"}, version="30.0.0", healthy=True)

    def health(self):
        return APIHealth(status="healthy", checks=["core"], message="ok")


class _FakeGateway:
    def __init__(self):
        self.api = _FakeAPI()

    def preview(self, context, execution_id):
        return ConversationPreviewResult(executed=True, approved=True, status="preview")

    def preview_with_workflow(self, context, wc, workflow_id, execution_id, kc=None, kid=""):
        return {"execution": {}, "workflow": {"id": workflow_id}}

    def preview_with_policy(self, context, pc, policy_id, execution_id):
        return {"execution": {}, "policy": {"id": policy_id}}

    def preview_with_audit(self, context, ac, audit_id, execution_id):
        return {"execution": {}, "audit": {"id": audit_id}}

    def preview_with_knowledge(self, context, kc, knowledge_id, execution_id, memory_id=""):
        return {"execution": {}, "knowledge": {"id": knowledge_id}}

    def preview_with_memory(self, context, mc, memory_id, execution_id):
        return {"execution": {}, "memory": {"id": memory_id}}

    def preview_with_artifact(self, context, ac, artifact_name, execution_id):
        return {"execution": {}, "artifact": {"name": artifact_name}}


def _consumers():
    return {"knowledge": object(), "workflow": object(), "policy": object(),
            "audit": object(), "memory": object(), "artifact": object()}


class TestRuntimeWiring:
    def test_wire_attaches_handlers(self):
        gw = _FakeGateway()
        wiring = wire_cli_runtime(gw, consumers=_consumers())
        att = wiring.attached()
        for name in ("workflow", "policy", "audit", "preview", "knowledge",
                     "memory", "artifact", "approval", "runtime", "health", "status"):
            assert att[name], "handler missing: " + name

    def test_capability_handlers_call_gateway(self):
        gw = _FakeGateway()
        wiring = wire_cli_runtime(gw, consumers=_consumers())
        reg = wiring.gateway.__class__  # placeholder
        # hampir langsung pakai handler dari wiring registry
        # jalur handler diakses lewat attach registry (gunakan register public)
        from sam.presentation.cli.wiring import CLI_CORE_COMMANDS
        h = _make_handler(gw, "workflow", _consumers())
        out = h("wf1", "e1")
        assert out["workflow"]["id"] == "wf1"
        h2 = _make_handler(gw, "status", _consumers())
        assert h2()["healthy"] is True

    def test_approval_pass_through(self):
        gw = _FakeGateway()
        h = _make_handler(gw, "approval", _consumers())
        out = h("r1", "e1")
        assert out["approved"] is True
        assert out["status"] == "preview"

    def test_runtime_health_handlers(self):
        gw = _FakeGateway()
        hh = _make_handler(gw, "health", _consumers())
        h = hh()
        assert h["status"] == "healthy" and h["healthy"] is True
        hr = _make_handler(gw, "runtime", _consumers())
        assert hr()["version"] == "30.0.0"

    def test_mission_no_handler(self):
        # Mission TANPA jalur -> _make_handler menghasilkan None (Deferred)
        gw = _FakeGateway()
        h = _make_handler(gw, "mission", _consumers())
        assert h is None


# ----------------------------------------------------------------------
# I3-I9 + I11 - Integration (semua command lewat jalur resmi)
# ----------------------------------------------------------------------

from sam.presentation.cli.integration import CLIIntegration, CLICommandResult
from sam.presentation.cli import CLICommandRegistry


class TestCLIIntegration:
    def _wired(self):
        gw = _FakeGateway()
        reg = CLICommandRegistry()
        wire_cli_runtime(gw, registry=reg, consumers=_consumers())
        return gw, CLIIntegration(registry=reg)

    def test_all_core_commands_run(self):
        _, integration = self._wired()
        for name in ("workflow", "policy", "audit", "preview", "knowledge",
                     "memory", "artifact", "approval", "runtime", "health", "status"):
            res = integration.run(name, "r1", "e1")
            assert res.ok, "command {} gagal: {}".format(name, res.error)

    def test_workflow_data(self):
        _, integration = self._wired()
        res = integration.run("workflow", "wf1", "e1")
        assert res.ok
        assert res.data["workflow"]["id"] == "wf1"

    def test_approval_pass_through(self):
        _, integration = self._wired()
        res = integration.run("approval", "r1", "e1")
        assert res.ok
        assert res.data["approved"] is True

    def test_mission_deferred(self):
        _, integration = self._wired()
        res = integration.run("mission")
        assert res.ok is False
        assert res.data["status"] == "deferred"

    def test_unknown_command(self):
        _, integration = self._wired()
        res = integration.run("nope")
        assert res.ok is False
        assert res.error == "unknown command"

    def test_render_ok_and_deferred(self):
        _, integration = self._wired()
        ok = integration.run("status")
        txt = integration.render(ok)
        assert "sam status" in txt
        dep = integration.run("mission")
        dtxt = integration.render(dep)
        assert "deferred" in dtxt

    def test_result_frozen(self):
        _, integration = self._wired()
        res = integration.run("status")
        assert dataclasses.is_dataclass(res)
        with pytest.raises(dataclasses.FrozenInstanceError):
            res.command = "x"
