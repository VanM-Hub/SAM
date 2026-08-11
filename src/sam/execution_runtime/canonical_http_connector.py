"""Canonical HTTP Universal Connector - M6-001 (Operational Expansion).

Primitive connector HTTP GENERIK yang menghubungkan SAM ke banyak sistem
eksternal via satu jalur canonical (RealExecutionHarness). Ini BUKAN executor
baru — ia adapter yang dipanggil SATU-SATUNYA melalui RealExecutionHarness
(ingle execution authority).

Arah arsitektur:
    SAM -> Capability Contract -> Policy -> Approval -> Canonical Execution
        -> HTTP Connector -> External API -> Real Response
        -> Verification -> Audit -> Learning

Prinsip jujur (tidak ada mock, tidak ada actor kedua):
  - Tanpa kredensial diperlukan untuk endpoint publik -> harus punya kontrak
    eksplisit; kalau endpoint butuh key dan key kosong -> BLOCKED (NO SIDE EFFECT).
  - Tanpa target valid / base_url tidak dikenal -> RAISE, bukan sukses palsu.
  - Respons harus 200 + JSON valid + payload sesuai kontrak -> kalau tidak,
    dianggap GAGAL (verification nyata), bukan dipaksakan sukses.
  - Tidak ada preview menyamar sebagai execution: mode PREVIEW -> explicit,
    EXECUTE -> HTTP nyata.

Endpoint didefinisikan sebagai KONFIGURASI (bukan hardcoded), didaftarkan ke
capability 'http'. READ-ONLY dulu (GET) — aman, mirror pola GitHub P5.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    GateResult,
    GATES,
    RealExecutionHarness,
)


class HttpConnectorError(Exception):
    """Error connector HTTP (no side effect: request tidak dikirim)."""


@dataclass(frozen=True)
class HttpEndpoint:
    """Definisi satu endpoint HTTP eksternal (kontrak + gate credential)."""

    name: str                      # id unik, mis. "jsonplaceholder_posts"
    method: str = "GET"
    url_template: str = ""         # mis. "https://jsonplaceholder.typicode.com/posts/{id}"
    auth_env: str = ""             # env var key; kosong = endpoint publik
    required_params: Tuple[str, ...] = ()
    description: str = ""
    timeout_seconds: float = 20.0

    def resolve_url(self, params: Dict[str, Any]) -> str:
        """Isi placeholder `{x}` di url_template dari params. Gagal -> raise."""
        url = self.url_template
        for key, val in params.items():
            url = url.replace("{" + key + "}", str(val))
        # placeholder tersisa yang belum terisi -> wajib otentikasi
        missing = [seg for seg in url.split("/") if seg.startswith("{") and seg.endswith("}")]
        if missing:
            raise HttpConnectorError(
                "parameter wajib belum ada: " + ", ".join(missing)
            )
        return url

    def auth_headers(self) -> Dict[str, str]:
        """Header auth dari env. Endpoint publik (auth_env kosong) -> {}."""
        if not self.auth_env:
            return {}
        token = os.environ.get(self.auth_env, "")
        if not token:
            raise HttpConnectorError(f"kredensial kosong: env {self.auth_env} (NO SIDE EFFECT)")
        return {"Authorization": f"Bearer {token}"}


# Endpoint default yang dikenali (penuh nyata, publik, tanpa key).
DEFAULT_HTTP_ENDPOINTS: Tuple[HttpEndpoint, ...] = (
    HttpEndpoint(
        name="jsonplaceholder_post",
        method="GET",
        url_template="https://jsonplaceholder.typicode.com/posts/{id}",
        auth_env="",
        required_params=("id",),
        description="REST publik JSONPlaceholder: ambil satu post by id",
    ),
    HttpEndpoint(
        name="jsonplaceholder_user",
        method="GET",
        url_template="https://jsonplaceholder.typicode.com/users/{id}",
        auth_env="",
        required_params=("id",),
        description="REST publik JSONPlaceholder: ambil satu user by id",
    ),
    HttpEndpoint(
        name="httpbin_get",
        method="GET",
        url_template="https://httpbin.org/get",
        auth_env="",
        required_params=(),
        description="httpbin echo: kembalikan request sebagai respons JSON nyata",
    ),
)


class RealHttpAdapter:
    """Adapter HTTP NYATA (httpx). Hanya GET dulu (read-only, aman)."""

    def __init__(self, audit: AuditTrail, endpoints: Tuple[HttpEndpoint, ...]) -> None:
        import httpx  # lazy

        self._httpx = httpx
        self._audit = audit
        self._endpoints = {e.name: e for e in endpoints}

    def get_endpoint(self, name: str) -> HttpEndpoint:
        if name not in self._endpoints:
            raise HttpConnectorError(f"endpoint HTTP tidak dikenal: {name}")
        return self._endpoints[name]

    def _json_or_raise(self, resp) -> Dict[str, Any]:
        if resp.status_code != 200:
            raise HttpConnectorError(
                f"HTTP {resp.status_code} dari target (bukan 200): no fake success"
            )
        try:
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            raise HttpConnectorError(
                f"respons bukan JSON valid: {type(exc).__name__}: {exc}"
            ) from exc

    def execute(self, endpoint_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = self.get_endpoint(endpoint_name)

        # VERIFIKASI KONTRAK: parameter wajib ada sebelum request
        for req in endpoint.required_params:
            if req not in params or params.get(req) in (None, ""):
                raise HttpConnectorError(f"param '{req}' wajib untuk endpoint {endpoint_name}")

        url = endpoint.resolve_url(params)
        headers = endpoint.auth_headers()  # raise bila key kosong (endpoint ber-auth)
        headers["Accept"] = "application/json"

        self._audit.record("http.connector.call", endpoint_name, url=url)
        try:
            resp = self._httpx.get(url, headers=headers, timeout=endpoint.timeout_seconds)
        except Exception as exc:  # noqa: BLE001
            self._audit.record("http.connector.network_fail", endpoint_name,
                               error=f"{type(exc).__name__}: {exc}")
            raise HttpConnectorError(f"network: {type(exc).__name__}: {exc}") from exc

        self._audit.record("http.connector.response", endpoint_name, status=resp.status_code)
        data = self._json_or_raise(resp)  # 200 + JSON valid wajib

        self._audit.record("http.connector.result", endpoint_name,
                           keys=list(data.keys())[:8], content_length=str(data)[:100])
        return {
            "ok": True,
            "endpoint": endpoint_name,
            "url": url,
            "http_status": resp.status_code,
            "content_type": resp.headers.get("content-type", ""),
            "data": data,
        }


class RealHttpConnector:
    """Connector HTTP yang dieksekusi HANYA melalui RealExecutionHarness.

    Satu-satunya jalur eksekusi adalah `execute()` yang lewat gate P2-B +
    gate credential per endpoint -> adapter nyata -> verification -> audit.
    Tidak ada jalur kedua (agent/user tidak bisa invoke adapter langsung).
    """

    def __init__(
        self,
        audit: Optional[AuditTrail] = None,
        endpoints: Tuple[HttpEndpoint, ...] = DEFAULT_HTTP_ENDPOINTS,
    ) -> None:
        self._audit = audit or AuditTrail()
        self._endpoints = endpoints
        self._harness = RealExecutionHarness(self._audit)
        operations = tuple(e.name for e in endpoints)
        self._harness.register_capability(
            "http",
            registry={"id": "http", "adapter": "RealHttpAdapter",
                      "external": "HTTP external API (read-only GET)",
                      "operations": operations},
            contract={
                e.name: {"method": e.method, "input": "params",
                         "output": "verified JSON", "side_effect": f"HTTP {e.method}"}
                for e in endpoints
            },
            policy="ALLOW",
        )

    def gate_http(self, request: ExecutionRequest) -> List[Dict[str, Any]]:
        if not self._harness.capability_exists("http"):
            return [{"id": "capability", "label": "Capability 'http' tidak terdaftar",
                     "passed": False, "detail": "registry kosong"}]
        full_gates = self._harness._evaluate_gates(request)  # noqa: SLF001 - gate P2-B
        # boundary hardcoded file -> timpa utk http: target = endpoint dikenal
        endpoint_name = request.operation.split("/")[-1]
        known = endpoint_name in {e.name for e in self._endpoints}
        full_gates = [
            GateResult("boundary", GATES[6]["label"], known, f"endpoint '{endpoint_name}' dikenal")
            if g.id == "boundary" else g
            for g in full_gates
        ]
        # gate credential per endpoint
        ep = next((e for e in self._endpoints if e.name == endpoint_name), None)
        if ep is None:
            cred_ok = False
            _env_label = "(unknown endpoint)"
        elif not ep.auth_env:
            cred_ok = True  # endpoint publik, tanpa key
            _env_label = "(publik, tanpa key)"
        else:
            cred_ok = bool(os.environ.get(ep.auth_env, ""))
            _env_label = f"env={ep.auth_env}"
        self._audit.record("http.gate.credential", endpoint_name, present=cred_ok)
        cred_gate = {
            "id": "credential_http",
            "label": f"Kredensial endpoint '{endpoint_name}' tersedia ({_env_label})",
            "passed": cred_ok,
            "detail": _env_label,
        }
        return [g.to_dict() for g in full_gates] + [cred_gate]

    def execute(
        self,
        endpoint_name: str,
        params: Dict[str, Any],
        mode: ExecutionMode = ExecutionMode.EXECUTE,
        approval_reason: str = "",
    ) -> Dict[str, Any]:
        req = ExecutionRequest(
            operation=f"http/{endpoint_name}",
            target="http-api",
            params={"endpoint": endpoint_name, **params},
            mode=mode,
            correlation_id=f"http-{endpoint_name}",
            timeout_seconds=30.0,
            approval_reason=approval_reason,
        )
        gates = self.gate_http(req)
        failed = [g for g in gates if not g["passed"]]
        for g in gates:
            self._audit.record("http.gate", g["id"], passed=g["passed"], label=g["label"])

        if mode == ExecutionMode.PREVIEW:
            self._audit.record("http.mode.preview", endpoint_name)
            return {"ok": True, "mode": "PREVIEW", "simulated": True,
                    "external_calls": 0, "detail": "PREVIEW: no side effect.", "gates": gates}

        if failed:
            self._audit.record("http.execute.blocked", endpoint_name,
                               blocked_by=[g["id"] for g in failed])
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "blocked": True, "blocked_by": [g["id"] for g in failed],
                    "detail": "NO EXTERNAL SIDE EFFECT (P2-B).", "gates": gates}

        self._audit.record("http.execute.allowed", endpoint_name)
        try:
            adapter = RealHttpAdapter(self._audit, self._endpoints)
            result = adapter.execute(endpoint_name, params)
            return {"ok": result.get("ok"), "mode": "EXECUTE", "gates": gates, **result}
        except HttpConnectorError as exc:
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": str(exc), "gates": gates, "verification_failed": True}
        except Exception as exc:  # noqa: BLE001
            self._audit.record("http.connector.fail", endpoint_name,
                               error=f"{type(exc).__name__}: {exc}")
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": f"{type(exc).__name__}: {exc}", "gates": gates}


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="M6-001 HTTP Universal Connector (canonical)")
    parser.add_argument("endpoint", choices=[e.name for e in DEFAULT_HTTP_ENDPOINTS])
    parser.add_argument("--id", default="1", help="nilai param id untuk endpoint yang butuh id")
    parser.add_argument("--mode", choices=["PREVIEW", "EXECUTE"], default="EXECUTE")
    parser.add_argument("--reason", default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    audit = AuditTrail()
    connector = RealHttpConnector(audit)
    mode = ExecutionMode(args.mode)

    params: Dict[str, Any] = {}
    if args.endpoint.startswith("jsonplaceholder"):
        params["id"] = args.id

    result = connector.execute(args.endpoint, params, mode=mode,
                               approval_reason=args.reason or f"M6 eksekusi {args.endpoint}")

    print("=" * 70)
    print("  M6-001 - HTTP Universal Connector (via harness canonical)")
    print("=" * 70)
    print(f"  endpoint : {args.endpoint}")
    print(f"  mode     : {mode.value}")
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

    if mode == ExecutionMode.EXECUTE:
        ok = result.get("ok")
        print(f"\n  VERDICT: {'REAL E2E OK (HTTP nyata ke external API)' if ok else 'GAGAL/BLOCKED'}")
        exit_code = 0 if ok else 1
    else:
        print("\n  VERDICT: PREVIEW OK (no side effect)")
        exit_code = 0

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"endpoint": args.endpoint, "mode": mode.value, "result": result,
                       "audit": [e.__dict__ for e in audit.entries]}, fh, indent=2, default=str)
        print(f"\n[Bukti JSON: {args.out}]")
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())
