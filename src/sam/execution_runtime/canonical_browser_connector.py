"""Canonical Universal Browser Connector - M6-005 (Operational Expansion).

Primitive connector browser yang menghubungkan SAM ke web via satu jalur
canonical (RealExecutionHarness). Ini BUKAN executor baru — adapter yang
dipanggil SATU-SATUNYA melalui RealExecutionHarness (single authority).

Arah arsitektur:
    SAM -> Capability Contract -> Policy -> Approval -> Canonical Execution
        -> Browser Connector -> Web -> Real Response
        -> Verification -> Audit -> Learning

Prinsip jujur (tidak ada mock, tidak ada actor kedua):
  - `fetch_url` = primitive render-agnostik NYATA via httpx (HTTP nyata ke
    server eksternal, read-only, GET). HTML diverifikasi (200 + non-kosong).
    Ini bukan mock: ada HTTP request nyata + respons nyata.
  - `render` = kontrak browser nyata (headless). Tanpa playwright/selenium
    terpasang -> gate BLOCKED (dicatat jujur, TIDAK diklaim sukses). Saat
    driver terpasang, lapisan ini aktif.
  - URL wajib https + valid; tanpa URL / URL tidak dikenal -> RAISE/BLOCKED.
  - READ-ONLY: hanya GET/fetch; tidak menulis, tidak submit form, tidak JS eval.
  - Tidak ada preview menyamar sebagai execution: PREVIEW explicit simulated.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    GateResult,
    GATES,
    RealExecutionHarness,
)


class BrowserConnectorError(Exception):
    """Error connector browser (no side effect)."""


_HTTPS_RE = re.compile(r"^https://[^\s]+$", re.IGNORECASE)


def is_valid_https_url(value: str) -> bool:
    if not _HTTPS_RE.match(value or ""):
        return False
    parsed = urlparse(value)
    return bool(parsed.scheme == "https" and parsed.netloc)


def _browser_driver_available() -> bool:
    """True hanya bila driver browser nyata (playwright/selenium) terpasang."""
    for mod in ("playwright", "selenium"):
        try:
            __import__(mod)
            return True
        except ImportError:
            continue
    return False


class RealBrowserAdapter:
    """Adapter browser. fetch_url = HTTP nyata; render = kontrak (BLOCKED bila tak ada driver)."""

    def __init__(self, audit: AuditTrail) -> None:
        self._audit = audit

    def fetch_url(self, url: str) -> Dict[str, Any]:
        if not is_valid_https_url(url):
            raise BrowserConnectorError(f"URL tidak valid / bukan https: {url}")
        import httpx  # lazy

        self._audit.record("browser.connector.fetch", url)
        try:
            resp = httpx.get(url, timeout=20.0, follow_redirects=True,
                             headers={"User-Agent": "SAM-canonical-browser/1.0"})
        except Exception as exc:  # noqa: BLE001
            self._audit.record("browser.connector.network_fail", url,
                               error=f"{type(exc).__name__}: {exc}")
            raise BrowserConnectorError(f"network: {type(exc).__name__}: {exc}") from exc

        if resp.status_code != 200:
            self._audit.record("browser.connector.non200", url, status=resp.status_code)
            raise BrowserConnectorError(f"HTTP {resp.status_code} (bukan 200): no fake success")

        html = resp.text or ""
        if not html.strip():
            raise BrowserConnectorError("HTML kosong: tidak ada konten nyata")

        # verifikasi: ekstrak <title> bila ada (bukti konten nyata di-fetched)
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = m.group(1).strip() if m else ""
        self._audit.record("browser.connector.result", url,
                           bytes_len=len(html.encode("utf-8")), title=title[:80])
        return {
            "ok": True,
            "url": url,
            "http_status": 200,
            "content_type": resp.headers.get("content-type", ""),
            "html_len": len(html),
            "title": title,
            "fetch_real": True,
        }

    def render(self, url: str) -> Dict[str, Any]:
        """Kontrak browser nyata. BLOCKED bila driver belum terpasang (jujur)."""
        if not is_valid_https_url(url):
            raise BrowserConnectorError(f"URL tidak valid / bukan https: {url}")
        if not _browser_driver_available():
            raise BrowserConnectorError(
                "driver browser nyata (playwright/selenium) belum terpasang - "
                "render headless TIDAK diklaim; pasang driver untuk aktifkan"
            )
        # ---- Lapisan ini aktif bila driver tersedia (belum dieksekusi di test ini) ----
        raise BrowserConnectorError("render nyata butuh konfigurasi driver lebih lanjut")


class RealBrowserConnector:
    """Connector browser dieksekusi HANYA melalui RealExecutionHarness."""

    OPERATIONS = ("fetch_url", "render")

    def __init__(self, audit: Optional[AuditTrail] = None) -> None:
        self._audit = audit or AuditTrail()
        self._harness = RealExecutionHarness(self._audit)
        self._harness.register_capability(
            "browser",
            registry={"id": "browser", "adapter": "RealBrowserAdapter",
                      "external": "web (read-only GET / render headless)",
                      "operations": self.OPERATIONS},
            contract={
                "fetch_url": {"input": "https url", "output": "html+title",
                              "side_effect": "HTTP GET read-only"},
                "render": {"input": "https url", "output": "rendered doc",
                           "side_effect": "headless browser (butuh driver)"},
            },
            policy="ALLOW",
        )

    def gate_browser(self, request: ExecutionRequest, op: str) -> List[Dict[str, Any]]:
        if not self._harness.capability_exists("browser"):
            return [{"id": "capability", "label": "Capability 'browser' tidak terdaftar",
                     "passed": False, "detail": "registry kosong"}]
        full_gates = self._harness._evaluate_gates(request)  # noqa: SLF001
        known = op in self.OPERATIONS
        full_gates = [
            GateResult("boundary", GATES[6]["label"], known, f"operasi '{op}' dikenal")
            if g.id == "boundary" else g
            for g in full_gates
        ]
        # gate driver: render butuh driver; fetch_url tidak (HTTP langsung)
        if op == "render":
            driver_ok = _browser_driver_available()
            label = "Driver browser nyata (playwright/selenium) tersedia"
        else:
            driver_ok = True
            label = "fetch_url tidak butuh driver (HTTP langsung readonly)"
        self._audit.record("browser.gate.driver", op, present=driver_ok)
        drv_gate = {
            "id": "driver_browser",
            "label": label,
            "passed": driver_ok,
            "detail": f"driver_available={_browser_driver_available()}",
        }
        return [g.to_dict() for g in full_gates] + [drv_gate]

    def execute(
        self,
        operation: str,
        url: str,
        mode: ExecutionMode = ExecutionMode.EXECUTE,
        approval_reason: str = "",
    ) -> Dict[str, Any]:
        req = ExecutionRequest(
            operation=f"browser/{operation}",
            target="web",
            params={"operation": operation, "url": url},
            mode=mode,
            correlation_id=f"browser-{operation}",
            timeout_seconds=25.0,
            approval_reason=approval_reason,
        )
        gates = self.gate_browser(req, operation)
        failed = [g for g in gates if not g["passed"]]
        for g in gates:
            self._audit.record("browser.gate", g["id"], passed=g["passed"], label=g["label"])

        if mode == ExecutionMode.PREVIEW:
            self._audit.record("browser.mode.preview", operation)
            return {"ok": True, "mode": "PREVIEW", "simulated": True,
                    "external_calls": 0, "detail": "PREVIEW: no side effect.", "gates": gates}

        if failed:
            self._audit.record("browser.execute.blocked", operation,
                               blocked_by=[g["id"] for g in failed])
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "blocked": True, "blocked_by": [g["id"] for g in failed],
                    "detail": "NO EXTERNAL SIDE EFFECT (P2-B).", "gates": gates}

        self._audit.record("browser.execute.allowed", operation)
        try:
            adapter = RealBrowserAdapter(self._audit)
            if operation == "fetch_url":
                result = adapter.fetch_url(url)
            else:
                result = adapter.render(url)
            return {"ok": result.get("ok"), "mode": "EXECUTE", "gates": gates, **result}
        except BrowserConnectorError as exc:
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": str(exc), "gates": gates, "verification_failed": True}
        except Exception as exc:  # noqa: BLE001
            self._audit.record("browser.connector.fail", operation,
                               error=f"{type(exc).__name__}: {exc}")
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": f"{type(exc).__name__}: {exc}", "gates": gates}


def _online() -> bool:
    try:
        import httpx
        return httpx.get("https://httpbin.org/html", timeout=8).status_code == 200
    except Exception:  # noqa: BLE001
        return False


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="M6-005 Browser Connector (canonical)")
    parser.add_argument("operation", choices=RealBrowserConnector.OPERATIONS,
                        default="fetch_url", nargs="?")
    parser.add_argument("--url", default="https://httpbin.org/html")
    parser.add_argument("--mode", choices=["PREVIEW", "EXECUTE"], default="EXECUTE")
    parser.add_argument("--reason", default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    audit = AuditTrail()
    connector = RealBrowserConnector(audit)
    mode = ExecutionMode(args.mode)
    result = connector.execute(args.operation, args.url, mode=mode,
                               approval_reason=args.reason or f"M6 browser {args.operation}")

    print("=" * 70)
    print("  M6-005 - Browser Connector (via harness canonical)")
    print("=" * 70)
    print(f"  operation : {args.operation}")
    print(f"  mode      : {mode.value}")
    print(f"  internet  : {_online()}")
    print("  gates:")
    for g in result.get("gates", []):
        print(f"    [{'PASS' if g['passed'] else 'FAIL'}] {g['label']}")
    print("  outcome:")
    for k, v in result.items():
        if k == "gates":
            continue
        print(f"    {k} : {str(v)[:160]}")
    print("  audit:")
    for e in audit.entries:
        print(f"    [{e.action}] {e.detail}")
    print("=" * 70)

    if args.operation == "fetch_url" and result.get("ok"):
        print(f"\n  VERDICT: REAL FETCH OK (HTTP nyata, title: {result.get('title','')[:40]})")
        exit_code = 0
    elif result.get("ok"):
        print("\n  VERDICT: OK (render)")
        exit_code = 0
    else:
        print(f"\n  VERDICT: GAGAL/BLOCKED ({result.get('detail') or result.get('error')})")
        exit_code = 1

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"operation": args.operation, "mode": mode.value, "result": result,
                       "audit": [e.__dict__ for e in audit.entries]}, fh, indent=2, default=str)
        print(f"\n[Bukti JSON: {args.out}]")
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())
