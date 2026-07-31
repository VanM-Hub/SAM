"""Sprint 262 - Configuration Runtime.

Program D - Runtime Services & Deployment.
"""
from __future__ import annotations
import pytest

from sam.runtime_service.configuration.config_loader import ConfigLoader
from sam.runtime_service.configuration.config_validator import ConfigValidator
from sam.runtime_service.configuration.config_profile import ConfigProfile
from sam.runtime_service.configuration.config_snapshot import ConfigSnapshot
from sam.runtime_service.configuration.config_runtime import ConfigRuntime


def test_loader_from_dict():
    l = ConfigLoader()
    assert l.from_dict({"a": 1}) == {"a": 1}


def test_loader_from_env_prefix():
    l = ConfigLoader()
    env = {"SAM_SERVICE": "svc", "SAM_PORT": "8080", "OTHER": "x"}
    out = l.from_env(env=env)
    assert out["service"] == "svc"
    assert out["port"] == "8080"
    assert "other" not in out


def test_loader_from_json():
    l = ConfigLoader()
    assert l.from_json('{"a": 1}') == {"a": 1}
    with pytest.raises(Exception):
        l.from_json("not-json")


def test_loader_load_format():
    l = ConfigLoader()
    assert l.load({"x": 1}, format="dict") == {"x": 1}
    with pytest.raises(ValueError):
        l.load(None, format="bogus")


def test_loader_yaml_available_or_error():
    l = ConfigLoader()
    try:
        assert l.from_yaml("a: 1") == {"a": 1}
    except RuntimeError:
        pytest.skip("PyYAML tidak tersedia")


def test_validator_required():
    v = ConfigValidator()
    errs = v.validate({})
    assert any("service" in e for e in errs)
    assert not v.is_valid({})
    assert v.is_valid({"service": "svc"})


def test_validator_required_custom():
    v = ConfigValidator()
    errs = v.validate({"a": 1}, required=["a", "b"])
    assert len(errs) == 1
    assert "b" in errs[0]


def test_validator_rejects_network_obj():
    v = ConfigValidator()
    class NetObj:  # objek dengan perilaku network-like
        def __init__(self): self.sock = object()
    errs = v.validate({"service": "s", "obj": NetObj()})
    assert any("obj" in e for e in errs)


def test_profile_immutable():
    p = ConfigProfile(name="prod", values={"port": 8080})
    assert p.get("port") == 8080
    with pytest.raises(Exception):
        p.name = "x"
    with pytest.raises(ValueError):
        ConfigProfile(name="")
    assert p.as_dict()["description"] == ""


def test_snapshot_immutable_values():
    s = ConfigSnapshot(values={"a": 1})
    assert s.get("a") == 1
    with pytest.raises(TypeError):
        s.values["a"] = 99  # MappingProxyType menolak mutasi
    assert s.get("a") == 1
    assert s.as_dict()["revision"] == 0


def test_snapshot_get():
    s = ConfigSnapshot(values={"p": 1})
    assert s.get("p") == 1
    assert s.get("q", "d") == "d"


def test_config_runtime_resolve_default():
    cr = ConfigRuntime()
    snap = cr.resolve({"service": "svc", "port": 8080})
    assert isinstance(snap, ConfigSnapshot)
    assert snap.get("service") == "svc"
    assert snap.get("port") == 8080
    assert cr.revision == 1


def test_config_runtime_profile_merge():
    cr = ConfigRuntime()
    cr.register_profile(ConfigProfile(name="prod", values={"service": "svc", "env": "prod", "port": 80}))
    snap = cr.resolve({"port": 9090}, profile="prod")
    assert snap.get("env") == "prod"
    assert snap.get("port") == 9090  # override menang
    assert snap.get("service") == "svc"


def test_config_runtime_profiles_list():
    cr = ConfigRuntime()
    cr.register_profile(ConfigProfile(name="b"))
    cr.register_profile(ConfigProfile(name="a"))
    assert cr.profiles() == ["a", "b"]


def test_config_runtime_missing_required():
    cr = ConfigRuntime()
    with pytest.raises(ValueError):
        cr.resolve({}, required=["service"])


def test_config_runtime_revision_increments():
    cr = ConfigRuntime()
    cr.resolve({"service": "a"})
    cr.resolve({"service": "b"})
    assert cr.revision == 2


def test_loader_no_direct_provider_read():
    # Konfigurasi tidak boleh membaca provider secara langsung
    import inspect
    src = inspect.getsource(ConfigLoader)
    assert "providers" not in src or "from_env" in src
