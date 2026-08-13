"""test_m12_013_backup.py — M12-013 Backup.

Kontrak M12-013: Backup Mission/Execution/Approval/Audit/Evidence/Idempotency/
Identity-config. Frequency+retention+encryption+location+integrity check.

Cakupan (unit, tanpa Docker nyata — _pg_dump dimock deterministik):
  - Backup sukses: archive terenkripsi + .sha256 dibuat; exit 0; blobs
    (pg dump + identity users.json) tercatat.
  - Enkripsi: archive TIDAK berupa zip plaintext; kunci salah -> integrity gagal.
  - Integrity: corrupt archive -> _verify False; sha256 tidak cocok -> False.
  - Wajib kunci: tanpa key -> error konfigurasi (bukan backup diam-diam).
  - pg_dump gagal -> backup GAGAL (exit 1), tidak menghasilkan archive sukses.
  - Retention: retain=N -> hanya N backup terbaru tersisa.
"""
from __future__ import annotations

import base64
import os
import zipfile
from pathlib import Path

import pytest

# tools/ bukan package `sam.tools` -> import via importlib.util
import importlib.util

def _load_backup():
    path = Path(__file__).resolve().parents[2] / "tools" / "sam_backup.py"
    spec = importlib.util.spec_from_file_location("sam_backup_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def m():
    return _load_backup()


def _key_str():
    # Fernet key 32-byte validd
    raw = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")
    while len(raw) % 4:
        raw += "="
    return raw


def test_backup_success_encrypted_and_verified(m, tmp_path, monkeypatch):
    monkeypatch.setattr(m, "_pg_dump", lambda *a, **k: b"\x00\x01PGDMP fake dump content \x02\x03" * 50)
    out = str(tmp_path / "bk")
    key = _key_str()
    kf = tmp_path / "k.txt"
    kf.write_text(key, encoding="utf-8")
    rc = m.main(["--out", out, "--key-file", str(kf), "--once"])
    assert rc == 0
    files = os.listdir(out)
    bin_files = [f for f in files if f.endswith(".bin")]
    sha_files = [f for f in files if f.endswith(".sha256")]
    assert len(bin_files) == 1
    assert len(sha_files) == 1
    # archive TERENKRIPSI: bukan zip plaintext biasa
    enc = Path(out) / bin_files[0]
    data = enc.read_bytes()
    assert b"PK\x03\x04" not in data[:4]  # bukan raw zip (harus ciphertext)
    # integritas terverifikasi
    fkey = m._fernet_key(str(kf), None)
    assert m._verify(str(enc), fkey) is True


def test_backup_wrong_key_integrity_fails(m, tmp_path, monkeypatch):
    monkeypatch.setattr(m, "_pg_dump", lambda *a, **k: b"PGDATA" * 100)
    out = str(tmp_path / "bk2")
    k1 = _key_str()
    k2 = _key_str()
    kf1 = tmp_path / "k1.txt"; kf1.write_text(k1, encoding="utf-8")
    kf2 = tmp_path / "k2.txt"; kf2.write_text(k2, encoding="utf-8")
    assert m.main(["--out", out, "--key-file", str(kf1), "--once"]) == 0
    enc = [f for f in os.listdir(out) if f.endswith(".bin")][0]
    path = str(Path(out) / enc)
    fkey2 = m._fernet_key(str(kf2), None)
    assert m._verify(path, fkey2) is False  # kunci salah -> gagal verifikasi


def test_backup_requires_key(m, tmp_path, monkeypatch):
    monkeypatch.setattr(m, "_pg_dump", lambda *a, **k: b"x" * 100)
    out = str(tmp_path / "bk3")
    monkeypatch.delenv("SAM_BACKUP_KEY", raising=False)
    with pytest.raises(RuntimeError) as exc:
        m.main(["--out", out, "--once"])  # tanpa key
    assert "kunci" in str(exc.value)


def test_backup_pg_dump_fail_exit1(m, tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("pg_dump gagal (PG down)")
    monkeypatch.setattr(m, "_pg_dump", boom)
    out = str(tmp_path / "bk4")
    kf = tmp_path / "k.txt"; kf.write_text(_key_str(), encoding="utf-8")
    rc = m.main(["--out", out, "--key-file", str(kf), "--once"])
    assert rc == 1  # GAGAL, bukan sukses palsu


def test_backup_corrupt_archive_integrity(m, tmp_path, monkeypatch):
    monkeypatch.setattr(m, "_pg_dump", lambda *a, **k: b"PGDATA" * 50)
    out = str(tmp_path / "bk5")
    kf = tmp_path / "k.txt"; kf.write_text(_key_str(), encoding="utf-8")
    m.main(["--out", out, "--key-file", str(kf), "--once"])
    enc = Path(out) / [f for f in os.listdir(out) if f.endswith(".bin")][0]
    enc.write_bytes(b"\x00" * 2000)  # corrupt
    fkey = m._fernet_key(str(kf), None)
    assert m._verify(str(enc), fkey) is False


def test_backup_retention_bounded(m, tmp_path, monkeypatch):
    monkeypatch.setattr(m, "_pg_dump", lambda *a, **k: b"PGDATA" * 50)
    kf = tmp_path / "k.txt"; kf.write_text(_key_str(), encoding="utf-8")
    out = str(tmp_path / "bk6")
    state = {"i": 0}
    real_strftime = m.time.strftime

    def fake_strftime(fmt, *a, **k):
        if fmt == "%Y%m%d-%H%M%S":
            state["i"] += 1
            return f"20260813-{100000 + state['i']:06d}"  # unik per panggilan
        return real_strftime(fmt, *a, **k)

    monkeypatch.setattr(m.time, "strftime", fake_strftime)
    # buat 3 backup dgn retain 2 -> setelah ketiga, sisa 2
    m.main(["--out", out, "--key-file", str(kf), "--retain", "2", "--once"])
    m.main(["--out", out, "--key-file", str(kf), "--retain", "2", "--once"])
    m.main(["--out", out, "--key-file", str(kf), "--retain", "2", "--once"])
    bins = [f for f in os.listdir(out) if f.endswith(".bin")]
    assert len(bins) == 2  # bounded retention



def test_backup_includes_identity_when_present(m, tmp_path, monkeypatch):
    monkeypatch.setattr(m, "_pg_dump", lambda *a, **k: b"PGDATA" * 40)
    # tiru users.json di ~/.sam (tanpa menyentuh file asli)
    fake_home = tmp_path / "fakehome" / ".sam"
    fake_home.mkdir(parents=True)
    (fake_home / "users.json").write_text('{"users":[]}', encoding="utf-8")
    monkeypatch.setattr(os.path, "expanduser", lambda p: p.replace("~", str(tmp_path / "fakehome")))
    out = str(tmp_path / "bk7")
    kf = tmp_path / "k.txt"; kf.write_text(_key_str(), encoding="utf-8")
    rc = m.main(["--out", out, "--key-file", str(kf), "--once"])
    assert rc == 0
    # validasi isi archive via decrypt
    enc = Path(out) / [f for f in os.listdir(out) if f.endswith(".bin")][0]
    fkey = m._fernet_key(str(kf), None)
    data = fkey.decrypt(enc.read_bytes())
    with zipfile.ZipFile(__import__("io").BytesIO(data)) as zf:
        names = zf.namelist()
    assert any("identity/users.json" == n for n in names)
