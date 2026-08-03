"""Command parsing tests for the Compliance CLI (P1-006)."""

import pytest

from sam.compliance.cli import (
    CommandDispatcher, CommandParseError, RUN, LIST, INFO, SUMMARY,
)
from sam.compliance.cli.session_runner import SessionFilter


@pytest.fixture
def dispatcher():
    return CommandDispatcher()


class TestRunParsing:
    def test_run_no_args(self, dispatcher):
        cmd = dispatcher.parse(["run"])
        assert cmd.action == RUN
        assert cmd.to_filter().is_empty()

    def test_run_all(self, dispatcher):
        cmd = dispatcher.parse(["run", "--all"])
        assert cmd.action == RUN
        assert cmd.to_filter().is_empty()

    def test_run_check_id(self, dispatcher):
        cmd = dispatcher.parse(["run", "L1-C01"])
        assert cmd.action == RUN
        assert cmd.check_id == "L1-C01"

    def test_run_level(self, dispatcher):
        cmd = dispatcher.parse(["run", "--level", "L0"])
        assert cmd.action == RUN
        assert cmd.level == "L0"
        filt = cmd.to_filter()
        assert isinstance(filt, SessionFilter)
        assert filt.level == "L0"

    def test_run_category(self, dispatcher):
        cmd = dispatcher.parse(["run", "--category", "ADR"])
        assert cmd.category == "ADR"

    def test_run_authority(self, dispatcher):
        cmd = dispatcher.parse(["run", "--authority", "Specification"])
        assert cmd.authority == "Specification"

    def test_run_tag(self, dispatcher):
        cmd = dispatcher.parse(["run", "--tag", "runtime"])
        assert cmd.tag == "runtime"

    def test_run_multiple_filters_and(self, dispatcher):
        cmd = dispatcher.parse(["run", "--level", "L1", "--category", "Testing"])
        assert cmd.level == "L1"
        assert cmd.category == "Testing"


class TestOtherParsing:
    def test_list(self, dispatcher):
        cmd = dispatcher.parse(["list"])
        assert cmd.action == LIST

    def test_list_with_filter(self, dispatcher):
        cmd = dispatcher.parse(["list", "--level", "L2"])
        assert cmd.action == LIST
        assert cmd.level == "L2"

    def test_info(self, dispatcher):
        cmd = dispatcher.parse(["info", "L0-01"])
        assert cmd.action == INFO
        assert cmd.check_id == "L0-01"

    def test_info_requires_check_id(self, dispatcher):
        with pytest.raises(CommandParseError):
            dispatcher.parse(["info"])

    def test_summary(self, dispatcher):
        cmd = dispatcher.parse(["summary"])
        assert cmd.action == SUMMARY

    def test_unknown_command(self, dispatcher):
        with pytest.raises(CommandParseError):
            dispatcher.parse(["frobnicate"])

    def test_no_command(self, dispatcher):
        with pytest.raises(CommandParseError):
            dispatcher.parse([])

    def test_unknown_option(self, dispatcher):
        with pytest.raises(CommandParseError):
            dispatcher.parse(["run", "--bogus"])

    def test_option_missing_value(self, dispatcher):
        with pytest.raises(CommandParseError):
            dispatcher.parse(["run", "--level"])

    def test_positional_not_allowed_in_list(self, dispatcher):
        with pytest.raises(CommandParseError):
            dispatcher.parse(["list", "L0-01"])


class TestDispatch:
    def test_dispatch_returns_action_if_no_handler(self, dispatcher):
        cmd = dispatcher.parse(["run"])
        assert dispatcher.dispatch(cmd) == RUN

    def test_dispatch_calls_handler(self, dispatcher):
        calls = []
        dispatcher.register(RUN, lambda c: calls.append(c.action) or "handled")
        cmd = dispatcher.parse(["run"])
        assert dispatcher.dispatch(cmd) == "handled"
        assert calls == ["run"]

    def test_to_filter(self, dispatcher):
        cmd = dispatcher.parse(["run", "--tag", "runtime"])
        filt = cmd.to_filter()
        assert filt.tag == "runtime"
