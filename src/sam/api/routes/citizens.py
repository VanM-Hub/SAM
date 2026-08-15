"""Citizen Routes — read-only inventory & discovery (Citizen Ecosystem wiring).

Murni read: daftar citizen, cari by id/kind, discovery berbasis kontrak.
Registry != Authority: endpoint ini TIDAK bisa register/unregister/activate.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from sam.citizen.wiring import citizen_api

router = APIRouter()


@router.get("/")
async def citizens():
    """Inventory citizen: jumlah, kinds, dan daftar ringkas (read-only)."""
    return {
        "count": citizen_api.count,
        "kinds": list(citizen_api.kinds()),
        "citizens": [s.as_dict() for s in citizen_api.all()],
    }


@router.get("/discover")
async def citizens_discover(
    kind: str = "",
    name: str = "",
    capability: str = "",
    contract: str = "",
    identity_id: str = "",
):
    """Discovery deterministik berbasis kriteria eksplisit (no implicit)."""
    if not any((kind, name, capability, contract, identity_id)):
        raise HTTPException(
            status_code=400,
            detail="discovery requires explicit criteria (no implicit discovery)",
        )
    return citizen_api.discover(
        kind=kind, name=name, capability=capability,
        contract=contract, identity_id=identity_id,
    ).as_dict()


@router.get("/kinds/{kind}")
async def citizens_by_kind(kind: str):
    """Daftar citizen dari satu jenis (equal, tidak ada privileged)."""
    return {
        "kind": kind,
        "citizens": [s.as_dict() for s in citizen_api.by_kind(kind)],
    }


@router.get("/{identity_id}")
async def citizen_detail(identity_id: str):
    """Detail satu citizen by identity_id (404 bila tidak ada)."""
    s = citizen_api.get(identity_id)
    if s is None:
        raise HTTPException(status_code=404, detail="citizen not found")
    return s.as_dict()
