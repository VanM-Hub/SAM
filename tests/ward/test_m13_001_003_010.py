# Tests M13-001..003 + M13-010 - Ward Foundation, Registry, Entrustment, Boundary
# No external calls. Pure domain/registry/boundary logic.
import pytest

from sam.ward.identity.models import (WardIdentity, Ward, WardOwner, WardAccessScope,
                                      WardMetadata)
from sam.ward.entrustment.models import Entrustment, ApprovalPolicy
from sam.ward.registry.registry import WardRepository, WardConflictError, WardNotFoundError
from sam.ward.governance.boundary import WardGovernanceBoundary


def make_github_ward():
    ident = WardIdentity.new("repository", "VanM-Hub/SAM",
                             seed="github:VanM-Hub/SAM")
    owner = WardOwner(owner_id="owner-van", owner_name="Van", owner_role="owner")
    scope = WardAccessScope(scope="github:VanM-Hub/SAM",
                            resource="VanM-Hub/SAM",
                            endpoints=("read",))
    return ident, owner, scope


def make_entrustment(ward_id, caps=("observe", "investigate", "protect")):
    return Entrustment(
        ward_id=ward_id, owner_id="owner-van", allowed_capabilities=caps,
        access_scope="github:VanM-Hub/SAM",
        approval_policy=ApprovalPolicy(required=True, approver_role="operator"),
        created_at="2026-08-14T00:00:00Z", revoked_at="")


# ---------------- M13-001 Ward Identity ----------------

def test_ward_identity_normalized_and_deterministic():
    a = WardIdentity.new("repository", "VanM-Hub/SAM", seed="s")
    b = WardIdentity.new("REPOSITORY", "VanM-Hub/SAM   ", seed="s")
    assert a.ward_id == b.ward_id          # normalisasi + deterministik
    assert a.ward_type == "repository"
    assert a.is_known
    assert a.name == "VanM-Hub/SAM"


def test_ward_identity_unknown_type():
    w = WardIdentity(ward_id="x", ward_type="mystery", name="n")
    assert w.ward_type == "unknown"
    assert not w.is_known


def test_ward_identity_immutable_frozen():
    w = WardIdentity.new("container", "pg", seed="c")
    with pytest.raises(Exception):  # frozen dataclass -> tidak bisa mutate
        w.ward_type = "database"


def test_ward_model_status_normalized():
    w = Ward(identity=WardIdentity.new("host", "vm", seed="h"), status="revoked")
    assert w.is_revoked
    assert not w.is_active


def test_known_ward_types_all_listed():
    for t in ("application", "service", "repository", "container",
              "database", "host", "filesystem", "external_api"):
        assert WardIdentity.new(t, "x", seed=t).ward_type == t


# ---------------- M13-002 Ward Registry ----------------

def test_registry_register_get_list():
    repo = WardRepository()
    ident, owner, scope = make_github_ward()
    repo.register(ident, owner=owner, access_scope=scope, registered_at="t0")
    got = repo.get(ident.ward_id)
    assert got is not None
    assert got.identity.ward_id == ident.ward_id
    assert got.owner.owner_id == "owner-van"
    assert repo.count() == 1
    listed = repo.list()
    assert len(listed) == 1


def test_registry_duplicate_conflict():
    repo = WardRepository()
    ident, _, _ = make_github_ward()
    repo.register(ident)
    with pytest.raises(WardConflictError):
        repo.register(ident)


def test_registry_unique_ids():
    a = WardIdentity.new("repository", "repo-a", seed="a")
    b = WardIdentity.new("repository", "repo-b", seed="b")
    assert a.ward_id != b.ward_id


def test_registry_identity_immutable_after_overwrite():
    repo = WardRepository()
    ident, owner, scope = make_github_ward()
    repo.register(ident, owner=owner, access_scope=scope)
    # overwrite ganti metadata, identity TETAP sama
    repo.register(ident, owner=WardOwner(owner_id="owner-x"),
                  access_scope=scope, overwrite=True)
    w = repo.get(ident.ward_id)
    assert w.identity.ward_id == ident.ward_id      # immutable
    assert w.owner.owner_id == "owner-x"            # metadata berubah


def test_registry_does_not_execute_observe_restart_delete_mutate():
    # Repository TIDAK punya method tsb - pastikan tidak ada atribut eksekusi.
    repo = WardRepository()
    for forbidden in ("execute", "observe", "restart", "delete", "mutate",
                      "start", "stop", "run"):
        assert not hasattr(repo, forbidden), forbidden


