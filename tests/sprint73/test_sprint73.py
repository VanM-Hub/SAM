import pytest, os, sys
from dataclasses import FrozenInstanceError
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.console import ConsoleCommand, ConsoleResponse
from sam.approval.console_engine import ConsoleEngine

def test_frozen():
    with pytest.raises(FrozenInstanceError):
        ConsoleCommand(command="help").__setattr__("command","x")

def test_engine():
    e = ConsoleEngine()
    assert "help" in e.list_commands()

def test_execute():
    r = ConsoleEngine().execute(ConsoleCommand(command="help"))
    assert r.success is True

def test_unknown():
    r = ConsoleEngine().execute(ConsoleCommand(command="nonexistent"))
    assert r.success is False
