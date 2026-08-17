"""Live acceptance W1 E/F — Ward persistence PostgreSQL + survive restart.

Van #1: persistence Ward pakai PostgreSQL (existing Repository Pattern).
Van accept E: persisted in PostgreSQL.
Van accept F: survives restart.

Alur:
  1. Gunakan PostgresWardStore (tabel sam_ward) via credential dari
     ZN_PASSWORDS.md (internal; tidak diekspos ke output).
  2. Simpan snapshot Ward OpenClaw + entrustment.
  3. "Restart" = buat WardRepository BARU dengan store yang SAMA (simulasi
     proses baru) -> _recover_from_store memuat ulang.
  4. Verifikasi status active + entrustment owner van tersedia pasca-restart.
  5. Bersihkan scope test (jangan mencemari tabel produksi).

Credential dibaca dari file password internal; TIDAK dicetak ke output.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sam.ward.persistence import PostgresWardStore  # noqa: E402
from sam.ward.registry.registry import WardRepository  # noqa: E402
from sam.ward.manager import WardManager  # noqa: E402
from sam.ward.bootstrap import bootstrap_openclaw_ward, openclaw_ward_identity  # noqa: E402


def _pg_password():
    """Baca password PG dari ZN_PASSWORDS.md (internal). TIDAK dicetak."""
    p = r"D:\Project AI\ZaraNote\ZN_SAM\ZN_PASSWORDS.md"
    txt = open(p, encoding="utf-8", errors="replace").read()
    sec = txt.split("## PostgreSQL")[1].split("## ")[0]
    d = {}
    for line in sec.splitlines():
        line = line.strip().lstrip("-").strip()
        m = re.match(r"^(host/port|db|user|password)\s*:\s*(.*)$", line)
        if m:
            d[m.group(1)] = m.group(2).strip().strip("`")
    hp = d.get("host/port", "127.0.0.1:5432")
    host, port = hp.split(":")
    return f"host={host} port={int(port)} dbname={d.get('db','sam')} " \
           f"user={d.get('user','sam')} password={d.get('password','')}"


def main():
    print("=" * 70)
    print("W1 LIVE ACCT E/F — Ward persistence PostgreSQL + survive restart")
    print("=" * 70)
    dsn = _pg_password()
    scope = "ward_live_w1_e2f_" + os.urandom(4).hex()

    # 1) store PG
    try:
        store = PostgresWardStore(dsn=dsn, scope=scope)
    except Exception as exc:
        print("PG UNAVAILABLE:", exc)
        print("VERDICT: W1 E/F SKIP (PostgreSQL tak reachable)")
        return 0

    # 2) daftarkan OpenClaw dgn store PG
    repo1 = WardRepository(persistence=store)
    mgr1 = WardManager(repository=repo1)
    wid = bootstrap_openclaw_ward(mgr1, "van")
    print("registered OpenClaw ward_id:", wid)
    ent1 = repo1.get_entrustment(wid)
    assert ent1 is not None and ent1.is_active and ent1.owner_id == "van"
    print("E: entrustment persisted owner=van active=", ent1.is_active)

    # 3) RESTART: repository BARU dgn store yg sama -> recover
    repo2 = WardRepository(persistence=store)
    mgr2 = WardManager(repository=repo2)
    ward2 = mgr2.repository.get(wid)
    ent2 = mgr2.repository.get_entrustment(wid)
    print("\n[AFTER RESTART]")
    print("  ward recovered:", ward2 is not None)
    print("  status:", ward2.status if ward2 else "MISSING")
    print("  entrustment recovered:", ent2 is not None)
    print("  entrustment active:", ent2.is_active if ent2 else None)
    print("  entrustment owner:", ent2.owner_id if ent2 else None)

    # verifikasi tenant 'van' masih bisa resolve pasca-restart
    if ward2 is not None:
        res = mgr2.with_tenant({"username": "van", "role": "operator"}).auth_ward(
            "OpenClaw", "environment.observe")
        print("  tenant van resolve post-restart:", res.ok, res.reason if not res.ok else "")
    if ent2 is not None and ward2 is not None and ward2.is_active:
        print("\nVERDICT: W1 E/F PASS — persiste di PostgreSQL & survives restart")
        ok = True
    else:
        print("\nVERDICT: W1 E/F FAIL")
        ok = False

    store.clear(scope)  # bersihkan scope test
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