def test_registry_update_metadata_and_revoke():
    repo = WardRepository()
    ident, _, _ = make_github_ward()
    repo.register(ident, registered_at="t0")
    repo.update_metadata(ident.ward_id, description="repo utama")
    w = repo.get(ident.ward_id)
    assert w.metadata.description == "repo utama"
    repo.revoke(ident.ward_id, revoked_at="t1")
    assert repo.get(ident.ward_id).is_revoked
    # masih bisa di-list (identity ada), tapi status revoked
    assert len(repo.list(status="revoked")) == 1


def test_registry_revoke_not_found_raises():
    repo = WardRepository()
    with pytest.raises(WardNotFoundError):
        repo.revoke("ward-nope")


# ---------------- M13-003 Entrustment / Consent ----------------

def test_entrustment_active_and_allows():
    ent = make_entrustment("ward-1")
    assert ent.is_active
    assert ent.allows("observe")
    assert ent.allows("protect")          # mutation dengan approval policy required
    assert ent.ward_id == "ward-1"
    assert ent.owner_id == "owner-van"


def test_entrustment_revoked_blocks_all():
    ent = make_entrustment("ward-1")
    ent = Entrustment(ward_id=ent.ward_id, owner_id=ent.owner_id,
                      allowed_capabilities=ent.allowed_capabilities,
                      access_scope=ent.access_scope,
                      approval_policy=ent.approval_policy,
                      created_at=ent.created_at, revoked_at="2026-08-14T12:00:00Z")
    assert not ent.is_active
    assert not ent.allows("observe")
    assert not ent.allows("protect")


def test_registered_ward_without_entrustment_not_authorized():
    # Registered Ward != permission - tanpa konsen Owner, observasi ditolak.
    repo = WardRepository()
    ident, _, _ = make_github_ward()
    repo.register(ident)
    boundary = WardGovernanceBoundary(repo)
    assert not boundary.can_observe(ident.ward_id).allowed
    assert not boundary.can_mutate(ident.ward_id).allowed


# ---------------- M13-010 Governance Boundary ----------------

def test_boundary_observation_granted():
    repo = WardRepository()
    ident, owner, scope = make_github_ward()
    repo.register(ident, owner=owner, access_scope=scope)
    repo.set_entrustment(make_entrustment(ident.ward_id))
    b = WardGovernanceBoundary(repo)
    res = b.can_observe(ident.ward_id)
    assert res.allowed
    assert not res.requires_approval


def test_boundary_mutation_requires_approval():
    repo = WardRepository()
    ident, owner, scope = make_github_ward()
    repo.register(ident, owner=owner, access_scope=scope)
    repo.set_entrustment(make_entrustment(ident.ward_id, caps=("observe", "protect")))
    b = WardGovernanceBoundary(repo)
    res = b.can_mutate(ident.ward_id)
    assert res.allowed
    assert res.requires_approval            # mutation selalu butuh approval


def test_boundary_mutation_blocked_without_protect_cap():
    repo = WardRepository()
    ident, owner, scope = make_github_ward()
    repo.register(ident, owner=owner, access_scope=scope)
    repo.set_entrustment(make_entrustment(ident.ward_id, caps=("observe",)))
    b = WardGovernanceBoundary(repo)
    res = b.can_mutate(ident.ward_id)
    assert not res.allowed
    assert "not granted" in res.reason


def test_boundary_revoked_blocks_observation_and_mutation():
    repo = WardRepository()
    ident, owner, scope = make_github_ward()
    repo.register(ident, owner=owner, access_scope=scope)
    repo.set_entrustment(make_entrustment(ident.ward_id))
    repo.revoke(ident.ward_id, revoked_at="t")
    b = WardGovernanceBoundary(repo)
    assert not b.can_observe(ident.ward_id).allowed
    assert not b.can_mutate(ident.ward_id).allowed


def test_boundary_unregistered_ward_blocked():
    b = WardGovernanceBoundary(WardRepository())
    assert not b.can_observe("ward-none").allowed
    assert not b.can_mutate("ward-none").allowed


def test_boundary_general_dispatch_unknown_capability():
    repo = WardRepository()
    ident, owner, scope = make_github_ward()
    repo.register(ident, owner=owner, access_scope=scope)
    repo.set_entrustment(make_entrustment(ident.ward_id))
    b = WardGovernanceBoundary(repo)
    assert not b.check(ident.ward_id, "bogus").allowed
