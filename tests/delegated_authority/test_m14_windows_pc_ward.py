"""M14-010 tests — Real Windows PC Ward (observe + diagnose Word/PDF).

Membuat file .docx/.pdf di tmp dir (signature valid & rusak) utk membuktikan
observe/diagnose + authority gate. Recovery action di-stub (execute_fn/verify_fn
diinjeksi). E2E real (PC produksi) terpisah & jujur.
"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.real_windows_pc_ward import WindowsPCWard


def _grant_auto():
    return DelegationGrant(
        ward_id="pc", owner_id="owner", autonomy_level=AutonomyLevel.AUTONOMOUS,
        allowed_mutations=("protect",), requires_human_approval=False,
    )


def _make_dir_with_files(corrupt=True):
    d = tempfile.mkdtemp(prefix="pc_ward_")
    # docx valid (PK magic)
    with open(os.path.join(d, "laporan.docx"), "wb") as f:
        f.write(b"PK\x03\x04" + b"\x00" * 20)
    # pdf valid
    with open(os.path.join(d, "dokumen.pdf"), "wb") as f:
        f.write(b"%PDF-1.7\n" + b"\x00" * 20)
    if corrupt:
        # docx rusak (tanpa PK)
        with open(os.path.join(d, "rusak.docx"), "wb") as f:
            f.write(b"\x00\x01\x02\x03" + b"\x00" * 20)
    return d


class TestWindowsPCWardObserve:
    def test_observe_healthy_folder(self):
        d = tempfile.mkdtemp(prefix="pc_ok_")
        ward = WindowsPCWard(d)
        diag = ward.observe()
        assert diag.healthy is True

    def test_observe_detects_corrupt_docx(self):
        d = _make_dir_with_files(corrupt=True)
        ward = WindowsPCWard(d)
        diag = ward.observe()
        # ada file rusak -> issue
        assert diag.issues
        names = [f.name for f in diag.files]
        assert "rusak.docx" in names
        rusak = next(f for f in diag.files if f.name == "rusak.docx")
        assert rusak.valid_signature is False


class TestWindowsPCWardRecover:
    async def test_healthy_no_recovery(self):
        d = tempfile.mkdtemp(prefix="pc_ok_")
        ward = WindowsPCWard(d)
        res = await ward.recover(grant=_grant_auto())
        assert res.repaired is False
        assert "no issue" in res.reason

    async def test_corrupt_recover_when_authorized(self):
        d = _make_dir_with_files(corrupt=True)
        ward = WindowsPCWard(d)
        res = await ward.recover(
            grant=_grant_auto(),
            execute_fn=lambda req: {"ok": True, "repaired": "rusak.docx"},
            verify_fn=lambda req: {"ok": True, "verified": "file ok"},
        )
        assert res.repaired is True
        assert res.outcome.ok is True

    async def test_corrupt_human_required_escalates(self):
        d = _make_dir_with_files(corrupt=True)
        ward = WindowsPCWard(d)
        g = DelegationGrant(
            ward_id="pc", owner_id="owner", autonomy_level=AutonomyLevel.AUTONOMOUS,
            allowed_mutations=("protect",), requires_human_approval=True,
        )
        res = await ward.recover(grant=g)
        assert res.repaired is False
        assert res.outcome.ok is False
