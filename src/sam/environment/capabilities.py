"""Environment-adaptive: factory ward/fixture spesifik -> CapabilityProvider.

"Membangun jembatan yang menjadikan ward spesifik (Word, PDF, OpenClaw,
GitHub/Project, Provider) sebagai INSTANCE terdaftar pada mesin generic" --
bukan katalog yang SAM andalkan. Mesin generic (AdaptiveEnvironmentPipeline)
TIDAK membutuhkan registry ini; ia berjalan penuh TANPA provider. Provider
hanya menambah OBSERVASI (evidence read-only) bila didaftarkan.

Setiap provider dibungkus dari class investigasi/ward lama (reuse, bukan
duplikat). Provider TIDAK mengeksekusi apa pun: remediate di sini hanya
melaporkan ketersediaan capability; eksekusi tetap lewat canonical.

ward_spesifik = "capability instance", bukan "application catalogue":
  - TIDAK ada daftar nama aplikasi yg dipakai discovery utk TAHU environment.
  - Discovery generik (process/port/file) yang menentukan entitas.
  - Provider hanya menambah evidence observasi untuk entitas yang sudah ada.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from sam.environment.confidence import Evidence
from sam.environment.providers import CapabilityProvider, ProviderRegistry


def _ev(provider: str, label: str, detail: str,
        strength: float) -> Evidence:
    """Buat Evidence observasi dari provider (source = nama provider)."""
    return Evidence(source=provider, statement=f"{label}: {detail}",
                    strength=strength)


# ---------------------------------------------------------------------------
# Word (.docx) provider — observation instance (read-only)
# ---------------------------------------------------------------------------

def word_provider(
    investigator: Any = None,
) -> Optional[CapabilityProvider]:
    """Wrap WordInvestigator jadi provider observasi instance.

    `investigator` adalah instance WordInvestigator (default None -> tak ada
    probe nyata bila class tidak tersedia). Provider hanya mengamati: buka
    struktur docx dan hasilkan evidence struktur, tanpa isi.
    """
    try:
        from sam.delegated_authority.real_word_investigation import (
            WordInvestigator,
        )
    except Exception:  # noqa: BLE001 - optional
        return None
    inv = investigator or WordInvestigator()
    known = getattr(inv, "investigate", None)
    if known is None:
        return None

    return CapabilityProvider(
        name="word",
        kind="file",
        observe_fn=lambda: _word_observe(inv),
        description=(
            "Word .docx structure investigation (read-only, metadata/structure)"),
    )


def _word_observe(investigator: Any) -> List[Evidence]:
    """Observasi default: probe file-word saat ini (bila ada di attr)."""
    result = []
    for path in _candidate_docx(investigator):
        try:
            inv = investigator.investigate(path)
            result.append(_ev(
                "word", "docx_investigated",
                f"valid={inv.is_valid} size={inv.size_bytes} "
                f"paras={inv.paragraph_count} tables={inv.table_count}",
                strength=0.7 if inv.is_valid else 0.2,
            ))
        except Exception:  # noqa: BLE001 - skip satu file
            continue
    if not result:
        result.append(_ev(
            "word", "docx_absent", "no docx observed - nil impact",
            strength=0.0,
        ))
    return result


def _candidate_docx(investigator: Any) -> List[str]:
    """Daftar path docx yang akan diobservasi (dari atribut investigator).

    Default kosong -> observasi menyatakan "tidak ada docx diobservasi"
    (jujur), TIDAK mengarang. Bila user mengisi investigator.targets, probe itu.
    """
    targets = getattr(investigator, "targets", None) or []
    return list(targets)


# ---------------------------------------------------------------------------
# PDF provider — observation instance (read-only)
# ---------------------------------------------------------------------------

def pdf_provider(investigator: Any = None) -> Optional[CapabilityProvider]:
    """Wrap PDFPerformanceInvestigator jadi provider observasi instance."""
    try:
        from sam.delegated_authority.real_pdf_investigation import (
            PDFPerformanceInvestigator,
        )
    except Exception:  # noqa: BLE001 - optional
        return None
    inv = investigator or PDFPerformanceInvestigator()
    if not hasattr(inv, "investigate"):
        return None
    return CapabilityProvider(
        name="pdf",
        kind="file",
        observe_fn=lambda: _pdf_observe(inv),
        description=(
            "PDF performance/structure investigation (read-only, no content)"),
    )


def _pdf_observe(investigator: Any) -> List[Evidence]:
    result = []
    for path in (getattr(investigator, "targets", None) or []):
        try:
            inv = investigator.investigate(path)
            result.append(_ev(
                "pdf", "pdf_investigated",
                f"valid={inv.is_valid} perf={inv.performance_level} "
                f"size={inv.size_bytes}",
                strength=0.7 if inv.is_valid else 0.2,
            ))
        except Exception:  # noqa: BLE001 - skip
            continue
    if not result:
        result.append(_ev(
            "pdf", "pdf_absent", "no pdf observed - nil impact", strength=0.0))
    return result


# ---------------------------------------------------------------------------
# OpenClaw provider — observation instance (health read-only)
# ---------------------------------------------------------------------------

def openclaw_provider(workspace: str = "") -> Optional[CapabilityProvider]:
    """Wrap OpenClawWard jadi provider observasi instance (health read-only)."""
    try:
        from sam.delegated_authority.real_openclaw_ward import OpenClawWard
    except Exception:  # noqa: BLE001 - optional
        return None

    def _observe() -> List[Evidence]:
        import asyncio
        ward = OpenClawWard(workspace=workspace)
        diag = asyncio.run(ward.diagnose())
        det = len(diag.detections)
        return [_ev(
            "openclaw", "runtime_diagnosed",
            f"status={diag.runtime_status} detections={det}",
            strength=0.9 if diag.healthy else 0.4,
        )]

    return CapabilityProvider(
        name="openclaw",
        kind="service",
        observe_fn=_observe,
        description=(
            "OpenClaw runtime health observation (read-only health/log)"),
    )


# ---------------------------------------------------------------------------
# GitHub / Project provider — observation instance (read-only detect)
# ---------------------------------------------------------------------------

def project_guardian_provider(
    kind: str = "github", owner: str = "", repo: str = "",
    path: str = "",
) -> Optional[CapabilityProvider]:
    """Wrap ProjectGuardian.detect jadi provider observasi instance."""
    try:
        from sam.delegated_authority.real_project_guardian import (
            GitHubProbe, LocalProjectProbe, ProjectGuardian, ProjectKind,
        )
    except Exception:  # noqa: BLE001 - optional
        return None

    guardian = ProjectGuardian(
        github_probe=GitHubProbe(), local_probe=LocalProjectProbe())

    def _observe() -> List[Evidence]:
        if kind == ProjectKind.LOCAL:
            probe = guardian.detect(kind=kind, target=path)
        else:
            probe = guardian.detect(kind=kind, owner=owner, repo=repo)
        return [_ev(
            "github" if kind == ProjectKind.GITHUB else "local",
            "project_probed",
            f"reachable={probe.reachable} issues={len(probe.issues)} "
            f"detail={probe.detail}",
            strength=0.8 if probe.reachable else 0.2,
        )]

    return CapabilityProvider(
        name="project",
        kind="project",
        observe_fn=_observe,
        description=(
            "Project/Repo reachability & health observation (read-only)"),
    )


# ---------------------------------------------------------------------------
# Provider recovery — observation instance (probe provider health read-only)
# ---------------------------------------------------------------------------

def provider_recovery_provider(
    executor: Any = None,
    probe_map: Optional[Dict[str, Callable[[], bool]]] = None,
) -> Optional[CapabilityProvider]:
    """Wrap real provider recovery jadi provider observasi instance.

    `executor` = ProviderExecutor (canonical). `probe_map` = {provider_id:
    ping_fn} untuk probe health read-only. Observasi = probe semua provider
    (tanpa recover/eksekusi).
    """
    try:
        from sam.delegated_authority.real_provider_recovery import (
            ProviderHealthProbe,
        )
        from sam.execution_runtime.provider_activation import ProviderExecutor  # noqa: F401
    except Exception:  # noqa: BLE001 - optional
        return None

    def _observe() -> List[Evidence]:
        if executor is None or not probe_map:
            return [_ev(
                "provider", "provider_unavailable",
                "no executor/probe_map supplied - nil impact", strength=0.0)]
        probe = ProviderHealthProbe(executor)
        result = []
        for pid, ping_fn in probe_map.items():
            try:
                p = probe.probe(pid, ping_fn=ping_fn)
                result.append(_ev(
                    "provider", "provider_probed",
                    f"{pid} available={p.available} healthy={p.healthy}",
                    strength=0.8 if p.available and p.healthy else 0.3))
            except Exception:  # noqa: BLE001 - satu gagal jangan jatuhkan
                result.append(_ev(
                    "provider", "provider_probe_failed", f"{pid} probe error",
                    strength=0.0))
        return result

    return CapabilityProvider(
        name="provider",
        kind="service",
        observe_fn=_observe,
        description=(
            "AI provider health/failover observation (read-only probe)"),
    )


# ---------------------------------------------------------------------------
# Registrasi mudah
# ---------------------------------------------------------------------------

def register_default_instances(
    registry: ProviderRegistry,
    *,
    include: Optional[List[str]] = None,
    **kwargs: Any,
) -> List[str]:
    """Daftarkan instance provider terpilih ke registry.

    `include` = nama provider yg mau didaftarkan (mis. ["word","pdf"]).
    Default None = semuanya yang bisa dibuat. Mengembalikan nama terdaftar.
    Argumen kwargs dilewatkan ke factory (mis. workspace=... utk openclaw).
    """
    factories: Dict[str, Callable] = {
        "word": word_provider,
        "pdf": pdf_provider,
        "openclaw": lambda: openclaw_provider(workspace=kwargs.get("workspace", "")),
        "project": lambda: project_guardian_provider(**{
            k: kwargs.get(k) for k in ("kind", "owner", "repo", "path")
            if kwargs.get(k) is not None}),
        "provider": lambda: provider_recovery_provider(
            executor=kwargs.get("executor"),
            probe_map=kwargs.get("probe_map")),
    }
    names = include or list(factories)
    registered = []
    for name in names:
        factory = factories.get(name)
        if not factory:
            continue
        try:
            provider = factory()
        except Exception:  # noqa: BLE001 - satu gagal jangan jatuhkan semua
            provider = None
        if provider is not None:
            registry.register(provider)
            registered.append(provider.name)
    return registered
