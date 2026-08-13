#!/usr/bin/env python
"""sam_backup.py — M12-013 Backup untuk SAM (proses terpisah).

Mengamankan operational truth SAM ke archive terenkripsi + integrity check.

Cakupan (Kontrak M12-013: Mission/Execution/Approval/Audit/Evidence/
Idempotency/Identity-config):
  - PostgreSQL (container sam-postgres): mission_store, sam_mission,
    sam_execution, sam_approval, sam_audit, sam_evidence, sam_idempotency,
    secret_store — via `docker exec sam-postgres pg_dump`.
  - Identity config: `~/.sam/users.json` (user & role).
  - Master key PEMISAH: `~/.sam/master.key` TIDAK digabung ke archive yang
    sama (jika digabung, enkripsi archive pelindungnya harus beda). Dibackup
    terpisah sebagai file (disalin apa adanya, di luar archive), sehingga
    enkripsi archive tetap jadi pelindung secret. Lihat --include-master-key.

Sifat (Kontrak M12-013):
  - Frequency : dipicu Task Scheduler (proses ini TIDAK punya loop; panggilan
    berulang oleh scheduler). `--every-days` hanya utk tagging metadata.
  - Retention : simpan N backup terbaru (default 7), buang lebih lama.
  - Encryption: archive dienkripsi Fernet (kunci dari env SAM_BACKUP_KEY atau
    file --key-file). Kunci TIDAK ditulis ke archive/lokasi backup.
  - Location  : default di luar project (`SAM_Backups/`), overridable --out.
  - Integrity : setelah menulis, verifikasi archive (zip + Fernet decrypt +
    PG dump tidak kosong). Exit 0 OK / 1 GAGAL / 2 KONFIGURASI.

Usage:
  python sam_backup.py [--out DIR] [--containers...] [--key-file PATH]
                       [--retain N] [--include-master-key] [--once]
Env: SAM_BACKUP_KEY (32-byte urlsafe b64 Fernet key) atau --key-file.
"""
from __future__ import annotations

import argparse
import base64
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # pragma: no cover
    Fernet = None
    InvalidToken = None

DEFAULT_CONTAINER = "sam-postgres"
DEFAULT_DB = "sam"
DEFAULT_OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "..",
    "..", "_ZaraTools", "SAM_Backups",
)


def _resolve_out(out: str | None) -> str:
    if out:
        return out
    p = os.path.abspath(DEFAULT_OUT)
    # jangan biarkan path relatif nyasar ke cwd saat dijalankan Task Scheduler
    return p


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _fernet_key(key_file: str | None, key_env: str | None):
    if Fernet is None:  # pragma: no cover
        raise RuntimeError("cryptography tidak tersedia (butuh utk enkripsi archive)")
    raw = key_env
    if not raw and key_file:
        with open(key_file, "r", encoding="utf-8") as fh:
            raw = fh.read().strip()
    if not raw:
        raise RuntimeError(
            "kunci enkripsi diperlukan: set env SAM_BACKUP_KEY atau --key-file"
        )
    # izinkan format "base64url" polos atau "Fernet:... "
    raw = raw.strip()
    if raw.startswith("Fernet:"):
        raw = raw[len("Fernet:"):]
    try:
        key = base64.urlsafe_b64decode(raw + "=" * ((4 - len(raw) % 4) % 4))
        return Fernet(base64.urlsafe_b64encode(key).decode())
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"kunci enkripsi tidak valid: {exc}")


def _run(cmd, env=None, cwd=None):
    # binary stdout/stderr (pg_dump -Fc = custom format binary)
    return subprocess.run(
        cmd, capture_output=True, env=env, cwd=cwd
    )


def _dec_err(b):
    return (b or b"").decode("utf-8", "replace").strip()[:300]


def _pg_dump(container: str, db: str) -> bytes:
    # dump SEMUA tabel (truth) ke format custom (binary), keluaran stdout.
    cmd = ["docker", "exec", container, "pg_dump", "-U", "sam", "-d", db, "-Fc"]
    proc = _run(cmd)
    if proc.returncode != 0:
        raise RuntimeError(
            f"pg_dump gagal (exit {proc.returncode}): {_dec_err(proc.stderr)}"
        )
    out = proc.stdout
    if not out or len(out) < 64:
        raise RuntimeError("pg_dump keluaran terlalu kecil (mungkin kosong)")
    if b"pg_dump: error" in out or b"segmentation" in out:
        raise RuntimeError("pg_dump mengembalikan error di output")
    return out


