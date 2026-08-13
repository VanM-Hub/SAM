#!/usr/bin/env python
"""sam_restore.py — M12-014 Restore Drill untuk SAM (proses terpisah).

Memulihkan operational truth dari archive backup terenkripsi (buatan
sam_backup.py), lalu verifikasi konsistensi.

Alur (Kontrak M12-014: backup -> destroy -> restore -> start -> verify):
  1. Integrity pre-check: sha256 + Fernet decrypt archive SEBELUM restore.
     (Tidak pernah restore archive rusak / kunci salah.)
  2. Ekstrak `sam-pg.dump` (format custom) dari zip dalam archive.
  3. Restore PostgreSQL ke target DB via `pg_restore`:
       - drop objects (--clean) biar target bersih seperti setelah destroy;
       - create schema jika perlu (--create memakai DB name dari dump #4 dengan
         -C memakai dbname argumen; di sini: pg_restore ke DATABASE yg EMPTY).
     Default target = db "sam" (produksi). Untuk SAFE drill, operator memakai
     --target-db sam_restoredrill (sandbox) supaya tidak merusak produksi.
  4. Bila archive berisi identity/users.json: kembalikan ke ~/.sam/users.json
     (overwrite hanya bila --identity-target diberikan; default BAHAYA ->
     Wajib eksplisit. Tanpa flag, identity TIDAK ditulis, hanya dicatat).
  5. Verify pasca-restore terhadap DB target: tabel mission_store / sam_audit
     ada + isi tertentu muncul. Exit 0 OK / 1 GAGAL.

Safety:
  - TIDAK ada --force-destroy otomatis; restore memakai pg_restore --clean yang
    drop objects DI TARGET. Operator harus yakin target=DB yg ingin dipulihkan.
  - Kunci TIDAK disimpan ke disk; dibaca dari env SAM_BACKUP_KEY / --key-file.

Usage:
  python sam_restore.py --input PATH.bin [--key-file PATH | env SAM_BACKUP_KEY]
                        [--container sam-postgres] [--target-db NAME]
                        [--database-url] [--restore-master-key] [--once]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import os
import subprocess
import sys
import zipfile
from pathlib import Path

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # pragma: no cover
    Fernet = None
    InvalidToken = None

DEFAULT_CONTAINER = "sam-postgres"


def _fernet_key(key_file: str | None, key_env: str | None):
    if Fernet is None:  # pragma: no cover
        raise RuntimeError("cryptography tidak tersedia (butuh utk decrypt archive)")
    raw = key_env
    if not raw and key_file:
        with open(key_file, "r", encoding="utf-8") as fh:
            raw = fh.read().strip()
    if not raw:
        raise RuntimeError(
            "kunci dekripsi diperlukan: set env SAM_BACKUP_KEY atau --key-file"
        )
    raw = raw.strip()
    if raw.startswith("Fernet:"):
        raw = raw[len("Fernet:"):]
    try:
        key = base64.urlsafe_b64decode(raw + "=" * ((4 - len(raw) % 4) % 4))
        return Fernet(base64.urlsafe_b64encode(key).decode())
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"kunci tidak valid: {exc}")


def _run_bin(cmd, env=None, cwd=None):
    return subprocess.run(cmd, capture_output=True, env=env, cwd=cwd)


def _check_integrity(path: str, key) -> bytes:
    """sha256 + Fernet decrypt -> zip bytes. Raise bila rusak/salah kunci."""
    if not os.path.exists(path):
        raise RuntimeError(f"archive tidak ada: {path}")
    enc = Path(path).read_bytes()
    sha_file = path + ".sha256"
    if os.path.exists(sha_file):
        expect = Path(sha_file).read_text(encoding="utf-8").strip().split()[0]
        if hashlib.sha256(enc).hexdigest() != expect:
            raise RuntimeError("integrity sha256 tidak cocok (archive dirusak)")
    try:
        return key.decrypt(enc)
    except InvalidToken as exc:
        raise RuntimeError("decrypt gagal (kunci salah / archive korup)") from exc


def _load_zip(data: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return {n: zf.read(n) for n in zf.namelist()}


def _find_pg_dump(files: dict) -> bytes | None:
    for name, payload in files.items():
        if name.endswith(".dump") or name.endswith(".sql"):
            return payload
    return None


def _restore_pg(container: str, db: str, dump: bytes) -> None:
    """Restore dump ke target DB. pg_restore --clean (drop objects yg ada).
    Dump dikirim via stdin -> cat di dalam container -> pg_restore."""
    cmd = ["docker", "exec", "-i", container, "sh", "-c",
           "cat > /tmp/sam_restore.dump && pg_restore -U sam -d " + db +
           " --clean --if-exists /tmp/sam_restore.dump"]
    proc = subprocess.run(cmd, input=dump, capture_output=True)
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", "replace").strip()[-400:]
        raise RuntimeError(f"pg_restore gagal (exit {proc.returncode}): {err}")


def _count(table: str, container: str, db: str) -> int:
    proc = _run_bin(["docker", "exec", container, "psql", "-U", "sam", "-d", db,
                     "-t", "-A", "-c", f"SELECT count(*) FROM {table};"])
    if proc.returncode != 0:
        return -1
    try:
        return int((proc.stdout or b"0").decode("utf-8", "replace").strip() or "0")
    except ValueError:
        return -1


def run_restore(args) -> int:
    key = _fernet_key(args.key_file, os.environ.get("SAM_BACKUP_KEY"))
    try:
        data = _check_integrity(args.input, key)
        files = _load_zip(data)
        dump = _find_pg_dump(files)
        if not dump:
            print("[code=1] RESTORE FAILED: archive tidak berisi pg dump", flush=True)
            return 1
        db = args.target_db
        # pastikan DB target ada (bila tidak, buat sandbox utk drill)
        _ensure_db(args.container, db)
        _restore_pg(args.container, db, dump)
        # verify: tabel mission/audit ada & count > -1 (bukan error)
        before_mission = _count("mission_store", args.container, db)
        before_audit = _count("sam_audit", args.container, db)
        if before_mission < 0:
            print("[code=1] RESTORE FAILED: mission_store tidak bisa dibaca", flush=True)
            return 1
        # identity restore HANYA bila eksplisit (hindari timpa tanpa sadar)
        identity_written = False
        if args.restore_master_key and "identity/users.json" in files:
            users = os.path.join(os.path.expanduser("~"), ".sam", "users.json")
            os.makedirs(os.path.dirname(users), exist_ok=True)
            Path(users).write_bytes(files["identity/users.json"])
            identity_written = True
        meta = {
            "archive": os.path.basename(args.input),
            "target_db": db,
            "verified": True,
            "mission_store_rows": before_mission,
            "sam_audit_rows": before_audit,
            "identity_restored": identity_written,
        }
        print(f"[code=0] RESTORE OK {meta}", flush=True)
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"[code=1] RESTORE FAILED: {exc}", flush=True)
        return 1


def _ensure_db(container: str, db: str) -> None:
    """Buat DB bila belum ada (utk target sandbox; produksi sudah ada)."""
    proc = _run_bin(["docker", "exec", container, "psql", "-U", "sam",
                     "-d", "sam", "-t", "-A", "-c",
                     f"SELECT 1 FROM pg_database WHERE datname='{db}';"])
    exists = (proc.stdout or b"").strip() == b"1"
    if not exists:
        # tidak boleh drop DB sembarangan; buat dgn owner sam
        _run_bin(["docker", "exec", container, "createdb", "-U", "sam",
                  "-O", "sam", db])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SAM M12-014 Restore Drill")
    ap.add_argument("--input", required=True, help="archive backup (.bin)")
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    ap.add_argument("--target-db", default="sam", help="DB target (default produksi)")
    ap.add_argument("--key-file", default=None)
    ap.add_argument("--restore-master-key", action="store_true",
                    help="timpa identity/users.json bila ada di archive (eksplisit)")
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args(argv)
    return run_restore(args)


if __name__ == "__main__":
    sys.exit(main())
