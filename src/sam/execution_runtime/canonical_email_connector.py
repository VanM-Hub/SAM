"""Canonical Universal Email Connector - M6-004 (Operational Expansion).

Primitive connector email yang menghubungkan SAM ke email via satu jalur
canonical (RealExecutionHarness). Ini BUKAN executor baru — adapter yang
dipanggil SATU-SATUNYA melalui RealExecutionHarness (single authority).

Arah arsitektur:
    SAM -> Capability Contract -> Policy -> Approval -> Canonical Execution
        -> Email Connector -> SMTP -> Real Response
        -> Verification -> Audit -> Learning

Prinsip jujur (tidak ada mock, tidak ada actor kedua):
  - Kirim email NYATA via SMTP (smtplib) BILA server + kredensial tersedia.
  - Tanpa kredensial SMTP / server tidak tersedia -> gate credential FAIL
    -> BLOCKED (NO SIDE EFFECT), BUKAN mock yang seolah terkirim.
  - `dry_run=True` = VALIDASI EKSPLISIT (bukan kirim nyata): memvalidasi format
    email + kontrak, TIDAK mengirim apa pun. Ditandai jelas `dry_run:true` dan
    `sent:false` — tidak membohongi sebagai sukses kirim.
  - Tanpa sender/recipient valid -> GAGAL/BLOCKED.
  - Tidak ada preview menyamar sebagai execution: PREVIEW explicit simulated.
"""
from __future__ import annotations

import json
import os
import re
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    GateResult,
    GATES,
    RealExecutionHarness,
)


SMTP_HOST_ENV = "SMTP_HOST"
SMTP_PORT_ENV = "SMTP_PORT"
SMTP_USER_ENV = "SMTP_USER"
SMTP_PASS_ENV = "SMTP_PASS"


class EmailConnectorError(Exception):
    """Error connector email (no side effect)."""


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value or ""))


def _smtp_configured() -> bool:
    """True hanya bila host + port + user + pass tersedia di env."""
    return bool(
        os.environ.get(SMTP_HOST_ENV)
        and os.environ.get(SMTP_PORT_ENV)
        and os.environ.get(SMTP_USER_ENV)
        and os.environ.get(SMTP_PASS_ENV)
    )


class RealEmailAdapter:
    """Adapter email NYATA (smtplib). dry_run = validasi eksplisit, tanpa kirim."""

    def __init__(self, audit: AuditTrail) -> None:
        self._audit = audit

    def execute(
        self,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        # VALIDASI kontrak wajib sebelum apapun
        if not is_valid_email(sender):
            raise EmailConnectorError(f"sender tidak valid: {sender}")
        if not is_valid_email(recipient):
            raise EmailConnectorError(f"recipient tidak valid: {recipient}")
        if not subject or not body:
            raise EmailConnectorError("subject & body wajib")

        if dry_run:
            # VALIDASI eksplisit, TIDAK mengirim. Jujur: sent=False.
            self._audit.record("email.connector.dry_run", recipient,
                               sender=sender, subject=subject[:40])
            return {
                "ok": True,
                "mode": "DRY_RUN",
                "dry_run": True,
                "sent": False,
                "detail": "VALIDASI: tidak ada email terkirim (dry_run eksplisit)",
                "sender": sender, "recipient": recipient, "subject": subject,
            }

        # KIRIM NYATA via SMTP. Harus terkonfigurasi.
        if not _smtp_configured():
            raise EmailConnectorError(
                f"SMTP tidak terkonfigurasi (env {SMTP_HOST_ENV}/{SMTP_PORT_ENV}/"
                f"{SMTP_USER_ENV}/{SMTP_PASS_ENV}) - NO SIDE EFFECT"
            )
        host = os.environ[SMTP_HOST_ENV]
        port = int(os.environ[SMTP_PORT_ENV])
        user = os.environ[SMTP_USER_ENV]
        password = os.environ[SMTP_PASS_ENV]

        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)

        self._audit.record("email.connector.send", recipient, host=host, port=port)
        try:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)
        except Exception as exc:  # noqa: BLE001
            self._audit.record("email.connector.fail", recipient,
                               error=f"{type(exc).__name__}: {exc}")
            raise EmailConnectorError(f"smtp: {type(exc).__name__}: {exc}") from exc

        self._audit.record("email.connector.sent", recipient, subject=subject[:40])
        return {
            "ok": True,
            "mode": "SMTP_SEND",
            "dry_run": False,
            "sent": True,
            "detail": "email terkirim via SMTP nyata",
            "sender": sender, "recipient": recipient, "subject": subject,
        }


