"""M14-008 tests — Real Credential Remediation (via boundary).

Fokus:
  - credential valid -> tidak remediasi (already available).
  - credential MISSING + tidak diotorisasi -> escalate, TIDAK remediasi.
  - credential MISSING + owner_supplied valid -> remediate + verify available.
  - replacement placeholder/terlalu pendek -> ditolak (no fake remediate).
  - nilai raw TIDAK pernah bocor ke hasil (masked saja).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.real_credential_remediation import (
    RealCredentialRemediation,
)
from sam.execution_runtime.credential_boundary import (
    CredentialBoundary, CredentialRequirement,
)
from sam.runtime_service.secrets.secret_provider import SecretProvider


def _req(env="SOME_TEST_KEY"):
    return CredentialRequirement(provider_id="prov", env_var=env, min_length=8)


def _boundary(env_map):
    return CredentialBoundary(provider=SecretProvider(env=dict(env_map)))


def _grant_auto():
    return DelegationGrant(
        ward_id="secret-prov", owner_id="owner",
        autonomy_level=AutonomyLevel.AUTONOMOUS,
        allowed_mutations=("protect",), requires_human_approval=False,
    )


class TestRealCredentialRemediation:
    async def test_already_available_no_remediation(self):
        boundary = _boundary({"SOME_TEST_KEY": "a" * 20})
        rem = RealCredentialRemediation(boundary)
        res = await rem.remediate(req=_req(), grant=_grant_auto())
        assert res.detected_status == "available"
        assert res.remediated is False

    async def test_missing_unauthorized_escalates(self):
        boundary = _boundary({})
        rem = RealCredentialRemediation(boundary)
        # grant human-required -> tidak boleh auto
        g = DelegationGrant(
            ward_id="s", owner_id="owner", autonomy_level=AutonomyLevel.AUTONOMOUS,
            allowed_mutations=("protect",), requires_human_approval=True,
        )
        res = await rem.remediate(req=_req(), grant=g)
        assert res.remediated is False
        assert "escalate" in res.reason.lower()

    async def test_missing_owner_supplied_valid_remediates(self):
        boundary = _boundary({})
        rem = RealCredentialRemediation(boundary)
        res = await rem.remediate(
            req=_req(), grant=_grant_auto(),
            new_value="secret-value-12345", owner_supplied=True,
        )
        assert res.remediated is True
        assert res.verified_status == "available"

    async def test_placeholder_replacement_rejected(self):
        boundary = _boundary({})
        rem = RealCredentialRemediation(boundary)
        res = await rem.remediate(
            req=_req(), grant=_grant_auto(),
            new_value="short", owner_supplied=True,
        )
        assert res.remediated is False
        # jangan pernah sukses palsu utk nilai tak valid

    async def test_no_self_create_without_owner_value(self):
        boundary = _boundary({})
        rem = RealCredentialRemediation(boundary)
        # owner_supplied False + new_value None -> SAM tidak menebak sendiri
        res = await rem.remediate(req=_req(), grant=_grant_auto())
        assert res.remediated is False
        assert "cannot self-create" in res.reason.lower()
