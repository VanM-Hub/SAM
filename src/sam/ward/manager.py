"""WardManager — composition root Ward (W1).

Menyatukan keputusan Van W1 (2026-08-17):
  - Persistence PostgreSQL via existing Repository Pattern (bukan JSON baru).
  - OpenClaw = Ward Lab pertama (bukan GitHub/local-machine).
  - Tenant boundary WAJIB (reuse AD-ENG-006 session) — cross-tenant fail-closed.
  - Capability scope awal: environment.observe/investigate/diagnose/recommend
    (read-only). Mutation TIDAK diaktifkan di W1.
  - Wire existing: WardRepository + WardGovernanceBoundary + capability
    contracts + credential boundary + existing runtime, lewat composition root
    canonical. TIDAK membuat execution pipeline kedua.

Design:
  - `WardManager` memegang satu `WardRepository` (dgn persistence opsional)
    dan satu `WardGovernanceBoundary`.
  - `resolve_ward(target, tenant)` -> SubjectRef ATAU AuthorizationResult
    refused. Menerjemahkan target bernama (mis. "openclaw") ke Ward yang
    terdaftar, lalu memeriksa tenant ownership + status + entrustment +
    capability scope. Cross-tenant / tanpa entrustment / revoked -> refused
    (fail-closed).
  - `gate(operation, subject)` -> AuthorizationResult dari boundary yg sama.
  - Persistence: bila `SAM_PG_DSN`/SAM_ENV=production -> PostgresWardStore
    (plugin), selain itu InMemory (regresi M10/M13 aman).

  LOCAL-MACHINE vs WARD:
  local-machine adalah Citizen environment (governed internal, bukan Ward
  eksternal). Ia TIDAK lewat WardRepository/gate Ward — tetap citizen di
  jalur EnvironmentDiscovery. Hanya target BUKAN local-machine yang di-resolve
  sebagai Ward eksternal (mis. OpenClaw). Ini menjawab #6 Van: jangan sembarang
  ubah local-machine jadi Ward.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sam.ward.capability.contracts import SubjectRef
from sam.ward.entrustment.models import Entrustment
from sam.ward.governance.boundary import WardGovernanceBoundary, AuthorizationResult
from sam.ward.registry.registry import WardRepository

# Nama target citizen murni yang TIDAK boleh di-resolve sbg Ward eksternal.
# local-machine = governed citizen environment (EnvironmentDiscovery),
# dijamin tetap citizen (Van #6).
_CITIZEN_ENV_TARGETS = ("local-machine", "local", "localhost", "127.0.0.1")


@dataclass(frozen=True)
class WardResolution:
    """Hasil resolve target -> subject (sukses) / refusal (fail-closed)."""

    ok: bool
    subject: Optional[SubjectRef] = None
    refused: bool = False
    reason: str = ""
    ward_id: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "subject": self.subject.as_dict() if self.subject else None,
            "refused": self.refused,
            "reason": self.reason,
            "ward_id": self.ward_id,
        }


def _tenant_owns(ent: Entrustment, tenant: Optional[Dict[str, str]]) -> bool:
    """Apakah entrustment dimiliki tenant ini? Cross-tenant -> False (fail-closed).

    tenant None (anonymous) -> False: tanpa identitas terverifikasi, access
    Ward eksternal ditolak (tidak ada anonymous ward access).
    """
    if not tenant:
        return False
    owner = (ent.owner_id or "").strip()
    username = (tenant.get("username") or "").strip()
    if not owner:
        return False
    # owner_id bisa berbentuk "user:van" atau "van" — cocokkan bagian username.
    return owner.split(":")[-1] == username


class WardManager:
    """Composition root Ward: repo + boundary + resolve + gate.

    TIDAK mengeksekusi apa pun (repos + boundary murni keputusan). Execution
    tetap via runner -> adapter -> existing runtime (tidak ada pipeline kedua).
    """

    _CAP_READONLY = frozenset(
        {"observe", "investigate", "diagnose", "recommend", "verify", "learn"}
    )

    def __init__(
        self,
        repository: Optional[WardRepository] = None,
        boundary: Optional[WardGovernanceBoundary] = None,
        persistence=None,
        tenant: Optional[Dict[str, str]] = None,
    ) -> None:
        self._repo = repository or WardRepository(persistence=persistence)
        self._boundary = boundary or WardGovernanceBoundary(self._repo)
        # tenant aktif utk sesi ini (dari SessionStore.authenticate, AD-ENG-006).
        self._tenant = tenant

    # -- akses repo/boundary (kontrak M13, single source) ------------------

    @property
    def repository(self) -> WardRepository:
        return self._repo

    @property
    def boundary(self) -> WardGovernanceBoundary:
        return self._boundary

    def with_tenant(self, tenant: Optional[Dict[str, str]]) -> "WardManager":
        """Clone manager dgn tenant aktif (immutable-ish; repo/boundary sama)."""
        return WardManager(
            repository=self._repo, boundary=self._boundary,
            tenant=tenant,
        )

    # -- registrasi (setup, bukan runtime access) ---------------------------

    def register_ward(
        self,
        identity,
        *,
        owner,
        access_scope,
        entrustment: Entrustment,
        metadata=None,
        origin: str = "",
    ) -> str:
        """Daftarkan Ward + entrustment (konsen Owner) secara eksplisit.

        Return ward_id deterministik. Identity immutable.
        """
        self._repo.register(
            identity, owner=owner, access_scope=access_scope,
            metadata=metadata, entrustment=entrustment, origin=origin,
        )
        return identity.ward_id

    # -- resolve (tenant -> ward) -------------------------------------------

    def is_citizen_env_target(self, target: str) -> bool:
        """Apakah target adalah citizen environment (local-machine, dll)?"""
        t = (target or "").strip().lower()
        return t in _CITIZEN_ENV_TARGETS

    def resolve_ward(self, target: str) -> WardResolution:
        """Resolve target bernama -> Ward terdaftar (tanpa tenant check).

        Dipakai UNTUK memeriksa keberadaan Ward. Gate tenant dilakukan di
        `auth_ward` (resolve + tenant + status + scope) sebelum eksekusi.
        citizen target -> refused (bukan Ward) dengan reason jelas.
        """
        t = (target or "").strip()
        if not t:
            return WardResolution(False, refused=True, reason="target kosong")
        if self.is_citizen_env_target(t):
            return WardResolution(
                False, refused=True, reason=f"'{t}' adalah citizen environment, bukan Ward eksternal"
            )
        # coba resolve by name untuk memudahkan UX ("openclaw") lalu by id.
        ward = None
        found_id = ""
        for w in self._repo.list():
            if w.name.lower() == t.lower():
                ward = w
                found_id = w.identity.ward_id
                break
        if ward is None:
            ward = self._repo.get(t)
            if ward is not None:
                found_id = t
        if ward is None:
            return WardResolution(False, refused=True,
                                  reason=f"Ward '{t}' tidak terdaftar (refused)")
        return WardResolution(
            True,
            subject=SubjectRef(subject_id=found_id, subject_type="ward",
                               kind=ward.ward_type, name=ward.name),
            ward_id=found_id,
        )

    def auth_ward(self, target: str, operation: str) -> WardResolution:
        """RESOLVE + AUTHORIZE target sbg Ward (tenant + status + scope).

        Adalah SATU gerbang yang dipakai runner SEBELUM adapter dipanggil.
        Fail-closed: revoked / tanpa entrustment / cross-tenant / cap tak
        diizinkan -> refused (TIDAK dieksekusi).

        operation memetakan ke capability:
          environment.observe     -> observe
          environment.investigate -> investigate
          environment.diagnose    -> diagnose
          environment.recommend   -> recommend
        """
        op = (operation or "").strip()
        resolved = self.resolve_ward(target)
        if not resolved.ok:
            return resolved

        # 1) status ward active (bukan revoked)
        ward = self._repo.get(resolved.ward_id)
        if ward is None or ward.is_revoked:
            return WardResolution(
                False, refused=True, reason="Ward revoked atau tidak ditemukan",
                ward_id=resolved.ward_id)

        # 2) entrustment ada + tenant ownership (cross-tenant -> fail)
        ent = self._repo.get_entrustment(resolved.ward_id)
        if ent is None or not ent.is_active:
            return WardResolution(
                False, refused=True,
                reason="tidak ada entrustment aktif (konsen Owner hilang/cabut)",
                ward_id=resolved.ward_id)
        if not _tenant_owns(ent, self._tenant):
            return WardResolution(
                False, refused=True,
                reason="cross-tenant: tenant saat ini bukan pemilik entrustment Ward ini (fail-closed)",
                ward_id=resolved.ward_id)

        # 3) capability scope (read-only environment.*)
        capability = _operation_to_capability(op)
        if capability not in self._CAP_READONLY:
            return WardResolution(
                False, refused=True,
                reason=f"capability '{capability}' di luar scope read-only W1 (mutation diblokir)",
                ward_id=resolved.ward_id)
        auth: AuthorizationResult = self._boundary.can_observe(
            resolved.ward_id, capability)
        if not auth.allowed:
            return WardResolution(
                False, refused=True, reason=auth.reason, ward_id=resolved.ward_id)

        return resolved  # ok=True, siap eksekusi via adapter

    def gate(self, operation: str, subject: SubjectRef) -> AuthorizationResult:
        """Gate boundary (defense in depth) utk subject yang sudah resolved."""
        capability = _operation_to_capability(operation)
        if capability in self._CAP_READONLY:
            return self._boundary.can_observe(subject.subject_id, capability)
        return self._boundary.can_mutate(subject.subject_id, capability)


def _operation_to_capability(operation: str) -> str:
    """Petakan operation -> capability entrustment.

    HANYA mengenali scope read-only W1 (observe/investigate/diagnose/recommend).
    Apapun di luar set itu (protect/mutate/process.run/email.send/db.write)
    -> dikembalikan sbg "mutation" yg TIDAK ada di _CAP_READONLY -> auth
    menolaknya (fail-closed). Ini menjamin capability scope W1 PERSIS
    read-only set (accept I).
    """
    op = (operation or "").strip()
    for cap, prefix in (("observe", "environment.observe"),
                        ("investigate", "environment.investigate"),
                        ("diagnose", "environment.diagnose"),
                        ("recommend", "environment.recommend")):
        if op.startswith(prefix):
            return cap
    # non read-only environment operation + non-environment -> mutation diblokir.
    return "mutation"
