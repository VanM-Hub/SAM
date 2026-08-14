"""M14-010 Real Windows PC Ward — observe + diagnose Word/PDF.

Target real Van: "Real Windows PC -> observe + diagnose Word/PDF."

Design (read-only observation -> diagnosis -> recovery delegated):
  - observe:  kumpulkan health PC (disk free, file sistem) + temukan file
              Word (.docx) / PDF (.pdf) pada direktori target.
  - diagnose: periksa integritas file Word/PDF secara read-only (header/signature,
              ukuran tak nol, ekstensi valid). TIDAK membaca isi dokumen -
              hanya METADATA + integrity signature (jauh dari data sensitif).
  - recover:  AutonomousRecoveryLoop; execute_fn DIINJEKSIKAN (repair action).
              Jujur: bila bukan masalah yang bisa diperbaiki SAM -> escalate.

Boundary data: SAM tidak mengekspos isi dokumen; diagnosis hanya metadata
(nama, ukuran, ekstensi, signature header, error). Ini melindungi privasi.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.recovery import (
    AutonomousRecoveryLoop, RecoveryOutcome,
)

# Signature header (magic bytes) untuk deteksi integritas file (read-only).
_DOCX_MAGIC = b"PK"                       # ZIP-based (docx/xlsx/pptx)
_PDF_MAGIC = b"%PDF-"
_SUPPORTED = {".docx": _DOCX_MAGIC, ".pdf": _PDF_MAGIC}


@dataclass(frozen=True)
class FileProbe:
    """Probe satu file (metadata + integrity, TANPA isi)."""

    path: str
    name: str
    ext: str
    size_bytes: int
    valid_signature: bool
    error: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path, "name": self.name, "ext": self.ext,
            "size_bytes": self.size_bytes,
            "valid_signature": self.valid_signature, "error": self.error,
        }


@dataclass(frozen=True)
class PCDiagnosis:
    """Hasil diagnosis PC (disk + file Office/PDF)."""

    disk_free_bytes: int
    disk_total_bytes: int
    target_dir: str
    files: tuple = ()
    issues: tuple = ()

    @property
    def healthy(self) -> bool:
        return not self.issues

    def as_dict(self) -> Dict[str, Any]:
        return {
            "disk_free_bytes": self.disk_free_bytes,
            "disk_total_bytes": self.disk_total_bytes,
            "target_dir": self.target_dir,
            "files": [f.as_dict() for f in self.files],
            "issues": list(self.issues),
        }


@dataclass
class PCWardResult:
    """Hasil siklus PC Ward (auditable)."""

    diagnosis: Optional[PCDiagnosis] = None
    repaired: bool = False
    outcome: Optional[RecoveryOutcome] = None
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "diagnosis": self.diagnosis.as_dict() if self.diagnosis else None,
            "repaired": self.repaired, "reason": self.reason,
            "outcome": self.outcome.as_dict() if self.outcome else None,
        }


class WindowsPCWard:
    """Ward PC Windows: observe + diagnose (Word/PDF) + recover delegated."""

    def __init__(
        self,
        target_dir: str = ".",
        loop: Optional[AutonomousRecoveryLoop] = None,
        allow_pdf_repair_hint: bool = True,
    ) -> None:
        self.target_dir = target_dir
        self._loop = loop or AutonomousRecoveryLoop()

    # --- observe ---

    def probe_file(self, path: str) -> FileProbe:
        """Probe satu file: metadata + signature header (read-only, tanpa isi)."""
        try:
            size = os.path.getsize(path)
            ext = os.path.splitext(path)[1].lower()
            if size == 0:
                return FileProbe(path, os.path.basename(path), ext, 0, False,
                                 "empty file")
            if ext not in _SUPPORTED:
                return FileProbe(path, os.path.basename(path), ext, size,
                                 True, "unsupported ext (skipped)")
            with open(path, "rb") as f:
                head = f.read(8)
            valid = ext == ".pdf" and head.startswith(_PDF_MAGIC) \
                or ext in (".docx",) and head.startswith(_DOCX_MAGIC)
            return FileProbe(path, os.path.basename(path), ext, size, valid,
                             "" if valid else "signature mismatch (possibly corrupt)")
        except OSError as e:
            return FileProbe(path, os.path.basename(path), "", 0, False, str(e))

    def observe(self) -> PCDiagnosis:
        """Kumpulkan disk free + file Word/PDF pada target_dir."""
        disk_free = disk_total = 0
        try:
            usage = shutil.disk_usage(self.target_dir)
            disk_total, disk_free = usage.total, usage.free
        except OSError:
            pass

        probes: List[FileProbe] = []
        if os.path.isdir(self.target_dir):
            for name in sorted(os.listdir(self.target_dir)):
                if not name.lower().endswith((".docx", ".pdf")):
                    continue
                full = os.path.join(self.target_dir, name)
                if os.path.isfile(full):
                    probes.append(self.probe_file(full))

        issues = []
        if disk_total > 0 and disk_free < disk_total * 0.05:
            issues.append("low disk space (<5% free)")
        for p in probes:
            if not p.valid_signature and p.ext in _SUPPORTED:
                issues.append(f"{p.name}: {p.error}")

        return PCDiagnosis(
            disk_free_bytes=disk_free, disk_total_bytes=disk_total,
            target_dir=self.target_dir, files=tuple(probes),
            issues=tuple(issues),
        )

    # --- recover ---

    async def recover(
        self,
        *,
        grant: Optional[DelegationGrant] = None,
        risk: float = 0.3,
        risk_label: str = "low",
        execute_fn: Optional[Callable] = None,
        verify_fn: Optional[Callable] = None,
        rollback_fn: Optional[Callable] = None,
        learn_fn: Optional[Callable] = None,
    ) -> PCWardResult:
        """Jalankan recovery utk PC bila diagnosis menemukan issue."""
        diagnosis = self.observe()

        if diagnosis.healthy:
            return PCWardResult(
                diagnosis=diagnosis, repaired=False,
                reason="PC healthy - no issue found",
            )

        grant = grant or DelegationGrant(
            ward_id="pc", owner_id="owner", autonomy_level=AutonomyLevel.OBSERVE,
            requires_human_approval=True,
        )

        from sam.execution_runtime.execution_request import ExecutionRequest
        request = ExecutionRequest(
            execution_id="exec-pc-ward", provider_id="pc", operation="recover",
            mode="execute", approved=False,
            payload={"ward_id": "pc", "target_dir": self.target_dir},
            timeout_seconds=30,
        )

        outcome = await self._loop.run(
            request=request, grant=grant, capability="protect",
            risk=risk, risk_label=risk_label,
            evidence_refs=(f"disk_free:{diagnosis.disk_free_bytes}",),
            plan={"diagnosis": diagnosis.as_dict()},
            observe_fn=lambda: {
                "disk_free_bytes": diagnosis.disk_free_bytes,
                "issues": list(diagnosis.issues),
            },
            investigate_fn=lambda: {
                "files": [f.as_dict() for f in diagnosis.files],
            },
            diagnose_fn=lambda: {"issues": list(diagnosis.issues)},
            execute_fn=execute_fn,
            verify_fn=verify_fn,
            rollback_fn=rollback_fn,
            learn_fn=learn_fn,
        )

        return PCWardResult(
            diagnosis=diagnosis, repaired=outcome.ok,
            outcome=outcome, reason=outcome.reason,
        )
