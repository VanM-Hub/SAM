"""Ward Routes - W2.5 Ward Administration (canonical Ward boundary).

Adapter REST murni ke canonical Ward boundary (W2.5, amanat Van 2026-08-17).

DESAIN (bukan shortcut):
  - Reuse TOTAL canonical backend: WardManager.register_ward /
    WardRepository.register / Entrustment / WardIdentity.new /
    PostgresWardStore via wiring.build_ward_manager / get_ward_manager.
    TIDAK ada model kedua, registry kedua, persistence kedua.
  - Owner/tenant HANYA dari authenticated session (sessions.authenticate),
    TIDAK PERNAH dari input UI / body (acceptance #4). Regsitrasi memakai
    manager.with_tenant({'username','role'}) sehingga entropy ownership
    benar dan cross-tenant fail-closed (auth_ward).
  - TIDAK hardcode OpenClaw: ward_type/name/resource/purpose datang dari UI,
    ward_id deterministik dari WardIdentity.new(ward_type, name, namespace).
  - Entrustment EKSPLISIT dibangun di route (owner + allowed_capabilities
    read-only W1: observe/investigate/diagnose/recommend). Ward hanya ACTIVE
    bila admission/governance terpenuhi (registry.register menolak tanpa
    entrustment utk auth; route menolak bila field tak valid).
  - Credential TIDAK pernah masuk route/UI/log/evidence (tidak ada field
    credential dalam request; Entrustment tidak membawa secret).
  - Jalur eksekusi W2 TIDAK diubah (register_ward bukan eksekusi; tetap
    runner->adapter utk environment.observe setelah resolve).

Endpoint:
  POST /wards     -> register Ward baru (canonical) -> {ward_id, ward}
  GET  /wards     -> daftar Ward (read-only, non-secret)
  GET  /wards/{id}-> detail satu Ward (404 bila tidak ada)
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

from fastapi import APIRouter, Cookie, Header, HTTPException
from pydantic import BaseModel, Field

from sam.ward.entrustment.models import ApprovalPolicy, Entrustment
from sam.ward.identity.models import WardAccessScope, WardIdentity, WardOwner, WardMetadata

# Capability scope W1 read-only (sama dgn bootstrap OpenClaw).
_W1_READONLY_CAPS = ("observe", "investigate", "diagnose", "recommend")


class AddWardRequest(BaseModel):
    """Field registrasi Ward (NON-credential; owner DIABA IGNORE dari body).

    owner TIDAK diterima di sini (selalu dari session) - memenuhi #4.
    """

    ward_type: str = Field(..., min_length=1, description="jenis Ward (application/repository/container/...)")
    name: str = Field(..., min_length=1, description="nama readable")
    namespace: str = Field("", description="ruang nama opsional")
    resource: str = Field("", description="resource target eksternal (access_scope.resource)")
    purpose: str = Field("", description="alasan/penggunaan (metadata.description / scope)")
    scope: str = Field("", description="deskripsi cakupan akses opsional")
    execution: str = Field("", description="mode execution deskriptif (info; eksekusi tetap via canonical runner)")


class WardsRoutes:
    """Factory adapter - memegang canonical Ward boundary + identity session."""

    def __init__(self) -> None:
        # REUSE session/user store yang SAMA dengan UxRoutes (M11-004) agar
        # token dari POST /ux/login dikenali di sini. Dua SessionStore terpisah
        # akan membuat token login tidak valid di route Ward (bug cross-route).
        from sam.api.routes import ux as _ux
        self.users = _ux._routes.users
        self.sessions = _ux._routes.sessions

    # -- identity boundary (M11-004 / M12-011), pola sama dgn UxRoutes ----

    @property
    def production(self) -> bool:
        return os.environ.get("SAM_ENV") == "production"

    @property
    def auth_enabled(self) -> bool:
        # AUTH aktif bila SAM_ENABLE_AUTH=1 ATAU produksi (login wajib).
        return os.environ.get("SAM_ENABLE_AUTH") == "1" or self.production

    @staticmethod
    def _extract_token(
        authorization: Optional[str], cookie: Optional[str] = None
    ) -> Optional[str]:
        if authorization and authorization.lower().startswith("bearer "):
            return authorization[7:].strip()
        return (cookie or "").strip() or None

    def _require_identity(
        self,
        authorization: Optional[str],
        cookie: Optional[str] = None,
        csrf_header: Optional[str] = None,
        require_csrf: bool = False,
    ) -> Dict[str, str]:
        """Wajibkan identitas terverifikasi; owner/tenant HANYA dari sini.

        - auth off (dev): tenant default {"username":"user","role":"operator"}
          (kompatibel regresi; TIDAK menerima input bebas utk owner).
        - auth on: token dari header/cookie; role wajib operator;
          forged/expired -> 401; cross-user -> deny.
        - CSRF (double-submit) HANYA wajib utk MUTASI (POST/PUT/DELETE,
          require_csrf=True). GET read-only TIDAK butuh CSRF - hanya autentikasi
          token (sebelumnya GET /wards/ ikut kena 403 CSRF -> list kosong).
        Mengembalikan dict {'username','role'} yang menjadi owner_id entrustment.
        """
        if not self.auth_enabled:
            return {"username": "user", "role": "operator"}
        token = self._extract_token(authorization, cookie)
        identity = self.sessions.authenticate(token)
        if not identity:
            raise HTTPException(status_code=401, detail="autentikasi diperlukan (login dulu)")
        if require_csrf and authorization is None and cookie:
            if not self.sessions.verify_csrf(token, csrf_header):
                raise HTTPException(status_code=403, detail="CSRF token tidak valid")
        if not self.users.can_operate(identity.get("role", "")):
            raise HTTPException(
                status_code=403, detail="role tidak berwenang mengelola Ward")
        return {"username": identity.get("username", ""), "role": identity.get("role", "")}

    # -- canonical Ward access (composition root, with_tenant per-request) --

    def _manager_with_tenant(self, identity: Dict[str, str]):
        from sam.ward.wiring import get_ward_manager
        mgr = get_ward_manager()
        return mgr.with_tenant(identity) if identity else mgr

    # -- operasi -----------------------------------------------------------

    def register_ward(self, req: AddWardRequest, identity: Dict[str, str]) -> Dict[str, object]:
        """Registrasi Ward lewat canonical WardManager.register_ward (bukan shortcut).

        owner_id = identity['username'] (session), TIDAK dari body.
        ward_id deterministik dari WardIdentity.new(ward_type, name, namespace).
        Entrustment eksplisit (read-only W1). ACTIVE bila admission terpenuhi.
        """
        mgr = self._manager_with_tenant(identity)

        ward_type = (req.ward_type or "").strip()
        name = (req.name or "").strip()
        if not ward_type or not name:
            raise HTTPException(status_code=422, detail="ward_type dan name wajib")

        # Identity immutable + deterministik (seed = type|name|namespace)
        ward_identity = WardIdentity.new(
            ward_type, name, namespace=(req.namespace or "").strip())
        owner_username = identity.get("username") or "user"
        owner_role = identity.get("role") or "operator"

        access_scope = WardAccessScope(
            scope=(req.scope or "").strip() or (req.purpose or "").strip(),
            resource=(req.resource or "").strip(),
            endpoints=("read",),
        )
        metadata = WardMetadata(
            description=(req.purpose or req.scope or "").strip(),
            data=(("execution", req.execution or ""), ("origin", "ward:api:w25")),
        )
        entrustment = Entrustment(
            ward_id=ward_identity.ward_id,
            owner_id=owner_username,
            allowed_capabilities=_W1_READONLY_CAPS,
            access_scope=access_scope.scope,
            approval_policy=ApprovalPolicy(
                required=True, approver_role="operator", timeout_seconds=3600),
        )

        try:
            ward_id = mgr.register_ward(
                ward_identity,
                owner=WardOwner(owner_id=owner_username, owner_name=owner_username,
                                owner_role=owner_role),
                access_scope=access_scope,
                metadata=metadata,
                entrustment=entrustment,
                origin="ward:api:w25",
            )
        except Exception as exc:  # noqa: BLE001 - konflik / registry error
            raise HTTPException(status_code=409, detail=f"registrasi Ward gagal: {exc}")

        ward = mgr.repository.get(ward_id)
        ent = mgr.repository.get_entrustment(ward_id) if ward is not None else None
        return {
            "ward_id": ward_id,
            "accepted": True,
            "ward": ward.as_dict() if ward is not None else None,
            "resource": (ward.access_scope.resource if ward is not None else (req.resource or "").strip()),
            "purpose": (ward.metadata.description if ward is not None else (req.purpose or "").strip()),
            "owner": owner_username,
            "active": bool(ward is not None and not ward.is_revoked and
                           ent is not None and ent.is_active),
        }

    def list_wards(self, identity: Dict[str, str]) -> List[Dict[str, object]]:
        """Daftar Ward (read-only, non-secret). Hanya milik tenant ini (filter)."""
        mgr = self._manager_with_tenant(identity)
        username = identity.get("username")
        out: List[Dict[str, object]] = []
        for w in mgr.repository.list():
            ent = mgr.repository.get_entrustment(w.ward_id)
            ent_owner = (ent.owner_id or "") if ent else ""
            # defense-in-depth: hanya tampilkan Ward yang di-entrust ke tenant ini
            if username and ent_owner.split(":")[-1] != username:
                continue
            out.append({
                "ward_id": w.ward_id,
                "ward_type": w.ward_type,
                "name": w.name,
                "namespace": w.identity.namespace,
                "resource": w.access_scope.resource,
                "scope": w.access_scope.scope,
                "status": w.status,
                "active": bool(ent is not None and ent.is_active),
                "owner": ent_owner,
            })
        return out

    def get_ward(self, ward_id: str, identity: Dict[str, str]) -> Optional[Dict[str, object]]:
        """Detail satu Ward milik tenant ini; cross-tenant -> None (fail-closed)."""
        mgr = self._manager_with_tenant(identity)
        entry = mgr.repository.get_entry(ward_id)
        if entry is None:
            return None
        ent = mgr.repository.get_entrustment(ward_id)
        ent_owner = (ent.owner_id or "") if ent else ""
        username = identity.get("username")
        if username and ent_owner.split(":")[-1] != username:
            return None  # cross-tenant: tidak terlihat (fail-closed)
        w = entry.ward
        return {
            "ward_id": entry.ward_id,
            "ward_type": w.ward_type,
            "name": w.name,
            "namespace": w.identity.namespace,
            "resource": w.access_scope.resource,
            "scope": w.access_scope.scope,
            "purpose": w.metadata.description,
            "status": w.status,
            "active": bool(ent is not None and ent.is_active),
            "owner": ent_owner,
            "origin": entry.origin,
        }


_routes = WardsRoutes()
router = APIRouter(tags=["wards"])


@router.post("/")
async def wards_register(
    request: AddWardRequest,
    authorization: Optional[str] = Header(None),
    sam_session: Optional[str] = Cookie(None),
    x_csrf_token: Optional[str] = Header(None),
):
    """Daftarkan Ward baru lewat canonical boundary (W2.5). Owner dari session."""
    identity = _routes._require_identity(authorization, sam_session, x_csrf_token, require_csrf=True)
    return _routes.register_ward(request, identity)


@router.get("/")
async def wards_list(
    authorization: Optional[str] = Header(None),
    sam_session: Optional[str] = Cookie(None),
):
    """Daftar Ward milik tenant saat ini (read-only, non-secret)."""
    identity = _routes._require_identity(authorization, sam_session)
    return {"wards": _routes.list_wards(identity)}


@router.get("/{ward_id}")
async def wards_detail(
    ward_id: str,
    authorization: Optional[str] = Header(None),
    sam_session: Optional[str] = Cookie(None),
):
    """Detail satu Ward milik tenant; 404 bila bukan miliknya / tidak ada."""
    identity = _routes._require_identity(authorization, sam_session)
    ward = _routes.get_ward(ward_id, identity)
    if ward is None:
        raise HTTPException(status_code=404, detail="ward tidak ditemukan")
    return ward
