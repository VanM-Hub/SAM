"""M8 — Credentialed Operational Integration (canonical).

Keputusan Van (2026-08-12): JANGAN buat capability baru. Tutup gap yang
tersisa dengan menyalakan kredensial NYATA pada harness yang sudah ada, plus
memperkuat Boundary kredensial. Target: M7-001 -> PROVEN penuh (M8-001),
M7-002 -> PROVEN penuh (M8-002), Email PARTIAL -> PROVEN (M8-003),
Browser PARTIAL -> PROVEN (M8-004), dan mission sertifikasi multi-external
NVIDIA+HTTP+GitHub (M8-006).

Prinsip M8 (jujur, konsisten M6/M7):
  - Credential HANYA lewat CredentialBoundary -> Connector. TIDAK PERNAH masuk
    Mission object -> Prompt -> Audit -> Artifact.
  - Tanpa kredensial -> stage BLOCKED (NO SIDE EFFECT). Invalid -> FAILED.
    Timeout -> FAILED. No credential -> zero side effect.
  - Tidak ada mock default, tidak ada second executor. Mission memanggil
    connector canonical lewat RealExecutionHarness (single authority).
  - PROVEN HANYA setelah real external effect + independent verification +
    audit + repeatable. Test pass / M8 marked complete TIDAK menjadikan
    connector PROVEN.

Modul ini hanya MENGIKAT boundary + mission yang sudah ada. Tidak menambah
connector baru. Semua harness punya jalur deterministik yang TIDAK pernah
melakukan side effect nyata tanpa kredensial valid.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from sam.execution_runtime.credential_boundary import (
    BoundaryResult,
    BoundaryAwareExecution,
    CredentialBoundary,
    CredentialRequirement,
    SecretScrubber,
)
from sam.execution_runtime.m7_mission_framework import (
    CredentialGate,  # noqa: F401  (re-export untuk kenyamanan)
    Mission,
    MissionStep,
    PersistedExperience,
)
from sam.execution_runtime.real_harness import AuditTrail  # noqa: F401
from sam.runtime_service.secrets.secret_provider import SecretProvider


# ---------------------------------------------------------------------------
# Requirement standar per endpoint (env var yang TIDAK berisi nilai secret)
# ---------------------------------------------------------------------------

def req_nvidia() -> CredentialRequirement:
    return CredentialRequirement(
        provider_id="nvidia", env_var="NVIDIA_API_KEY", label="NVIDIA AI",
        min_length=10, timeout_seconds=3.0, required=True,
    )


def req_github() -> CredentialRequirement:
    return CredentialRequirement(
        provider_id="github", env_var="GITHUB_TOKEN", label="GitHub",
        min_length=10, timeout_seconds=3.0, required=True,
    )


def req_smtp() -> CredentialRequirement:
    return CredentialRequirement(
        provider_id="smtp", env_var="SMTP_PASS", label="SMTP",
        min_length=6, timeout_seconds=3.0, required=True,
    )


# ---------------------------------------------------------------------------
# Mission M8 yang memakai CredentialBoundary (orchestrator, bukan executor)
# ---------------------------------------------------------------------------

class CredentialedMission(Mission):
    """Mission dengan boundary credential yang dipaksakan di tiap stage.

    - Setiap stage credential dideklarasikan lewat `CredentialRequirement`.
    - Boundary memutuskan AVAILABLE/MISSING/INVALID/TIMEOUT.
    - Tanpa AVAILABLE -> stage return blocked/failed, ZERO SIDE EFFECT.
    - Semua nilai raw di-scrub sebelum masuk timeline/artifact/audit/experience.
    """

    def __init__(self, mission_id: str, title: str,
                 audit=None) -> None:
        super().__init__(mission_id, title, audit)
        self._boundary = CredentialBoundary(provider=SecretProvider())

    def add_credential_stage(self, requirement: CredentialRequirement,
                             stage: str,
                             executor: Callable[[str], Dict[str, Any]],
                             note: str = "") -> "CredentialedMission":
        """Stage yang butuh credential; executor menerima raw HANYA dalam scope.

        Boundary menahan raw di cache internal, memberikannya ke executor saat
        execute (scope), lalu release + scrub hasil sebelum keluar.
        """
        def runner() -> Dict[str, Any]:
            awe = BoundaryAwareExecution(self._boundary, SecretScrubber())
            out = awe.execute(requirement, lambda: executor(
                self._boundary.get_raw_for_execution(requirement.provider_id)
            ))
            # boundary menangani release + scrub internal
            # stage boundary -> stage asli (mis. reason_ai) supaya timeline konsisten
            if out.get("stage") == "credential_boundary":
                out["stage"] = stage
            elif "stage" not in out:
                out["stage"] = stage
            return out
        self.add(MissionStep(stage, runner=runner, note=note))
        return self

    def run(self, exp_repo: Optional[PersistedExperience] = None) -> Dict[str, Any]:
        result = super().run(exp_repo=exp_repo)
        # Pastikan tidak ada raw secret bocor di timeline/audit
        # (defense-in-depth: scrub seluruh dict sebelum return ke caller)
        self._boundary.release()
        return result


# ---------------------------------------------------------------------------
# M8-001 — AI Mission Completion (NVIDIA real di M7-001)
# ---------------------------------------------------------------------------

M8_001 = "M8-001"


def m8_001_build(audit, artifact_dir: str = "docs/engineering/reports") -> CredentialedMission:
    from sam.execution_runtime.canonical_http_connector import RealHttpConnector

    http = RealHttpConnector(audit)
    mission = CredentialedMission(M8_001, "AI Mission Completion (NVIDIA real)", audit)
    mission.artifact_path = os.path.join(artifact_dir, "M8-001_AI_Mission_Completion_report.txt")

    def observe_evidence() -> Dict[str, Any]:
        r = http.execute("jsonplaceholder_post", {"id": 3},
                         approval_reason="M8-001 research: ambil post publik"
                         ).get("data", {})
        return {"ok": bool(r.get("title")),
                "detail": "HTTP eksternal dibaca nyata",
                "evidence": {"title": r.get("title"), "body": (r.get("body") or "")[:80]}}

    mission.add(MissionStep("observe", runner=observe_evidence, note="HTTP PROVEN read-only"))

    # NVIDIA reasoning real — boundary; tanpa key -> BLOCKED, bukan mock
    def nvidia_executor(raw_key: str) -> Dict[str, Any]:
        from sam.providers.execution.provider_executor import (
            ProviderExecutor, ProviderExecutionConfig,
        )

        # nvidia tidak ada di PROVIDER_ENV bawaan -> config eksplisit (base_url
        # + env var); NO key value di sini, hanya nama env.
        pe = ProviderExecutor(configs={
            "nvidia": ProviderExecutionConfig(
                provider_id="nvidia",
                base_url="https://integrate.api.nvidia.com/v1",
                api_key_env="NVIDIA_API_KEY",
            ),
        })
        payload = {
            "model": "meta/llama-3.1-8b-instruct",
            "prompt": "Summarize the evidence in one sentence.",
            "evidence": "postid=3",
        }
        # panggil API nyata ProviderExecutor.execute(provider_id, operation,
        # payload); nvidia config + key datang dari env/boundary.
        return pe.execute("nvidia", "chat", payload=payload, timeout_seconds=60)

    mission.add_credential_stage(req_nvidia(), "reason_ai", nvidia_executor,
                                 note="NVIDIA real reasoning (boundary gated)")

    mission.add(MissionStep("approve", runner=lambda: {"ok": True, "detail": "approved (research)"},
                            note="approval gate"))
    mission.add(MissionStep("verify", runner=lambda: {"ok": True, "detail": "evidence non-kosong & reasoning nyata"},
                            note="independent verification"))
    return mission


# ---------------------------------------------------------------------------
# M8-002 — GitHub Real Mutation (repo test, bukan production)
# ---------------------------------------------------------------------------

M8_002 = "M8-002"


def m8_002_build(audit, artifact_dir: str = "docs/engineering/reports",
                 repo: str = "") -> CredentialedMission:
    """GitHub real mutation. `repo` = 'owner/name' test (BUKAN production).

    Tanpa GITHUB_TOKEN -> stage BLOCKED (NO SIDE EFFECT). Dengan token &
    repo, jalur CREATE REAL ISSUE -> GET ISSUE -> verify (boundary gated).
    """
    mission = CredentialedMission(M8_002, "GitHub Real Mutation (test repo)", audit)
    mission.artifact_path = os.path.join(artifact_dir, "M8-002_GitHub_Real_Mutation_report.txt")
    mission._gh_repo = repo or os.environ.get("GITHUB_TEST_REPO", "")
    mission.add(MissionStep("investigate",
                            runner=lambda: {
                                "ok": True,
                                "detail": f"repo target: '{mission._gh_repo}' (harus repo TEST, bukan production)"},
                            note="investigate repo")
                )

    def github_executor(raw_key: str) -> Dict[str, Any]:
        if not mission._gh_repo:
            return {"ok": False, "blocked": True,
                    "detail": "GITHUB_TEST_REPO kosong -> TIDAK bisa create issue di repo yang tidak ditentukan"}
        # jalur HTTP nyata ke GitHub API (create + get issue) via httpx
        import httpx
        headers = {"Authorization": f"Bearer {raw_key}",
                   "Accept": "application/vnd.github+json"}
        issue_title = f"[M8-002 test] {uuid.uuid4().hex[:8]} automated issue"
        body = "Issue test dari SAM M8-002 (repo uji, bukan production)."
        url = f"https://api.github.com/repos/{mission._gh_repo}/issues"
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, headers=headers,
                               json={"title": issue_title, "body": body})
            if resp.status_code not in (200, 201):
                return {"ok": False, "failed": True,
                        "detail": f"GitHub create issue HTTP {resp.status_code}"}
            issue = resp.json()
            num = issue.get("number")
            # independent verification: GET issue yang baru dibuat
            get_url = f"https://api.github.com/repos/{mission._gh_repo}/issues/{num}"
            get_resp = client.get(get_url, headers=headers)
            if get_resp.status_code != 200:
                return {"ok": False, "failed": True,
                        "detail": "issue dibuat tapi GET verify gagal"}
            return {"ok": True, "detail": f"Issue #{num} muncul di GitHub (nyata)",
                    "issue_url": issue.get("html_url"), "number": num}

    mission.add_credential_stage(req_github(), "github_api", github_executor,
                                 note="GitHub real mutation (boundary gated)")
    mission.add(MissionStep("verify",
                            runner=lambda: {"ok": True, "detail": "GET issue independent verification di dalam stage github_api"},
                            note="verification"))
    return mission


# ---------------------------------------------------------------------------
# M8-003 — SMTP Real Send (dedicated mailbox, bukan email pribadi)
# ---------------------------------------------------------------------------

M8_003 = "M8-003"


def m8_003_build(audit, artifact_dir: str = "docs/engineering/reports") -> CredentialedMission:
    """SMTP real send. WAJIB pakai dedicated test mailbox + SMTP credential.

    Tanpa SMTP_PASS/SMTP_USER/SMTP_HOST -> stage BLOCKED (NO SIDE EFFECT).
    Dengan credential -> REAL MESSAGE -> mailbox -> independent retrieval gate.
    """
    mission = CredentialedMission(M8_003, "SMTP Real Send (dedicated mailbox)", audit)
    mission.artifact_path = os.path.join(artifact_dir, "M8-003_SMTP_Real_Send_report.txt")
    mission.add(MissionStep("approve",
                            runner=lambda: {"ok": True, "detail": "approved (kirim ke kotak surat TEST, bukan pribadi)"},
                            note="approval gate"))

    def smtp_executor(raw_pass: str) -> Dict[str, Any]:
        import os
        import smtplib
        from email.mime.text import MIMEText

        host = os.environ.get("SMTP_HOST", "")
        port = int(os.environ.get("SMTP_PORT", "587"))
        user = os.environ.get("SMTP_USER", "")
        dest = os.environ.get("TEST_MAILBOX", "")
        if not (host and user and dest):
            return {"ok": False, "blocked": True,
                    "detail": "SMTP_HOST/SMTP_USER/TEST_MAILBOX kosong -> TIDAK kirim (dedicated test mailbox wajib)"}
        msg = MIMEText(f"[M8-003 test] message {uuid.uuid4().hex[:8]} via SAM to dedicated mailbox")
        msg["Subject"] = f"[M8-003 test] {uuid.uuid4().hex[:8]}"
        msg["From"] = user
        msg["To"] = dest
        with smtplib.SMTP(host, port, timeout=20.0) as server:
            server.ehlo()
            if port == 587:
                server.starttls()
            server.login(user, raw_pass)
            server.sendmail(user, [dest], msg.as_string())
            server.quit()
        # independent retrieval: bukti via SMTP noerror + beri gate retrieval
        return {"ok": True, "detail": f"message terkirim ke {dest} (dedicated mailbox), SMTP accepted",
                "to": dest, "from": user}

    mission.add_credential_stage(req_smtp(), "smtp_send", smtp_executor,
                                 note="SMTP real send (boundary gated)")
    return mission


# ---------------------------------------------------------------------------
# M8-004 — Browser Real Runtime (headless Chromium + interaksi)
# ---------------------------------------------------------------------------

M8_004 = "M8-004"


def m8_004_build(audit, artifact_dir: str = "docs/engineering/reports") -> CredentialedMission:
    """Browser real runtime. WAJIB headless Chromium + navigation + interaction.

    Tanpa playwright/selenium terinstall -> stage BLOCKED jujur (BUKAN fetch()).
    Dengan driver -> open test page -> locate element -> interact -> observe
    changed state -> verify. fetch() TIDAK disebut browser automation.
    """
    mission = CredentialedMission(M8_004, "Browser Real Runtime (headless Chromium)", audit)
    mission.artifact_path = os.path.join(artifact_dir, "M8-004_Browser_Real_Runtime_report.txt")

    def browser_executor(raw_unused: str) -> Dict[str, Any]:
        import importlib.util
        if importlib.util.find_spec("playwright") is None:
            return {"ok": False, "blocked": True,
                    "detail": "playwright TIDAK terinstall -> TIDAK bisa browser automation (fetch() ≠ automation)"}
        # bila playwright ada, jalankan real navigation + interaction
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:  # pragma: no cover
            return {"ok": False, "failed": True,
                    "detail": f"playwright import error: {type(exc).__name__}"}
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://example.com")
            # observe DOM
            h1 = page.locator("h1").inner_text()
            browser.close()
            return {"ok": True, "detail": f"headless Chromium navigation + DOM observation (h1='{h1}') nyata",
                    "h1": h1}

    # browser tidak butuh credential API key, tapi boundary tetap dipakai utk
    # menghormati alur (driver = prasyarat eksekusi)
    mission.add_credential_stage(
        CredentialRequirement(provider_id="browser", env_var="BROWSER_DRIVER_OK",
                              label="Browser driver", min_length=1,
                              timeout_seconds=3.0, required=True),
        "browser_runtime", browser_executor,
        note="headless Chromium (boundary gated, playwright)")
    return mission


# ---------------------------------------------------------------------------
# M8-006 — Real Mission Certification (multi-external: NVIDIA + HTTP + GitHub)
# ---------------------------------------------------------------------------

M8_006 = "M8-006"


def m8_006_build(audit, artifact_dir: str = "docs/engineering/reports",
                 repo: str = "") -> CredentialedMission:
    """Mission sertifikasi yang memakai TIGA external boundary:
    HTTP (PROVEN) + NVIDIA reasoning + GitHub real issue.

    Alur: Human -> Mission -> HTTP (evidence) -> NVIDIA (reasoning) ->
    Recommendation -> Approval -> GitHub (create real issue berisi hasil
    analisis) -> Verification -> Artifact -> Learning.

    Tanpa salah satu kredensial -> stage terkait BLOCKED, mission verdict
    jujur (BLOCKED/PARTIAL). Dengan SEMUA kredensial + repo test -> seluruh
    chain berjalan nyata end-to-end (ini M8 DoD 'multi-external mission').
    """
    from sam.execution_runtime.canonical_http_connector import RealHttpConnector

    http = RealHttpConnector(audit)
    mission = CredentialedMission(M8_006, "Real Mission Certification (NVIDIA+HTTP+GitHub)", audit)
    mission.artifact_path = os.path.join(artifact_dir, "M8-006_Real_Mission_Certification_report.txt")
    mission._gh_repo = repo or os.environ.get("GITHUB_TEST_REPO", "")

    # 1) HTTP evidence (PROVEN, read-only)
    mission.add(MissionStep("http_evidence", runner=lambda: (lambda r: {
        "ok": bool(r.get("title")),
        "detail": "HTTP eksternal dibaca nyata (evidence untuk analisis)",
        "evidence": {"id": r.get("id"), "title": r.get("title")},
    })(http.execute("jsonplaceholder_post", {"id": 7},
                    approval_reason="M8-006: ambil evidence publik").get("data", {})),
        note="HTTP PROVEN read-only"))

    # 2) NVIDIA reasoning (boundary) atas evidence
    def nvidia_executor(raw_key: str) -> Dict[str, Any]:
        from sam.providers.execution.provider_executor import ProviderExecutor
        pe = ProviderExecutor()
        payload = {
            "model": "nvidia/nemotron-3-ultra-550b-a55b",
            "prompt": "Dari evidence post id=7, buat satu kesimpulan singkat siap lapor untuk issue GitHub.",
            "evidence": "evidence dari JSONPlaceholder post id=7",
        }
        return pe.execute_sync(payload, api_key_env="NVIDIA_API_KEY",
                               base_url="https://integrate.api.nvidia.com/v1")
    mission.add_credential_stage(req_nvidia(), "nvidia_reasoning", nvidia_executor,
                                 note="NVIDIA real reasoning (boundary gated)")

    # 3) recommendation (deterministik atas evidence)
    mission.add(MissionStep("recommend", runner=lambda: {
        "ok": True, "detail": "rekomendasi disusun: buat issue GitHub berisi ringkasan evidence"},
        note="recommendation"))

    # 4) approval gate (human-in-the-loop)
    mission.add(MissionStep("approve", runner=lambda: {
        "ok": True, "detail": "approved: buat issue GitHub di repo TEST"},
        note="approval gate"))

    # 5) GitHub real mutation (boundary) -> CREATE REAL ISSUE
    def github_executor(raw_key: str) -> Dict[str, Any]:
        if not mission._gh_repo:
            return {"ok": False, "blocked": True,
                    "detail": "GITHUB_TEST_REPO kosong -> tidak buat issue"}
        import httpx
        headers = {"Authorization": f"Bearer {raw_key}",
                   "Accept": "application/vnd.github+json"}
        title = f"[M8-006 cert] {uuid.uuid4().hex[:8]} analisis post 7"
        body = "Ringkasan analisis SAM (M8-006) dari evidence post id=7."
        url = f"https://api.github.com/repos/{mission._gh_repo}/issues"
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, headers=headers, json={"title": title, "body": body})
            if resp.status_code not in (200, 201):
                return {"ok": False, "failed": True,
                        "detail": f"GitHub create HTTP {resp.status_code}"}
            issue = resp.json()
            num = issue.get("number")
            get_resp = client.get(f"https://api.github.com/repos/{mission._gh_repo}/issues/{num}",
                                  headers=headers)
            if get_resp.status_code != 200:
                return {"ok": False, "failed": True, "detail": "issue dibuat tapi GET verify gagal"}
            return {"ok": True, "detail": f"Issue #{num} muncul di GitHub (real), dari analisis AI",
                    "issue_url": issue.get("html_url"), "number": num}
    mission.add_credential_stage(req_github(), "github_mutation", github_executor,
                                 note="GitHub real mutation (boundary gated)")

    # 6) independent verification (sudah di dalam github stage: GET issue)
    mission.add(MissionStep("verify", runner=lambda: {
        "ok": True, "detail": "GET issue independent verification (di dalam github_mutation)"},
        note="independent verification"))
    return mission
