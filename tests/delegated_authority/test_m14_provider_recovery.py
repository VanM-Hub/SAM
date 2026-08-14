"""M14-007 tests — Real Provider Recovery (auto-failover).

Harness + failover logic DIUJI deterministik (provider mock via ping_fn &
executor stub). Real E2E (network nyata ke provider hidup) terpisah & jujur:
di sini kami buktikan LOGIKA failover + boundary authority, bukan klaim
"provider X real online" (itu butuh env + network, ditandai test real E2E
terpisah).

Fokus:
  - primary sehat -> tidak ada failover.
  - primary gagal + alternatif sehat + grant auto -> switch, COMPLETED.
  - primary gagal + grant human-required -> ESCALATE (tidak auto-switch).
  - tanpa alternatif sehat -> FAILED honest.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.real_provider_recovery import (
    ProviderRecovery, ProviderHealthProbe,
)


class _StubExecutor:
    """Stub ProviderExecutor: available() berdasarkan peta sehat/tidak."""

    def __init__(self, healthy_map):
        self._healthy = healthy_map  # {pid: bool}

    def available(self, provider_id):
        return self._healthy.get(provider_id, False)

    def execute(self, provider_id, operation, payload=None, timeout_seconds=60):
        if not self._healthy.get(provider_id, False):
            raise RuntimeError(f"provider {provider_id} unavailable")
        return {
            "provider_id": provider_id, "operation": operation,
            "status": "completed", "external_calls": 1,
            "payload": {"choices": [{"message": {"content": "ok"}}]},
        }


def _grant_auto():
    return DelegationGrant(
        ward_id="p", owner_id="owner", autonomy_level=AutonomyLevel.AUTONOMOUS,
        allowed_mutations=("protect",), requires_human_approval=False,
    )


def _grant_human():
    return DelegationGrant(
        ward_id="p", owner_id="owner", autonomy_level=AutonomyLevel.AUTONOMOUS,
        allowed_mutations=("protect",), requires_human_approval=True,
    )


class TestProviderHealthProbe:
    def test_available_but_not_pinged(self):
        ex = _StubExecutor({"ollama": True})
        probe = ProviderHealthProbe(ex)
        r = probe.probe("ollama")
        assert r.available is True
        assert r.healthy is True

    def test_unavailable_honest(self):
        ex = _StubExecutor({"ollama": False})
        probe = ProviderHealthProbe(ex)
        r = probe.probe("ollama")
        assert r.available is False
        assert r.healthy is False


class TestProviderRecovery:
    async def test_primary_healthy_no_failover(self):
        ex = _StubExecutor({"p": True, "a": True})
        rec = ProviderRecovery(ex, probe_map={"p": lambda: True})
        res = await rec.recover(primary="p", candidates=["a"], grant=_grant_auto())
        assert res.failed is False
        assert res.switched_to is None

    async def test_failover_to_healthy_alternative_when_authorized(self):
        ex = _StubExecutor({"p": False, "a": True, "b": True})
        rec = ProviderRecovery(ex, probe_map={"p": lambda: False, "a": lambda: True})
        res = await rec.recover(primary="p", candidates=["a", "b"], grant=_grant_auto())
        assert res.failed is True
        assert res.switched_to == "a"
        assert res.outcome is not None
        assert res.outcome.ok is True

    async def test_human_required_escalates_no_switch(self):
        ex = _StubExecutor({"p": False, "a": True})
        rec = ProviderRecovery(ex, probe_map={"p": lambda: False, "a": lambda: True})
        res = await rec.recover(primary="p", candidates=["a"], grant=_grant_human())
        assert res.failed is True
        assert res.switched_to is None      # tidak auto-switch
        assert res.outcome.ok is False

    async def test_no_healthy_alternative_failed_honest(self):
        ex = _StubExecutor({"p": False, "a": False, "b": False})
        rec = ProviderRecovery(ex, probe_map={
            "p": lambda: False, "a": lambda: False, "b": lambda: False,
        })
        res = await rec.recover(primary="p", candidates=["a", "b"], grant=_grant_auto())
        assert res.failed is True
        assert res.switched_to is None
        assert res.outcome.ok is False
