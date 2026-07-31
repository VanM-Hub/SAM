"""Sprint 266 - Plugin Runtime.

Program D - Runtime Services & Deployment.
Plugin hanya metadata. Tidak memanggil provider.
"""
from __future__ import annotations
import pytest

from sam.runtime_service.plugins import PLUGIN_NAMES
from sam.runtime_service.plugins.plugin_descriptor import PluginDescriptor
from sam.runtime_service.plugins.plugin_registry import PluginRegistry
from sam.runtime_service.plugins.plugin_loader import PluginLoader
from sam.runtime_service.plugins.plugin_validator import PluginValidator
from sam.runtime_service.plugins.plugin_runtime import PluginRuntime


def test_plugin_names_present():
    for name in ("openai", "anthropic", "gemini", "deepseek",
                 "openrouter", "ollama", "openclaw"):
        assert name in PLUGIN_NAMES


def test_descriptor_immutable():
    d = PluginDescriptor(name="openai")
    assert d.kind == "provider"
    with pytest.raises(Exception):
        d.name = "x"
    with pytest.raises(ValueError):
        PluginDescriptor(name="")


def test_descriptor_as_dict():
    d = PluginDescriptor(name="openai", secret_key="OPENAI_API_KEY",
                         capabilities=["chat"])
    ad = d.as_dict()
    assert ad["secret_key"] == "OPENAI_API_KEY"
    assert ad["capabilities"] == ["chat"]


def test_registry_register_get():
    r = PluginRegistry()
    r.register(PluginDescriptor(name="a"))
    assert r.has("a")
    assert r.get("a").name == "a"
    assert r.count() == 1


def test_registry_duplicate():
    r = PluginRegistry()
    r.register(PluginDescriptor(name="a"))
    with pytest.raises(ValueError):
        r.register(PluginDescriptor(name="a"))


def test_registry_list_sorted():
    r = PluginRegistry()
    r.register(PluginDescriptor(name="b"))
    r.register(PluginDescriptor(name="a"))
    assert r.names() == ["a", "b"]


def test_loader_load():
    loader = PluginLoader()
    n = loader.load([PluginDescriptor(name="x"), PluginDescriptor(name="y")])
    assert n == 2
    assert loader.registry.count() == 2


def test_loader_from_dicts():
    loader = PluginLoader()
    n = loader.load_from_dicts([{"name": "a"}, {"name": "b", "kind": "tool"}])
    assert n == 2
    assert loader.registry.get("b").kind == "tool"


def test_loader_duplicate_rejected():
    loader = PluginLoader()
    loader.load([PluginDescriptor(name="a")])
    with pytest.raises(ValueError):
        loader.load([PluginDescriptor(name="a")])


def test_validator_valid():
    v = PluginValidator()
    assert v.is_valid(PluginDescriptor(name="ok"))
    assert v.validate(PluginDescriptor(name="ok", kind="bogus"))
    assert not v.is_valid(PluginDescriptor(name="ok", kind="bogus"))


def test_validator_requires_name():
    v = PluginValidator()
    assert v.validate(PluginDescriptor(name="ok")) == []


def test_runtime_defaults_loaded():
    rt = PluginRuntime()
    assert rt.count() == 7
    assert set(rt.names()) == set(PLUGIN_NAMES)


def test_runtime_get_secret_key():
    rt = PluginRuntime()
    assert rt.get("openai").secret_key == "OPENAI_API_KEY"
    assert rt.get("openclaw").secret_key == "OPENCLAW_URL"


def test_runtime_get_missing():
    rt = PluginRuntime()
    assert rt.get("nonexistent") is None
    assert "nonexistent" not in rt.names()


def test_runtime_metadata_only():
    # Plugin tidak boleh punya perilaku eksekusi/metode network
    rt = PluginRuntime()
    d = rt.get("openai")
    assert not hasattr(d, "execute")
    assert not hasattr(d, "invoke")
    assert not hasattr(d, "call")


def test_runtime_ollama_no_secret():
    rt = PluginRuntime()
    # ollama dapat tidak memerlukan secret key
    assert rt.get("ollama").secret_key is None


def test_plugins_are_metadata_not_calls():
    import inspect
    from sam.runtime_service.plugins import plugin_runtime
    src = inspect.getsource(plugin_runtime)
    assert "requests." not in src
    assert "urllib" not in src
    assert "import socket" not in src
