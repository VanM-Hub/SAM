"""Sprint 146 — Shell Provider Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.providers.shell.shell_provider import ShellProvider
from sam.providers.shell.command_builder import ShellCommand, ShellCommandBuilder
from sam.providers.shell.command_preview import ShellPreview, ShellCommandPreview
from sam.providers.shell.command_validator import ShellCommandValidator, ShellCommandValidation
from sam.providers.shell.command_history import ShellHistory, ShellHistoryEntry
from sam.providers.shell.conversation_shell import ConversationShellBridge
from sam.providers.shell.dashboard_shell import DashboardShellBridge
from sam.providers.base.base_provider import ProviderError
from sam.providers.dashboard.dashboard_provider import ExecutionCard


class TestShellProvider:
    def test_descriptor(self):
        p = ShellProvider()
        assert p.descriptor.provider_type == "shell"

    def test_build_command(self):
        p = ShellProvider()
        r = p.build_command("ls", ["-la"])
        assert r["preview"] is True
        assert r["executed"] is False
        assert r["external_calls"] == 0

    def test_build_empty_raises(self):
        with pytest.raises(ProviderError):
            ShellProvider().build_command("")

    def test_external_always_zero(self):
        p = ShellProvider()
        p.build_command("ls")
        assert p.external_calls == 0


class TestShellCommand:
    def test_render(self):
        c = ShellCommand("c1", "ls", ["-la", "/tmp"])
        assert c.render() == "ls -la /tmp"

    def test_immutable(self):
        c = ShellCommand("c1", "ls")
        with pytest.raises(FrozenInstanceError):
            c.executable = "rm"


class TestShellCommandBuilder:
    def test_build(self):
        c = ShellCommandBuilder().build("c1", "cat", ["/a"])
        assert c.command_id == "c1"
        assert c.executable == "cat"

    def test_args_default(self):
        c = ShellCommandBuilder().build("c1", "echo")
        assert c.args == []


class TestShellCommandPreview:
    def test_preview(self):
        cmd = ShellCommandBuilder().build("c1", "ls")
        p = ShellCommandPreview().preview(cmd)
        assert p.executed is False
        assert p.external_calls == 0
        assert p.preview is True


class TestShellCommandValidator:
    def test_valid(self):
        v = ShellCommandValidator().validate(ShellCommand("c1", "ls"))
        assert v.valid is True

    def test_empty_executable(self):
        v = ShellCommandValidator().validate(ShellCommand("c1", ""))
        assert v.valid is False

    def test_blocked_executable(self):
        v = ShellCommandValidator().validate(ShellCommand("c1", "bash"))
        assert v.valid is False

    def test_blocked_subprocess(self):
        v = ShellCommandValidator().validate(ShellCommand("c1", "subprocess"))
        assert v.valid is False


class TestShellHistory:
    def test_record(self):
        h = ShellHistory()
        h.record(ShellHistoryEntry("c1", "ls", validated=True, executed=False))
        assert h.count() == 1

    def test_no_execution(self):
        h = ShellHistory()
        h.record(ShellHistoryEntry("c1", "ls"))
        assert h.total_external_calls() == 0


class TestConversationShellBridge:
    def test_describe(self):
        b = ConversationShellBridge(ShellProvider())
        assert "shell" in b.describe()

    def test_contract(self):
        b = ConversationShellBridge(ShellProvider())
        assert "shell" in b.contract()

    def test_supports(self):
        b = ConversationShellBridge(ShellProvider())
        assert b.supports("build")
        assert b.supports("preview")


class TestDashboardShellBridge:
    def test_card(self):
        b = DashboardShellBridge(ShellProvider())
        card = b.card()
        assert isinstance(card, ExecutionCard)
        assert card.provider_id == "shell"
        assert card.verdict == "ready"


class TestShellImmutability:
    DTO_CLASSES = [
        ShellCommand, ShellPreview,
        ShellCommandValidation, ShellHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
