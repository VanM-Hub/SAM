# M13-013 tests - Evidenced external protection wiring helpers
#
# Fokus: HttpObservationAdapter harus bisa membaca header read-only dari env
# runtime (fallback ke os.environ) tanpa hardcode secret, dan tidak pernah
# memasukkan secret utuh ke payload/evidence.
import os
import pytest

from sam.ward.capability.contracts import SubjectRef
from sam.ward.adapters.http_observation import HttpObservationAdapter


def _adapter(**kw):
    subj = SubjectRef(subject_id="w", subject_type="ward", kind="repository", name="x")
    base = kw.pop("base_url", "https://api.github.com")
    ph = kw.pop("path", "repos/x")
    return HttpObservationAdapter(subj, base_url=base, path=ph, **kw)


def test_no_headers_env_returns_none():
    a = _adapter()
    assert a._resolve_headers(None) is None


def test_headers_env_reads_from_explicit_runtime_env():
    a = _adapter(headers_env={"Authorization": "AUTH_KEY"})
    h = a._resolve_headers({"AUTH_KEY": "sekretX"})
    assert h == {"Authorization": "sekretX"}


def test_headers_env_falls_back_to_os_environ(monkeypatch):
    monkeypatch.setenv("PROBE_AUTH", "abc123")
    a = _adapter(headers_env={"Authorization": "PROBE_AUTH"})
    h = a._resolve_headers(None)
    assert h == {"Authorization": "abc123"}


def test_missing_env_key_not_in_headers():
    a = _adapter(headers_env={"Authorization": "NOPE"})
    assert a._resolve_headers({}) is None


def test_resolve_url_joins_base_and_path():
    a = _adapter(path="repos/VanM-Hub/test-issues")
    assert a._resolve_url() == "https://api.github.com/repos/VanM-Hub/test-issues"


def test_adapter_has_no_mutation_methods():
    a = _adapter()
    assert not hasattr(a, "mutate")
    assert not hasattr(a, "create_issue")
    assert not hasattr(a, "write")
    assert not hasattr(a, "restart")
    assert not hasattr(a, "delete")
