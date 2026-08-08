# IP-3.4-001 WP-10 - End-to-end Federation Certification test
# Federation Foundation (AO-3.4-001 / ED-3.4-001)
#
# Definisi Done IP-3.4-001: beberapa Citizen Ecosystem yang berdaulat dapat
# saling MENGENALI dan BERTUKAR capability melalui contract - secara
# deterministik, observasional, dan TANPA authority. Bukan distributed
# runtime: tidak ada remote execution, tidak ada distributed scheduler,
# tidak ada global governance.
#
# Guardrail IP-3.4-001 dikunci:
#   Federation != Central Governance; Registry != Control Plane;
#   Capability Exchange != Execution; Discovery != Connection;
#   Health != Monitoring Control; Descriptor != Contract Execution;
#   Federation Identity != Global Identity; Sovereignty First.

import os

import pytest

from sam.citizen.federation.identity import (
    FederationIdentity,
    FederationMember,
    FederationInstance,
)
from sam.citizen.federation.registry import FederationRegistry
from sam.citizen.federation.discovery import FederationDiscovery
from sam.citizen.federation.descriptor import (
    FederationDescriptor,
    build_federation_descriptor,
)
from sam.citizen.federation.capability_exchange import (
    CapabilityAdvertisement,
    CapabilityExchange,
)
from sam.citizen.federation.health import (
    FederationHealth,
    FederationHealthAssessor,
)
from sam.citizen.federation.api import FederationAPI
from sam.citizen.federation.compliance import (
    compliance_check,
    default_source_files,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FED_ROOT = os.path.join(_ROOT, "src", "sam", "citizen", "federation")


@pytest.fixture
def federation():
    fed = FederationIdentity("fed-01", "SAM Federation",
                             "antar Citizen Ecosystem")
    member_a = FederationMember("ecosystem-a", local_identity="sam-a-id",
                                endpoint="desc://sam-a/cap.json",
                                state="advertised")
    member_b = FederationMember("ecosystem-b", local_identity="sam-b-id",
                                endpoint="desc://sam-b/cap.json",
                                state="observed")
    reg = FederationRegistry()
    reg.register(member_a)
    reg.register(member_b)
    d_a = build_federation_descriptor(
        "ecosystem-a", capability=("health-check", "audit"),
        contracts=("health", "audit"), version="1.0")
    d_b = build_federation_descriptor(
        "ecosystem-b", capability=("generate", "translate"),
        contracts=("llm",), version="1.2")
    alpha = FederationAPI(reg, descriptors=(d_a, d_b),
                          healths={"ecosystem-a": "healthy",
                                   "ecosystem-b": "degraded"},
                          federation=fed)
    return fed, member_a, member_b, reg, d_a, d_b, alpha


# --------------------------------------------------------------------------
# WP-01 Federation Identity
# --------------------------------------------------------------------------

def test_federation_identity_immutable(federation):
    fed, member_a, _b, _r, _da, _db, _a = federation
    assert fed.federation_id == "fed-01"
    with pytest.raises(Exception):
        fed.federation_id = "changed"  # immutable


def test_member_keeps_local_identity(federation):
    _fed, member_a, _b, _r, _da, _db, _a = federation
    # Federation Identity != Global Identity: local dipertahankan
    assert member_a.local_identity == "sam-a-id"
    assert not hasattr(member_a, "global_identity")
    assert member_a.is_sovereign  # Sovereignty First


def test_federation_instance_grouping(federation):
    fed, member_a, member_b, _r, _da, _db, _a = federation
    inst = FederationInstance("fi-1", fed, (member_a, member_b))
    assert inst.member_ids() == ("ecosystem-a", "ecosystem-b")
    assert inst.has_member("ecosystem-a")
    assert not inst.has_member("ecosystem-x")


# --------------------------------------------------------------------------
# WP-02 Federation Registry (metadata, bukan control plane)
# --------------------------------------------------------------------------

def test_registry_metadata_only(federation):
    _fed, _a, _b, reg, _da, _db, _a = federation
    assert reg.count() == 2
    assert "ecosystem-a" in reg.member_ids()
    # registry hanya menyimpan metadata - tidak mengontrol node
    assert not hasattr(reg, "control_node")
    assert not hasattr(reg, "start_remote")


def test_registry_readonly_get_all(federation):
    _fed, _a, _b, reg, _da, _db, _a = federation
    member = reg.get("ecosystem-a")
    assert member.local_identity == "sam-a-id"


# --------------------------------------------------------------------------
# WP-03 Federation Discovery (registry-based, tidak connect)
# --------------------------------------------------------------------------

def test_discovery_registry_based(federation):
    _fed, _a, _b, reg, da, _db, alpha = federation
    disc = FederationDiscovery(reg, (da,))
    # discovery = pencarian registry, bukan koneksi
    assert not hasattr(disc, "connect")
    assert not hasattr(disc, "handshake")
    # semua member yang terdaftar di registry ditemukan
    assert set(disc.discover_all()) == {"ecosystem-a", "ecosystem-b"}


def test_discovery_by_capability(federation):
    _fed, _a, _b, _r, _da, _db, alpha = federation
    assert alpha.discover("audit") == ("ecosystem-a",)
    assert alpha.discover("translate") == ("ecosystem-b",)
    assert alpha.discover("no-such") == ()


# --------------------------------------------------------------------------
# WP-04 Federation Descriptor (deklaratif)
# --------------------------------------------------------------------------

def test_descriptor_declarative(federation):
    _fed, _a, _b, _r, da, _db, _a = federation
    assert da.is_declarative is True
    assert da.has_capability("audit")
    assert da.supports_contract("health")
    assert not hasattr(da, "execute")
    assert not hasattr(da, "invoke")


def test_descriptor_compat_cert_fields(federation):
    _fed, _a, _b, _r, _da, _db, _a = federation
    d = build_federation_descriptor(
        "ecosystem-c", capability=("serve",), contracts=("http",),
        version="2.0",
        compatibility=(("ecosystem-a", {"compatible": True}),),
        certification=("defined", {"checks": 3}))
    assert d.version == "2.0"
    assert d.compatibility == (("ecosystem-a", {"compatible": True}),)
    assert d.certification == ("defined", {"checks": 3})


# --------------------------------------------------------------------------
# WP-05 Capability Exchange (advertisement, bukan execution)
# --------------------------------------------------------------------------

def test_capability_advertisement_not_execution(federation):
    _fed, _a, _b, _r, _da, _db, alpha = federation
    adv_a = alpha.capabilities("ecosystem-a")
    assert isinstance(adv_a, CapabilityAdvertisement)
    assert adv_a.is_advertisement is True
    assert adv_a.is_execution is False
    assert "audit" in adv_a.capabilities


def test_exchange_who_advertises(federation):
    _fed, _a, _b, _r, da, db, _a = federation
    ex = CapabilityExchange((da, db))
    assert ex.who_advertises("generate") == ("ecosystem-b",)
    assert ex.who_advertises("audit") == ("ecosystem-a",)


def test_advertised_all_capabilities(federation):
    _fed, _a, _b, _r, _da, _db, alpha = federation
    ads = alpha.advertised()
    assert set(ads) == {"health-check", "audit", "generate", "translate"}


# --------------------------------------------------------------------------
# WP-06 Federation Health (observasional)
# --------------------------------------------------------------------------

def test_health_observational(federation):
    _fed, _a, _b, _r, _da, _db, alpha = federation
    h = alpha.health()
    assert h.overall == "degraded"
    assert h.healthy_count == 1
    assert h.degraded_count == 1
    # observasi, bukan kontrol/monitoring control
    assert not hasattr(alpha, "restart_remote")
    assert not hasattr(alpha, "control_runtime")


def test_health_aggregate_deterministic(federation):
    _fed, _a, _b, _r, _da, _db, alpha = federation
    h1 = alpha.health()
    h2 = alpha.health()
    assert h1.as_dict() == h2.as_dict()


# --------------------------------------------------------------------------
# WP-07 Federation API (read-only)
# --------------------------------------------------------------------------

def test_api_read_only(federation):
    _fed, _a, _b, reg, _da, _db, alpha = federation
    before = reg.count()
    alpha.discover()
    alpha.describe("ecosystem-a")
    alpha.capabilities("ecosystem-a")
    alpha.health()
    # tidak ada member bertambah, tidak ada kontrol
    assert reg.count() == before
    assert not hasattr(alpha, "connect")
    assert not hasattr(alpha, "execute")
    assert not hasattr(alpha, "invoke_remote")
    assert not hasattr(alpha, "approve_shared")
    assert not hasattr(alpha, "control_node")


def test_api_discover_describe_capabilities_health(federation):
    _fed, _a, _b, _r, _da, _db, alpha = federation
    assert alpha.discover() == ("ecosystem-a", "ecosystem-b")
    assert alpha.describe("ecosystem-a").local_identity == "sam-a-id"
    assert alpha.capabilities("ecosystem-a").capabilities == \
        ("health-check", "audit")
    assert alpha.health().overall == "degraded"


def test_registry_authoritative(federation):
    _fed, _a, _b, _r, _da, _db, alpha = federation
    # deskripsi capability diambil dari descriptor, bukan ditebak
    assert alpha.discover("translate") == ("ecosystem-b",)
    # member yang tidak dikenal tidak muncul
    assert alpha.describe("ghost") is None


# --------------------------------------------------------------------------
# WP-08 Federation Compliance
# --------------------------------------------------------------------------

def test_federation_compliance_suite_passed():
    files = default_source_files(_FED_ROOT)
    passed, checks = compliance_check(files, module_root=_FED_ROOT)
    assert passed
    assert sum(1 for c in checks if c.passed) == len(checks)


# --------------------------------------------------------------------------
# WP-10 Exit criteria (sentence-level)
# --------------------------------------------------------------------------

def test_federation_not_distributed_runtime(federation):
    """Federation mengenali & bertukar capability, BUKAN menjalankan remote."""
    _fed, _a, _b, _r, _da, _db, alpha = federation
    # tidak ada eksekusi remote: capability hanya diiklankan
    assert alpha.capabilities("ecosystem-a").is_execution is False
    assert not hasattr(alpha, "execute")
    assert not hasattr(alpha, "run_remote")
    assert not hasattr(alpha, "remote_execute")
    # tidak ada distributed scheduler / global governance
    assert not hasattr(alpha, "schedule")
    assert not hasattr(alpha, "global_governance")


def test_exit_criteria_end_to_end(federation):
    """Ekosistem berdaulat saling mengenali & bertukar capability via
    contract - deterministik, observasional, tanpa authority."""
    _fed, _a, _b, _r, _da, _db, alpha = federation

    # Saling mengenali (discovery - registry-based)
    assert set(alpha.discover()) == {"ecosystem-a", "ecosystem-b"}

    # Bertukar capability (advertisement, bukan eksekusi)
    assert "audit" in alpha.capabilities("ecosystem-a").capabilities
    assert alpha.discover("translate") == ("ecosystem-b",)

    # Melalui contract (deskriptif)
    assert alpha.describe("ecosystem-a").member_id == "ecosystem-a"

    # Kesehatan observasional
    assert alpha.health().overall in ("healthy", "degraded", "unknown")

    # Tanpa authority & tanpa control
    assert not hasattr(alpha, "execute")
    assert not hasattr(alpha, "connect")
    assert not hasattr(alpha, "approve_shared")
    assert not hasattr(alpha, "control_node")

    # Sovereignty: identitas lokal dipertahankan oleh tiap ecosystem
    assert alpha.describe("ecosystem-a").local_identity == "sam-a-id"
    assert alpha.describe("ecosystem-b").local_identity == "sam-b-id"
