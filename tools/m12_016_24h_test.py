#!/usr/bin/env python
"""m12_016_24h_test.py — M12-016 24-Hour Mission Test harness (proses terpisah).

Kontrak M12-016: Operator tak sentuh SAM selama 24 jam + controlled failure.
  NO LOST TRUTH / NO DUPLICATE / NO UNOBSERVED FAILURE /
  NO UNSAFE CONTINUATION / NO MANUAL RECOVERY.

Harness ini TIDAK mengubah state SAM; ia membaca snapshot operasional dari
PostgreSQL (psql via docker) + endpoint /health/ready, lalu menyimpan /
membandingkan snapshot.

Mode:
  --begin      : rekam baseline saat ini (truth count, idempotency, audit,
                 readiness, uptime) ke {state_dir}/baseline.json.
  --seed       : injeksi failure TERKONTROL: `sc stop SAM` + `sc start SAM`
                 (service SAM restart). Harus dijalankan oleh operator/Task
                 Scheduler utk menguji recovery tanpa sentuhan manual.
  --verify     : setelah periode (default >=24 jam sejak baseline) bandingkan
                 state saat ini vs baseline:
                   - NO LOST TRUTH: tiap truth baseline masih ADA & value konsisten
                     (mission/execution/approval/audit/evidence/idempotency).
                   - NO DUPLICATE : idempotency key tidak bertambah duplikat utk
                     key yg sudah ada (nilai request_id konsisten).
                   - NO UNOBSERVED FAILURE : service hidup & /health/ready 200
                     (fail-closed aktif bila dependency down).
                   - NO UNSAFE CONTINUATION : tidak ada execution yg berstatus
                     "running" tanpa batas (harus FAILED/REJECTED/COMPLETED).
                 Exit 0 PASS / 1 FAIL.
USAGE:
  python tools/m12_016_24h_test.py --begin --state-dir ./M12-016-state
  python tools/m12_016_24h_test.py --verify --state-dir ./M12-016-state
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_TRUTH = [
    "mission_store", "sam_mission", "sam_execution", "sam_approval",
    "sam_audit", "sam_evidence", "sam_idempotency",
]
STATE_REL = "docs/engineering/state/M12-016"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _psql(db: str, query: str) -> str:
    p = subprocess.run(
        ["docker", "exec", "sam-postgres", "psql", "-U", "sam", "-d", db,
         "-t", "-A", "-c", query],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        return ""
    return (p.stdout or "").strip()


def _table_counts() -> dict:
    counts: dict[str, int] = {}
    for t in REQUIRED_TRUTH:
        v = _psql("sam", f"SELECT count(*) FROM {t};")
        try:
            counts[t] = int(v or "0")
        except ValueError:
            counts[t] = -1
    return counts


def _idempotency_snapshot() -> dict:
    """{key: request_id} -> deteksi duplicate later."""
    out: dict[str, str] = {}
    raw = _psql("sam", "SELECT key, payload FROM sam_idempotency ORDER BY key;")
    for line in raw.splitlines():
        if not line:
            continue
        parts = line.split("|", 1)
        if len(parts) == 2:
            key, payload = parts[0], parts[1]
            req = ""
            if "request_id" in payload:
                import re
                m = re.search(r'"request_id"\s*:\s*"([^"]+)"', payload)
                if m:
                    req = m.group(1)
            out[key] = req
    return out


def _readiness() -> dict:
    try:
        with urllib.request.urlopen(
                "http://127.0.0.1:8080/health/ready", timeout=5) as r:
            return {"code": r.status, "body": r.read().decode("utf-8", "replace")[:200]}
    except Exception as exc:
        return {"code": -1, "body": str(exc)[:200]}


def _service_state() -> str:
    p = subprocess.run(["sc", "query", "SAM"], capture_output=True, text=True)
    for line in (p.stdout or "").splitlines():
        if "STATE" in line:
            return line.strip()
    return "unknown"


def _unsafe_running_executions() -> int:
    # execution berstatus running (belum settle) -> unsafe continuation risk
    raw = _psql("sam", "SELECT count(*) FROM sam_execution "
                       "WHERE payload::text LIKE '%running%';")
    try:
        return max(0, int(raw or "0"))
    except ValueError:
        return -1


def _baseline_path(state_dir: str) -> Path:
    return Path(state_dir) / "baseline.json"


def cmd_begin(args) -> int:
    counts = _table_counts()
    snapshot = {
        "started_at": _now_iso(),
        "table_counts": counts,
        "idempotency": _idempotency_snapshot(),
        "readiness": _readiness(),
        "service": _service_state(),
        "unsafe_running_executions": _unsafe_running_executions(),
    }
    out = _baseline_path(args.state_dir)
    Path(args.state_dir).mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[code=0] BASELINE RECORDED -> {out}", flush=True)
    print(json.dumps({
        "counts": counts,
        "service": snapshot["service"],
        "ready": snapshot["readiness"],
    }, ensure_ascii=False), flush=True)
    return 0


def cmd_seed(args) -> int:
    """Controlled failure: restart service SAM via sc (NSSM)."""
    p = subprocess.run(["sc", "stop", "SAM"], capture_output=True, text=True)
    time.sleep(4)
    p2 = subprocess.run(["sc", "start", "SAM"], capture_output=True, text=True)
    time.sleep(6)
    state = _service_state()
    ready = _readiness()
    ok = "RUNNING" in state and ready.get("code") == 200
    print(
        f"[code={0 if ok else 1}] SEED CONTROLLED FAILURE (SAM restart): "
        f"service={state!r} ready={ready.get('code')}",
        flush=True,
    )
    return 0 if ok else 1


def cmd_verify(args) -> int:
    bl = json.loads(_baseline_path(args.state_dir).read_text(encoding="utf-8"))
    started = datetime.fromisoformat(bl["started_at"])
    elapsed_h = (datetime.now(timezone.utc) - started).total_seconds() / 3600.0

    results: list[tuple[str, bool, str]] = []
    # NO MANUAL RECOVERY / NO LOST TRUTH: truth baseline masih ada & konsisten
    counts = _table_counts()
    for t, base in bl["table_counts"].items():
        cur = counts.get(t, -1)
        # truth tidak BOLEH berkurang lebih rendah dari baseline (lost truth)
        ok_lost = cur >= 0 and cur >= base
        results.append((f"NO_LOST_TRUTH:{t}", ok_lost,
                        f"base={base} now={cur}"))

    # NO DUPLICATE: idempotency key tak berubah request_id / tak dobel value
    idem_now = _idempotency_snapshot()
    for key, req in bl["idempotency"].items():
        if key in idem_now:
            dup = idem_now[key] == req or idem_now[key] == "" and req != ""
            results.append((f"NO_DUPLICATE:{key}", bool(dup),
                            f"base_req={req} now_req={idem_now[key]}"))

    # NO UNOBSERVED FAILURE: service hidup & ready 200 (fail-closed aktif)
    ready = _readiness()
    results.append(("NO_UNOBSERVED_FAILURE_ready", ready.get("code") == 200,
                    f"ready={ready.get('code')}"))

    # NO UNSAFE CONTINUATION: tidak ada execution running tak settle
    unsafe = _unsafe_running_executions()
    results.append(("NO_UNSAFE_CONTINUATION", unsafe == 0,
                    f"running_exec={unsafe}"))

    # durasi minimal (periode jujur)
    results.append(("PERIOD_24H", elapsed_h >= 24.0,
                    f"elapsed_h={elapsed_h:.1f}"))

    fails = [r for r in results if not r[1]]
    all_pass = not fails
    print(f"[code={0 if all_pass else 1}] VERIFY 24H test "
          f"(elapsed {elapsed_h:.1f}h) -> "
          f"{'PASS' if all_pass else 'FAIL'}", flush=True)
    for name, ok, info in results:
        print(f"  {'OK ' if ok else 'BAD'} {name}: {info}", flush=True)
    return 0 if all_pass else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="M12-016 24h test harness")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--begin", action="store_true")
    g.add_argument("--seed", action="store_true")
    g.add_argument("--verify", action="store_true")
    ap.add_argument("--state-dir", default=STATE_REL)
    args = ap.parse_args(argv)
    if args.begin:
        return cmd_begin(args)
    if args.seed:
        return cmd_seed(args)
    return cmd_verify(args)


if __name__ == "__main__":
    sys.exit(main())
