"""Sprint 265 - Dependency Injection.

Program D - Runtime Services & Deployment.
Semua runtime dibuat melalui container. Tidak instantiate manual.
"""
from __future__ import annotations
import pytest

from sam.runtime_service.container import Container
from sam.runtime_service.container.provider_factory import (
    ProviderFactory, ProviderRegistration,
)
from sam.runtime_service.container.runtime_factory import (
    RuntimeFactory, RuntimeRegistration,
)
from sam.runtime_service.container.service_factory import (
    ServiceFactory, ServiceRegistration,
)
from sam.runtime_service.container.resolver import Resolver


def test_provider_factory_register_create():
    pf = ProviderFactory()
    pf.register("openai", kind="llm")
    assert pf.count() == 1
    reg = pf.create("openai")
    assert reg.kind == "llm"
    assert reg.enabled is True


def test_provider_factory_duplicate():
    pf = ProviderFactory()
    pf.register("openai")
    with pytest.raises(ValueError):
        pf.register("openai")


def test_provider_factory_missing():
    pf = ProviderFactory()
    with pytest.raises(KeyError):
        pf.create("nope")


def test_provider_factory_names_filter_enabled():
    pf = ProviderFactory()
    pf.register("a", enabled=True)
    pf.register("b", enabled=False)
    assert pf.names() == ["a"]


def test_runtime_factory_singleton():
    rf = RuntimeFactory()
    counter = {"n": 0}
    def make():
        counter["n"] += 1
        return object()
    rf.register("rt", make, singleton=True)
    a = rf.resolve("rt")
    b = rf.resolve("rt")
    assert a is b  # singleton: instance sama
    assert counter["n"] == 1


def test_runtime_factory_non_singleton():
    rf = RuntimeFactory()
    def make():
        return object()
    rf.register("rt", make, singleton=False)
    a = rf.resolve("rt")
    b = rf.resolve("rt")
    assert a is not b  # non-singleton: instance beda


def test_runtime_factory_missing():
    rf = RuntimeFactory()
    with pytest.raises(KeyError):
        rf.resolve("nope")


def test_service_factory_dependencies():
    sf = ServiceFactory()
    def make_repo():
        return {"repo": True}
    def make_svc(repo):
        return {"svc": True, "uses": repo}
    sf.register("repo", make_repo)
    sf.register("svc", make_svc, dependencies=["repo"])
    svc = sf.resolve("svc")
    assert svc["svc"] is True
    assert svc["uses"]["repo"] is True


def test_service_factory_singleton():
    sf = ServiceFactory()
    sf.register("s", lambda: object())
    assert sf.resolve("s") is sf.resolve("s")


def test_service_factory_missing():
    sf = ServiceFactory()
    with pytest.raises(KeyError):
        sf.resolve("nope")


def test_resolver_kinds():
    r = Resolver()
    r.register_provider("openai")
    r.register_runtime("rt", lambda: "runtime-obj")
    assert r.resolve("provider", "openai").name == "openai"
    assert r.resolve("runtime", "rt") == "runtime-obj"
    with pytest.raises(ValueError):
        r.resolve("bogus", "x")


def test_container_register_get_runtime():
    c = Container()
    c.register_runtime("exec", lambda: "exec-instance")
    assert c.get_runtime("exec") == "exec-instance"
    assert c.has_runtime("exec") is True


def test_container_runtime_singleton():
    c = Container()
    def make():
        return object()
    c.register_runtime("rt", make)
    assert c.get_runtime("rt") is c.get_runtime("rt")


def test_container_register_provider():
    c = Container()
    c.register_provider("gemini", kind="llm")
    reg = c.get_provider_registration("gemini")
    assert reg.kind == "llm"


def test_container_service_deps():
    c = Container()
    c.register_service("dep", lambda: "D")
    c.register_service("main", lambda d: ("MAIN", d), dependencies=["dep"])
    result = c.get_service("main")
    assert result == ("MAIN", "D")


def test_container_all_through_container():
    # Semua instance harus dibuat via container (bukan manual)
    c = Container()
    c.register_provider("deepseek")
    c.register_runtime("eng", lambda: {"via": "container"})
    obj = c.get_runtime("eng")
    assert obj["via"] == "container"
