"""test_m12_014_restore_drill.py — M12-014 Restore Drill.

Kontrak M12-014: Buktikan backup -> destroy -> restore -> start -> verify
(mission/audit/idempotency/identity truth konsisten).

Cakupan (unit; docker dipatch agar deterministik — drill NYATA terhadap
sandbox PG dilakukan oleh operator/CI, bukan di unit):
  - Integrity pre-check: archive rusak (sha256 tetap tapi isi korup) ->
    restore DITOLAK (tidak pernah restore archive korup).
  - Kunci salah -> decrypt gagal -> restore DITOLAK.
  - Restore sukses: pg_restore --clean dipanggil, psql count dibaca,
    exit code=0 RESTORE OK dengan truth konsisten (mission/audit terbaca).
  - Archive tanpa pg dump -> RESTORE FAILED.
  - Identity/users.json HANYA ditimpa bila --restore-master-key eksplisit
    (jangan menimpa tanpa sengaja); tanpa flag -> dicatat, tidak ditulis.
"""
from __future__ import annotations

import base64
import importlib.util
import os
import zipfile
import io
from pathlib import Path

import pytest


def _load_restore():
    path = Path(__file__).resolve().parents[2] / "tools" / "sam_restore.py"
    spec = importlib.util.spec_from_file_location("sam_restore_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def m():
    return _load_restore()


def _key_str():
    raw = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
    while len(raw) % 4:
        raw += "="
    return raw


def _make_archive(tmp_path, key, dump=b"PGDUMPCONTENT" * 50, users=None,
                  corrupt_after=False):
    """Buat archive terenkripsi berisi pg dump (+ optional users.json)."""
    kf = tmp_path / "k.txt"
    kf.write_text(key, encoding="utf-8")
    # build zip in-memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("sam-pg.dump", dump)
        if users is not None:
            zf.writestr("identity/users.json", users)
    data = buf.getvalue()
    # encrypt dgn kunci asli
    mod = _load_restore()
    fkey = mod._fernet_key(str(kf), None)
    enc = fkey.encrypt(data)
    arc = tmp_path / "backup.bin"
    arc.write_bytes(enc)
    if corrupt_after:
        # sha256 benar, tapi isi file diubah -> mismatch
        Path(tmp_path / "backup.bin.sha256").write_text(
            _make_sha(enc), encoding="utf-8")
        arc.write_bytes(b"\x00" * len(enc))  # isi diganti
    else:
        Path(tmp_path / "backup.bin.sha256").write_text(
            _make_sha(enc), encoding="utf-8")
    return str(arc), str(kf)


def _make_sha(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest() + "\n"


class _Proc:
    def __init__(self, rc=0, out=b"", err=b""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err


def test_restore_rejects_corrupt_archive(m, tmp_path, monkeypatch):
    key = _key_str()
    arc, kf = _make_archive(tmp_path, key, corrupt_after=True)
    # korup: sha256 cocok (set di _make_archive), tapi isi beda
    res = m.main(["--input", arc, "--key-file", str(kf),
                  "--target-db", "sam_victim", "--once"])
    assert res == 1  # DITOLAK / FAILED, bukan sukses palsu


def test_restore_rejects_wrong_key(m, tmp_path, monkeypatch):
    key1 = _key_str()
    key2 = _key_str()
    arc, kf1 = _make_archive(tmp_path, key1)
    kf2 = tmp_path / "k2.txt"
    kf2.write_text(key2, encoding="utf-8")
    res = m.main(["--input", arc, "--key-file", str(kf2),
                  "--target-db", "sam_victim", "--once"])
    assert res == 1  # decrypt gagal -> tolak restore


def test_restore_success_pgrestore_called(m, tmp_path, monkeypatch):
    key = _key_str()
    arc, kf = _make_archive(tmp_path, key)
    calls = []
    # patch _run_bin utk _ensure_db + _count; patch subprocess.run utk pg_restore
    monkeypatch.setattr(m, "_run_bin",
                        lambda cmd, **k: _Proc(0, b"1" if "pg_database" in " ".join(cmd) else b"1"))
    captured = {}

    def fake_run(cmd, input=None, **k):
        captured["cmd"] = cmd
        captured["input_len"] = len(input or b"")
        # pg_restore sukses
        return _Proc(0)

    monkeypatch.setattr(m.subprocess, "run", fake_run)
    res = m.run_restore(
        type("A", (), {
            "input": arc, "key_file": str(kf), "target_db": "sam_victim",
            "container": "sam-postgres", "restore_master_key": False,
            "once": True,
        })())
    assert res == 0
    joined = " ".join(captured["cmd"])
    assert "--clean" in joined  # destroy objects saat restore
    assert "pg_restore" in joined
    assert captured["input_len"] > 0  # dump dikirim ke pg_restore


def test_restore_no_pg_dump_failed(m, tmp_path, monkeypatch):
    key = _key_str()
    kf = tmp_path / "k.txt"
    kf.write_text(key, encoding="utf-8")
    # archive TANPA pg dump
    mod = _load_restore()
    fkey = mod._fernet_key(str(kf), None)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("identity/users.json", b"{}")
    enc = fkey.encrypt(buf.getvalue())
    arc = tmp_path / "nodump.bin"
    arc.write_bytes(enc)
    Path(str(arc) + ".sha256").write_text(_make_sha(enc), encoding="utf-8")
    res = m.main(["--input", str(arc), "--key-file", str(kf),
                  "--target-db", "sam_victim", "--once"])
    assert res == 1  # archive tak berisi pg dump -> FAILED (bukan sukses palsu)


def test_identity_not_overwritten_without_flag(m, tmp_path, monkeypatch):
    key = _key_str()
    users = b'{"users":[{"u":"van"}]}'
    arc, kf = _make_archive(tmp_path, key, users=users)
    # tiru ~/.sam/users.json lama
    fake_home = tmp_path / "fh"
    (fake_home / ".sam").mkdir(parents=True)
    old = fake_home / ".sam" / "users.json"
    old.write_text("OLD", encoding="utf-8")
    monkeypatch.setattr(os.path, "expanduser",
                        lambda p: p.replace("~", str(fake_home)))
    monkeypatch.setattr(m, "_run_bin",
                        lambda cmd, **k: _Proc(0, b"1" if "pg_database" in " ".join(cmd) else b"1"))
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **k: _Proc(0))
    res = m.main(["--input", arc, "--key-file", str(kf),
                  "--target-db", "sam_victim", "--once"])
    assert res == 0
    # tanpa --restore-master-key -> users.json TIDAK ditimpa
    assert old.read_text(encoding="utf-8") == "OLD"


def test_identity_overwritten_with_flag(m, tmp_path, monkeypatch):
    key = _key_str()
    new_users = b'{"users":[{"u":"van2"}]}'
    arc, kf = _make_archive(tmp_path, key, users=new_users)
    fake_home = tmp_path / "fh2"
    (fake_home / ".sam").mkdir(parents=True)
    old = fake_home / ".sam" / "users.json"
    old.write_text("OLD", encoding="utf-8")
    monkeypatch.setattr(os.path, "expanduser",
                        lambda p: p.replace("~", str(fake_home)))
    monkeypatch.setattr(m, "_run_bin",
                        lambda cmd, **k: _Proc(0, b"1" if "pg_database" in " ".join(cmd) else b"1"))
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **k: _Proc(0))
    res = m.main(["--input", arc, "--key-file", str(kf),
                  "--target-db", "sam_victim", "--once", "--restore-master-key"])
    assert res == 0
    assert old.read_bytes() == new_users  # ditimpa krn eksplisit