class RealEmailConnector:
    """Connector email dieksekusi HANYA melalui RealExecutionHarness."""

    OPERATIONS = ("send", "validate")

    def __init__(self, audit: Optional[AuditTrail] = None) -> None:
        self._audit = audit or AuditTrail()
        self._harness = RealExecutionHarness(self._audit)
        self._harness.register_capability(
            "email",
            registry={"id": "email", "adapter": "RealEmailAdapter",
                      "external": "email SMTP", "operations": self.OPERATIONS},
            contract={
                "send": {"input": "sender/recipient/subject/body",
                         "output": "sent:true (SMTP) / sent:false (dry_run)",
                         "side_effect": "SMTP send (nyata) / validasi (dry_run)"},
                "validate": {"input": "email", "output": "valid / tidak",
                             "side_effect": "none"},
            },
            policy="ALLOW",
        )

    def gate_email(self, request: ExecutionRequest, dry_run: bool) -> List[Dict[str, Any]]:
        if not self._harness.capability_exists("email"):
            return [{"id": "capability", "label": "Capability 'email' tidak terdaftar",
                     "passed": False, "detail": "registry kosong"}]
        full_gates = self._harness._evaluate_gates(request)  # noqa: SLF001
        op = request.operation.split("/")[-1]
        known = op in self.OPERATIONS
        full_gates = [
            GateResult("boundary", GATES[6]["label"], known, f"operasi '{op}' dikenal")
            if g.id == "boundary" else g
            for g in full_gates
        ]
        # gate credential: kirim nyata butuh SMTP; dry_run tidak butuh (validasi)
        if op == "send" and not dry_run:
            cred_ok = _smtp_configured()
            label = f"SMTP terkonfigurasi (env {SMTP_HOST_ENV}) utk kirim nyata"
        else:
            cred_ok = True  # dry_run / validate tidak butuh SMTP (validasi eksplisit)
            label = "Tidak butuh SMTP (dry_run/validate = validasi eksplisit)"
        self._audit.record("email.gate.credential", op, dry_run=dry_run, present=cred_ok)
        cred_gate = {
            "id": "credential_email",
            "label": label,
            "passed": cred_ok,
            "detail": f"dry_run={dry_run} smtp_configured={_smtp_configured()}",
        }
        return [g.to_dict() for g in full_gates] + [cred_gate]

    def execute(
        self,
        operation: str,
        params: Dict[str, Any],
        mode: ExecutionMode = ExecutionMode.EXECUTE,
        approval_reason: str = "",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        req = ExecutionRequest(
            operation=f"email/{operation}",
            target="email-smtp",
            params={"operation": operation, **params, "dry_run": dry_run},
            mode=mode,
            correlation_id=f"email-{operation}",
            timeout_seconds=25.0,
            approval_reason=approval_reason,
        )
        gates = self.gate_email(req, dry_run)
        failed = [g for g in gates if not g["passed"]]
        for g in gates:
            self._audit.record("email.gate", g["id"], passed=g["passed"], label=g["label"])

        if mode == ExecutionMode.PREVIEW:
            self._audit.record("email.mode.preview", operation)
            return {"ok": True, "mode": "PREVIEW", "simulated": True,
                    "external_calls": 0, "detail": "PREVIEW: no side effect.", "gates": gates}

        if failed:
            self._audit.record("email.execute.blocked", operation,
                               blocked_by=[g["id"] for g in failed])
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "blocked": True, "blocked_by": [g["id"] for g in failed],
                    "detail": "NO EXTERNAL SIDE EFFECT (P2-B).", "gates": gates}

        self._audit.record("email.execute.allowed", operation)
        try:
            adapter = RealEmailAdapter(self._audit)
            if operation == "validate":
                email = str(params.get("email", ""))
                ok = is_valid_email(email)
                self._audit.record("email.connector.validate", email, valid=ok)
                return {"ok": ok, "mode": "EXECUTE", "gates": gates,
                        "valid": ok, "email": email}
            # send
            result = adapter.execute(
                sender=str(params.get("sender", "")),
                recipient=str(params.get("recipient", "")),
                subject=str(params.get("subject", "")),
                body=str(params.get("body", "")),
                dry_run=dry_run,
            )
            return {"ok": result.get("ok"), "mode": "EXECUTE", "gates": gates, **result}
        except EmailConnectorError as exc:
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": str(exc), "gates": gates, "verification_failed": True}
        except Exception as exc:  # noqa: BLE001
            self._audit.record("email.connector.fail", operation,
                               error=f"{type(exc).__name__}: {exc}")
            return {"ok": False, "mode": "EXECUTE", "external_calls": 0,
                    "error": f"{type(exc).__name__}: {exc}", "gates": gates}


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="M6-004 Email Connector (canonical)")
    parser.add_argument("--to", default="van@sam.local")
    parser.add_argument("--subject", default="M6 email connector")
    parser.add_argument("--body", default="test body")
    parser.add_argument("--dry-run", action="store_true", help="validasi eksplisit, tanpa kirim")
    parser.add_argument("--mode", choices=["PREVIEW", "EXECUTE"], default="EXECUTE")
    parser.add_argument("--reason", default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    audit = AuditTrail()
    connector = RealEmailConnector(audit)
    mode = ExecutionMode(args.mode)
    dry = bool(args.dry_run)
    params = {"sender": "zara@sam.local", "recipient": args.to,
              "subject": args.subject, "body": args.body}
    result = connector.execute("send", params, mode=mode, dry_run=dry,
                               approval_reason=args.reason or f"M6 email -> {args.to}")

    print("=" * 70)
    print("  M6-004 - Email Connector (via harness canonical)")
    print("=" * 70)
    print(f"  dry_run : {dry}")
    print(f"  mode    : {mode.value}")
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

    verbose = " (dry_run: TIDAK ada email terkirim)" if dry and result.get("ok") else ""
    verdict = f"DRY_RUN/validasi OK{verbose}" if result.get("ok") else "GAGAL/BLOCKED"
    print(f"\n  VERDICT: {verdict}")
    exit_code = 0 if result.get("ok") else 1

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"dry_run": dry, "mode": mode.value, "result": result,
                       "audit": [e.__dict__ for e in audit.entries]}, fh, indent=2, default=str)
        print(f"\n[Bukti JSON: {args.out}]")
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())
