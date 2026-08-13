"""_make_user.py — Bootstrapping user SAM (M11-004).

Menulis ~/.sam/users.json (DI LUAR project, tidak pernah di-commit) berisi
satu user dengan password yang sudah di-hash (pbkdf2). Password dibaca dari
env SAM_NEW_USER / SAM_NEW_PASSWORD — TIDAK ditampilkan di CLI/arg.

Cara pakai (PowerShell, semua dalam SAME exec):
  $env:SAM_NEW_USER='van'; $env:SAM_NEW_PASSWORD='<pass>';
  python _make_user.py --role operator [--replace]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Pastikan src di import path bila dijalankan dari root repo.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from sam.application.ux.identity import _hash_password, _default_users_file  # noqa: E402


def main() -> int:
    username = (os.environ.get("SAM_NEW_USER") or "").strip()
    password = os.environ.get("SAM_NEW_PASSWORD") or ""
    role = os.environ.get("SAM_NEW_ROLE") or "operator"
    replace = "--replace" in sys.argv

    if not username or not password:
        print("ERROR: set SAM_NEW_USER dan SAM_NEW_PASSWORD dulu (dalam SAME exec).")
        return 2
    if len(password) < 6:
        print("ERROR: password minimal 6 karakter.")
        return 2

    path = _default_users_file()
    # baca file lama bila ada (tambah user tanpa menimpa user lain)
    users = []
    if path.exists() and not replace:
        try:
            with open(path, "r", encoding="utf-8") as f:
                users = list((json.load(f).get("users") or []))
        except Exception:
            users = []

    # hapus user dengan nama sama bila replace, lalu tambahkan versi baru
    users = [u for u in users if u.get("username") != username]
    users.append({
        "username": username,
        "role": role,
        "password": _hash_password(password),
    })

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, ensure_ascii=False, indent=2)
    print(f"OK: users.json ditulis ke {path} ({len(users)} user, {username} role={role})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
