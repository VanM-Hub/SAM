"""sam_watchdog.py — M12-009 External Watchdog (proses terpisah).

Memantau SAM dari LUAR proses server (server tidak mengawasi dirinya sendiri).
Deteksi & alert:
  - DEAD       : tidak bisa konek ke /health (proses server down / koneksi gagal)
  - UNHEALTHY  : /health status != healthy
  - NOT_READY  : /health/ready != 200 (mis. produksi fail-closed, PG down)
  - RESTART_LOOP : status gagal berulang terus dalam window (mengindikasikan
                   crash-restart berulang, bukan hanya satu gangguan)

Mode:
  python sam_watchdog.py --once          -> cek sekali; exit 0/1/2/3 (utk scripting)
  python sam_watchdog.py --interval 30   -> loop polling (utk Task Scheduler / service)

Alert:
  - Windows Event Log (source 'SAM-Watchdog') bila bisa (butuh hak menulis Event Log)
  - File log (--log, default logs/watchdog.log) dengan rotasi sederhana (bounded).

JANGAN dijalankan dari dalam proses server; jalankan terpisah (Task Scheduler).
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_eventlog(message: str, kind: str = "Warning") -> None:
    """Tulis ke Windows Application Event Log bila memungkinkan."""
    try:
        import win32api  # type: ignore
        import win32security  # type: ignore
        import win32evtlogutil  # type: ignore
        import win32con  # type: ignore

        # otentikasi sebagai System supaya source bisa dibuat tanpa admin berkali-kali
        try:
            win32evtlogutil.AddSourceToRegistry("SAM-Watchdog")
        except Exception:
            pass
        win32evtlogutil.ReportEvent(
            "SAM-Watchdog",
            800 + (1 if kind == "Error" else 2 if kind == "Warning" else 0),
            eventCategory=0,
            eventType=win32con.EVENTLOG_ERROR_TYPE if kind == "Error"
            else win32con.EVENTLOG_WARNING_TYPE
            if kind == "Warning" else win32con.EVENTLOG_INFORMATION_TYPE,
            strings=[message],
        )
    except Exception:
        # Event Log tidak tersedia (pywin32 tak ada / non-Windows) -> abaikan,
        # file log tetap jadi sumber alert.
        pass


class _LogRotator:
    """Log bounded: simpan maks N baris (hapus paling lama)."""

    def __init__(self, path: Path, max_lines: int = 500) -> None:
        self.path = path
        self.max_lines = max_lines

    def append(self, line: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        if self.path.exists():
            try:
                lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                lines = []
        lines.append(line)
        if len(lines) > self.max_lines:
            lines = lines[-self.max_lines:]
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_once(base_url: str, timeout: int = 5):
    """Cek kondisi SAM sekali. Return (code, detail). code: 0 ok, 1 dead, 2 not_ready, 3 unhealthy."""
    # 1) /health
    try:
        req = Request(base_url + "/health", headers={"Accept": "application/json"})
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            status = resp.status
    except HTTPError as e:
        body = ""
        status = e.code
    except Exception as e:
        return 1, f"DEAD: tidak bisa konek /health ({e})"

    if status != 200 or '"healthy"' not in body and '"state":"healthy"' not in body.replace(" ", ""):
        return 3, f"UNHEALTHY: /health -> HTTP {status}"

    # 2) /health/ready
    try:
        req2 = Request(base_url + "/health/ready", headers={"Accept": "application/json"})
        with urlopen(req2, timeout=timeout) as resp:
            ready_status = resp.status
    except HTTPError as e:
        ready_status = e.code
    except Exception:
        return 1, "DEAD: /health ok tapi /health/ready gagal konek"

    if ready_status != 200:
        return 2, f"NOT_READY: /health/ready -> HTTP {ready_status} (produksi fail-closed?)"

    return 0, "OK"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SAM External Watchdog (M12-009)")
    ap.add_argument("--url", default=os.environ.get("SAM_URL", "http://127.0.0.1:8080"),
                    help="Base URL SAM (default http://127.0.0.1:8080)")
    ap.add_argument("--interval", type=int, default=30, help="Interval polling detik (loop mode)")
    ap.add_argument("--once", action="store_true", help="Cek sekali lalu keluar")
    ap.add_argument("--log", default=None, help="Path file log (default logs/watchdog.log)")
    ap.add_argument("--window", type=int, default=120, help="Window detik utk restart-loop")
    ap.add_argument("--restart-threshold", type=int, default=4,
                    help="Jumlah kegagalan beruntun dalam window utk dianggap restart-loop")
    args = ap.parse_args(argv)

    log_path = Path(args.log) if args.log else PROJECT_ROOT / "logs" / "watchdog.log"
    rot = _LogRotator(log_path, max_lines=500)

    def alert(code: int, detail: str) -> None:
        kind = "Error" if code == 1 else "Warning"
        line = f"{_now()} [code={code}] {detail}"
        print(line, flush=True)
        rot.append(line)
        _write_eventlog(f"SAM {detail} (watchdog code={code})", kind)

    # --- mode sekali ---
    if args.once:
        code, detail = check_once(args.url)
        print(f"{_now()} [code={code}] {detail}", flush=True)
        if code != 0:
            rot.append(f"{_now()} [code={code}] {detail}")
        return code

    # --- mode loop ---
    print(f"{_now()} SAM Watchdog loop mulai: {args.url} (interval {args.interval}s)", flush=True)
    rot.append(f"{_now()} WATCHDOG start url={args.url} interval={args.interval}s")

    fail_history: list[float] = []
    while True:
        time.sleep(args.interval)
        code, detail = check_once(args.url)
        now = time.time()
        if code == 0:
            fail_history.clear()
            print(f"{_now()} [code=0] OK", flush=True)
            continue
        alert(code, detail)
        fail_history = [t for t in fail_history if now - t <= args.window]
        fail_history.append(now)
        if len(fail_history) >= args.restart_threshold:
            alert(code, f"RESTART_LOOP: {len(fail_history)} kegagalan dalam {args.window}s — "
                        "SAM mungkin crash-restart berulang. Perlu intervensi operator.")


if __name__ == "__main__":
    sys.exit(main())
