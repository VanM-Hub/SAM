import json
import os
import pytest

from sam.services.configuration import ConfigurationService, ConfigSchema


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def test_load_valid_json(tmp_path):
    p = tmp_path / "cfg.json"
    write_json(p, {"a": 1, "b": "x"})
    svc = ConfigurationService(str(p))
    assert svc.get_int("a") == 1
    assert svc.get_str("b") == "x"


def test_load_missing_file(tmp_path):
    p = tmp_path / "nope.json"
    # Ensure file does not exist
    if p.exists():
        p.unlink()
    svc = ConfigurationService(str(p))
    # Missing file -> get returns default
    assert svc.get("whatever", "def") == "def"


def test_get_str(tmp_path):
    p = tmp_path / "cfg.json"
    write_json(p, {"workspace": "./ws"})
    svc = ConfigurationService(str(p))
    assert svc.get_str("workspace") == "./ws"


def test_get_int(tmp_path):
    p = tmp_path / "cfg.json"
    write_json(p, {"runtime": {"timeout": 10}})
    svc = ConfigurationService(str(p))
    assert svc.get_int("runtime.timeout") == 10


def test_get_bool(tmp_path):
    p = tmp_path / "cfg.json"
    write_json(p, {"flags": {"enabled": True}})
    svc = ConfigurationService(str(p))
    assert svc.get_bool("flags.enabled") is True


def test_get_path(tmp_path):
    p = tmp_path / "cfg.json"
    write_json(p, {"paths": {"data": "./data"}})
    svc = ConfigurationService(str(p))
    assert svc.get_path("paths.data") == "./data"


def test_get_default(tmp_path):
    p = tmp_path / "cfg.json"
    write_json(p, {"x": 1})
    svc = ConfigurationService(str(p))
    assert svc.get_str("no.such.key", "fallback") == "fallback"


def test_set_and_get(tmp_path):
    p = tmp_path / "cfg.json"
    write_json(p, {"x": {}})
    svc = ConfigurationService(str(p))
    svc.set("x.value", 42)
    assert svc.get_int("x.value") == 42


def test_reload(tmp_path):
    p = tmp_path / "cfg.json"
    write_json(p, {"v": 1})
    svc = ConfigurationService(str(p))
    assert svc.get_int("v") == 1
    # modify file
    write_json(p, {"v": 2})
    svc.reload()
    assert svc.get_int("v") == 2


def test_validate_schema_valid(tmp_path):
    p = tmp_path / "cfg.json"
    write_json(p, {"required_field": "ok", "num": 5})
    schema = ConfigSchema(required=["required_field"], types={"required_field": "str", "num": "int"})
    svc = ConfigurationService(str(p), schema=schema)
    # explicit validate should pass
    svc.validate()


def test_validate_schema_invalid(tmp_path):
    p = tmp_path / "cfg.json"
    write_json(p, {"num": 5})
    schema = ConfigSchema(required=["required_field"], types={"required_field": "str"})
    with pytest.raises(Exception):
        # initialization should attempt validation and raise
        ConfigurationService(str(p), schema=schema)