def _write_encrypted_archive(out_path: str, files: dict, key) -> None:
    """files: {arcname: bytes/GambarPath}. Tulis zip -> enkripsi -> out_path + .integrity."""
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
        zip_path = tf.name
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, payload in files.items():
                if isinstance(payload, bytes):
                    zf.writestr(name, payload)
                else:
                    zf.write(payload, arcname=name)
        data = Path(zip_path).read_bytes()
        enc = key.encrypt(data)
        Path(out_path).write_bytes(enc)
        Path(out_path + ".sha256").write_text(
            hashlib.sha256(enc).hexdigest() + "\n", encoding="utf-8"
        )
    finally:
        try:
            os.remove(zip_path)
        except OSError:
            pass


def _verify(out_path: str, key) -> bool:
    """Integrity: sha256 cocok, Fernet decrypt OK, zip valid, nama file benar."""
    if not os.path.exists(out_path):
        return False
    # 1. file utama ada & non-kosong
    enc = Path(out_path).read_bytes()
    if len(enc) < 64:
        return False
    # 2. sha256 integrity cocok
    sha_file = out_path + ".sha256"
    if os.path.exists(sha_file):
        expect = Path(sha_file).read_text(encoding="utf-8").strip().split()[0]
        if hashlib.sha256(enc).hexdigest() != expect:
            return False
    # 3. Fernet decrypt & zip valid
    try:
        data = key.decrypt(enc)
    except InvalidToken:
        return False
    with zipfile.ZipFile(__import__("io").BytesIO(data)) as zf:
        names = zf.namelist()
        if not names:
            return False
        # 4. setidaknya ada dump PG (mission truth)
        if not any("mission" in n or n.endswith(".dump") or n.endswith(".sql")
                   for n in names):
            return False
    return True


def _cleanup_retention(out_dir: str, retain: int, prefix: str = "sam-backup-") -> None:
    """Buang backup lama selain N terbaru (bounded retention)."""
    backups = sorted(glob.glob(os.path.join(out_dir, prefix + "*")))
    full = list(filter(lambda p: p.endswith(".zip") is False and not p.endswith(".sha256"),
                       backups))
    # pilih file arsip utama (bukan .sha256)
    main = [p for p in backups if p.endswith(".zip") is False and not p.endswith(".sha256")]
    # nama arsip = out_path (mis. sam-backup-20260813-141500.bin). sort & buang lama.
    main.sort()
    for old in main[:-retain] if retain > 0 else []:
        try:
            os.remove(old)
            if os.path.exists(old + ".sha256"):
                os.remove(old + ".sha256")
        except OSError:
            pass


def run_backup(args) -> int:
    out_dir = _resolve_out(args.out)
    _ensure_dir(out_dir)
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(out_dir, f"sam-backup-{ts}.bin")
    key = _fernet_key(args.key_file, os.environ.get("SAM_BACKUP_KEY"))
    try:
        dump = _pg_dump(args.container, args.db)
        files = {
            f"{args.db}-pg.dump": dump,
        }
        # identity config (di luar project)
        users = os.path.join(os.path.expanduser("~"), ".sam", "users.json")
        if os.path.exists(users):
            files["identity/users.json"] = users
        if args.include_master_key:
            mk = os.path.join(os.path.expanduser("~"), ".sam", "master.key")
            if os.path.exists(mk):
                # master key dipakai sebagai file terpisah (bukan di arsip sama)
                # -> salin apa adanya ke out_dir (dilindungi ACL di luar archive)
                shutil.copy2(mk, os.path.join(out_dir, f"sam-masterkey-{ts}.key"))
        _write_encrypted_archive(out_path, files, key)
        if not _verify(out_path, key):
            print(f"[code=1] INTEGRITY FAILED: {out_path}", flush=True)
            return 1
        _cleanup_retention(out_dir, args.retain)
        # output ringkas (tanpa isi/secret)
        meta = {
            "archive": os.path.basename(out_path),
            "encrypted": True,
            "blobs": sorted(files.keys()),
            "retain": args.retain,
            "integrity": "OK",
        }
        print(f"[code=0] BACKUP OK {json.dumps(meta)}", flush=True)
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"[code=1] BACKUP FAILED: {exc}", flush=True)
        return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SAM M12-013 Backup")
    ap.add_argument("--out", default=None, help="dir output (default di luar project)")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--key-file", default=None, help="file berisi Fernet key")
    ap.add_argument("--retain", type=int, default=7)
    ap.add_argument("--include-master-key", action="store_true")
    ap.add_argument("--once", action="store_true", help="mode sekali (default)")
    args = ap.parse_args(argv)
    return run_backup(args)


if __name__ == "__main__":
    sys.exit(main())
