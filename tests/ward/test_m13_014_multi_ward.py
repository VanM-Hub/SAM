# Tests M13-014 - Multi-Ward Generalization
#
# Satu semantic governance model harus bekerja untuk BERBAGAI jenis Ward
# (GitHub repo, HTTP status endpoint, dsb) tanpa duplikasi capability dan
# tanpa executor kedua. Engine yang sama (WardGovernor + boundary) dipakai
# untuk semua subject; hanya ADAPTER (infrastructure) yang berbeda.
#
# Unit test: TIDAK ada panggilan eksternal (adapter di-stub).
import pytest

from sam.ward.identity.models import (WardIdentity, WardOwner, WardAccessScope)
from sam.ward.entrustment.models import Entrustment, ApprovalPolicy
from sam.ward.registry.registry import WardRepository
from sam.ward.governance.boundary import WardGovernanceBoundary
from sam.ward.governance.governor import WardGovernor
from sam.ward.capability.contracts import (
    SubjectRef, Observation, InvestigationResult, ObservationTarget,
    InvestigationTarget,
)


# --- 3 jenis Ward dengan adapter berbeda, SEMUA memakai kontrak sama ---

class _FakeLinkObservation(ObservationTarget):
    """Adapter Ward 'external_api' - mis. HTTP status endpoint."""

    def __init__(self, reachable=True):
        self._reachable = reachable

    def observe(self, *, capability="observe"):
        return Observation(subject=SubjectRef("w", "ward", kind="external_api"),
                           capability=capability, successful=self._reachable,
                           payload={"http_status": 200 if self._reachable else 503},
                           evidence={"verified_read": self._reachable,
                                     "pool_hit": True})


class _FakeGitHubObservation(ObservationTarget):
    """Adapter Ward 'repository' - mis. GitHub repo."""

    def __init__(self, private=True):
        self._private = private

    def observe(self, *, capability="observe"):
        return Observation(subject=SubjectRef("w2", "ward", kind="repository"),
                           capability=capability, successful=True,
                           payload={"private": self._private,
                                    "open_issues": 0},
                           evidence={"verified_read": True, "pool_hit": True})


class _FakeProcessObservation(ObservationTarget):
    """Adapter Ward 'process' - mis. service/daemon local."""

    def __init__(self, running=True):
        self._running = running

    def observe(self, *, capability="observe"):
        return Observation(subject=SubjectRef("w3", "ward", kind="process"),
                           capability=capability, successful=self._running,
                           payload={"pid": 1234 if self._running else None},
                           evidence={"verified_read": self._running})


class _FakeInvestigation(InvestigationTarget):
    def investigate(self, *, evidence, capability="investigate"):
        ok = bool(evidence.get("verified_read"))
        return InvestigationResult(
            subject=SubjectRef("w", "ward"),
            successful=True,
            findings=[{"label": "reachable" if ok else "unreachable",
                       "confidence": 0.9}],
            evidence_ref="", summary="x")


# --- helpers ---
def make_ward(repo, kind, resource, caps=("observe", "investigate", "protect")):
    ident = WardIdentity.new(kind, resource, seed="multi:{}:{}".format(kind, resource))
    repo.register(ident, owner=WardOwner(owner_id="owner-van"),
                  access_scope=WardAccessScope(scope=kind, resource=resource))
    repo.set_entrustment(Entrustment(
        ward_id=ident.ward_id, owner_id="owner-van",
        allowed_capabilities=caps, access_scope=kind,
        approval_policy=ApprovalPolicy(required=True, approver_role="operator"),
        created_at="t", revoked_at=""))
    return ident


def test_multi_ward_one_engine_all_observable():
    """Satu governor mengobservasi 3 jenis Ward berbeda - semua realizable."""
    repo = WardRepository()
    gov = WardGovernor(repo)
    w1 = make_ward(repo, "external_api", "status.example")
    w2 = make_ward(repo, "repository", "org/repo-a")
    w3 = make_ward(repo, "process", "svc-db")

    out1 = gov.observe(subject_ref(w1), _FakeLinkObservation(reachable=True))
    out2 = gov.observe(subject_ref(w2), _FakeGitHubObservation(private=True))
    out3 = gov.observe(subject_ref(w3), _FakeProcessObservation(running=True))

    assert out1.authorized and out1.observation.ok
    assert out2.authorized and out2.observation.ok
    assert out3.authorized and out3.observation.ok


def test_one_engine_not_duplicated_per_ward_type():
    """Tidak ada engine terpisah per jenis Ward - satu Governor dipakai semua."""
    repo = WardRepository()
    gov = WardGovernor(repo)
    for kind in ("repository", "external_api", "process", "database", "container"):
        ident = make_ward(repo, kind, "res-{}".format(kind))
        subj = subject_ref(ident)
        out = gov.observe(subj, _FakeLinkObservation(reachable=True))
        assert out.authorized
    # tetap satu file governor, bukan N varian
    import sam.ward.governance.governor as _g
    assert _g.WardGovernor is WardGovernor


def test_multi_ward_revoke_isolated():
    """Revoke satu Ward tidak memengaruhi Ward lain (isolasi)."""
    repo = WardRepository()
    gov = WardGovernor(repo)
    w1 = make_ward(repo, "external_api", "ep-1")
    w2 = make_ward(repo, "external_api", "ep-2")
    repo.revoke(w1.ward_id, revoked_at="t")

    out1 = gov.observe(subject_ref(w1), _FakeLinkObservation())
    out2 = gov.observe(subject_ref(w2), _FakeLinkObservation())
    assert not out1.authorized       # dicabut -> block
    assert out2.authorized           # yang lain tetap ok


def test_multi_ward_failure_not_universal():
    """Satu Ward gagal tidak membuat Ward lain gagal (no domino)."""
    repo = WardRepository()
    gov = WardGovernor(repo)
    w_down = make_ward(repo, "external_api", "down")
    w_up = make_ward(repo, "external_api", "up")
    out_down = gov.observe(subject_ref(w_down), _FakeLinkObservation(reachable=False))
    out_up = gov.observe(subject_ref(w_up), _FakeLinkObservation(reachable=True))
    assert not out_down.observation.ok
    assert out_up.observation.ok


def test_multi_ward_same_capability_different_adapter():
    """Capability 'observe' yang SAMA dipakai oleh semua adapter (no duplicate)."""
    repo = WardRepository()
    gov = WardGovernor(repo)
    for kind, adapter in (("repository", _FakeGitHubObservation()),
                          ("external_api", _FakeLinkObservation()),
                          ("process", _FakeProcessObservation())):
        ident = make_ward(repo, kind, "r-{}".format(kind))
        out = gov.observe(subject_ref(ident), adapter, capability="observe")
        assert out.authorized and out.observation.capability == "observe"


def subject_ref(ident):
    return SubjectRef(subject_id=ident.ward_id, subject_type="ward",
                      kind=ident.ward_type, name=ident.name)
