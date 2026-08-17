"""ward/bootstrap.py — bootstrap Ward canonical (W1).

Keputusan Van W1:
  - OpenClaw adalah Ward Lab pertama.
  - Explicitness: Registration != authority; entrustment (konsen Owner) eksplisit.
  - Tenant boundary: Ward/Entrustment harus terbukti ownership-nya — owner_id
    harus cocok dgn tenant (username) yang terautentikasi (AD-ENG-006).

Modul ini menyediakan `bootstrap_openclaw_ward(manager, tenant_username)` yang
MENDaftarkan OpenClaw sbg Ward (`application`) + entrustment read-only
environment.observe, IDEMPOTEN (tidak menimpa entri / konsen yang sudah ada).

TIDAK mengeksekusi apa pun (repo + entrustment murni data). Tidak menyimpan
credential. Capability scope: hanya observe (W1 read-only; mutation TIDAK
diaktifkan — Van #4).

Dipanggil dari composition root canonical (ward/wiring.build_ward_manager)
agar OpenClaw ter-resolve sbg Ward di server nyata (accept B/C W1).
"""
from __future__ import annotations

from typing import Optional

from sam.ward.entrustment.models import ApprovalPolicy, Entrustment
from sam.ward.identity.models import WardAccessScope, WardIdentity, WardOwner, WardMetadata
from sam.ward.manager import WardManager

# Jenis Ward OpenClaw: external entrusted application (M13 taxonomy).
_OPENCLAW_WARD_TYPE = "application"
_OPENCLAW_NAME = "OpenClaw"
_OPENCLAW_SEED = "openclaw:ward:samlabs"
_DEFAULT_OWNER = "van"  # tenant operator (AD-ENG-006; users = van/operator)


def openclaw_ward_identity() -> WardIdentity:
    """Identity deterministic OpenClaw Ward (immutable)."""
    return WardIdentity.new(
        _OPENCLAW_WARD_TYPE, _OPENCLAW_NAME, seed=_OPENCLAW_SEED,
    )


def openclaw_entrustment(
    owner_username: str, *, revoked_at: str = "", created_at: str = "",
) -> Entrustment:
    """Entrustment konsen Owner utk OpenClaw Ward.

    - owner_id = tenant (username) yang mempercayakan -> ownership terbukti
      (cross-tenant access -> fail-closed di WardManager.auth_ward).
    - allowed_capabilities = read-only observation scope (W1).
    - approval_policy: observation selalu non-mutating; mutation (protect/mutate)
      TIDAK diberikan di W1 (hanya scope observe) — Van #4.
    """
    identity = openclaw_ward_identity()
    return Entrustment(
        ward_id=identity.ward_id,
        owner_id=(owner_username or _DEFAULT_OWNER).strip() or _DEFAULT_OWNER,
        allowed_capabilities=("observe", "investigate", "diagnose", "recommend"),
        access_scope="openclaw:observe:environment",
        approval_policy=ApprovalPolicy(required=True, approver_role="operator",
                                       timeout_seconds=3600),
        created_at=created_at or "", revoked_at=revoked_at,
    )


def bootstrap_openclaw_ward(
    manager: WardManager,
    owner_username: Optional[str] = None,
) -> str:
    """Daftarkan OpenClaw Ward + entrustment (idempotent) ke composition root.

    Return ward_id OpenClaw. Idempotent: bila OpenClaw sudah terdaftar, TIDAK
    menimpa entri/konsen yang ada (aman dipanggil berulang / saat restart).
    """
    owner = (owner_username or "").strip() or _DEFAULT_OWNER
    identity = openclaw_ward_identity()

    existing = manager.repository.get(identity.ward_id)
    if existing is not None:
        # entrustment mungkin belum ada (migrasi) -> lengkapi, tanpa menimpa.
        if manager.repository.get_entrustment(identity.ward_id) is None:
            manager.repository.set_entrustment(openclaw_entrustment(owner))
        return identity.ward_id

    manager.register_ward(
        identity,
        owner=WardOwner(owner_id=owner, owner_name=owner, owner_role="operator"),
        access_scope=WardAccessScope(scope="openclaw:observe:environment",
                                     resource="openclaw",
                                     endpoints=("read",)),
        metadata=WardMetadata(
            description="OpenClaw Ward Lab pertama (W1) - external entrusted "
                        "application, observe read-only via M14 canonical"),
        entrustment=openclaw_entrustment(owner),
        origin="ward.bootstrap:w1",
    )
    return identity.ward_id
