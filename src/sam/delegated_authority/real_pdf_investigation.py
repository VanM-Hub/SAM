"""M14-012 PDF Performance Investigation — analisis performa file PDF.

Menilai kesehatan & PERFORMANCE PDF secara read-only (metrik, bukan isi):
  - integritas header (%PDF-)
  - ukuran file
  - jumlah objek & stream (indikator kompleksitas render)
  - kompresi: ada Filter FlateDecode? (PDF terkompresi lebih ringan)
  - estimasi "render cost" (heuristic on structure)
TIDAK mendekode isi dokumen / teks - hanya struktur biner + metrik.

Verdict performa: healthy / large / heavy - deterministic, auditable.
Konsisten M13 separation: ini investigation (read), bukan mutation.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sam.delegated_authority.authority import DelegationGrant


@dataclass(frozen=True)
class PDFPerformanceInvestigation:
    """Hasil investigasi performa PDF (read-only, auditable)."""

    path: str
    ok: bool
    size_bytes: int = 0
    is_valid: bool = False
    obj_count: int = 0
    stream_count: int = 0
    flate_compressed: bool = False
    page_references: int = 0            # jumlah referensi /Type /Page (heuristik)
    performance_level: str = "unknown"  # healthy | large | heavy
    findings: tuple = ()
    error: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path, "ok": self.ok, "size_bytes": self.size_bytes,
            "is_valid": self.is_valid, "obj_count": self.obj_count,
            "stream_count": self.stream_count,
            "flate_compressed": self.flate_compressed,
            "page_references": self.page_references,
            "performance_level": self.performance_level,
            "findings": list(self.findings), "error": self.error,
        }


class PDFPerformanceInvestigator:
    """Menginvestigasi performa PDF (read-only, tanpa decode isi)."""

    _OBJ_RE = re.compile(rb"\b5?[0-9]{1,6}\s+[0-9]+\s+obj\b")
    _STREAM_RE = re.compile(rb"stream\r?\n|<<\s*/Length")
    _FLATE_RE = re.compile(rb"/FlateDecode")
    _PAGE_RE = re.compile(rb"/Type\s*/Page\b")

    def investigate(
        self, path: str, *, grant: Optional[DelegationGrant] = None
    ) -> PDFPerformanceInvestigation:
        """Investigasi performa satu PDF.

        `grant` diterima utk konsistensi policy; investigate adalah read
        capability (tidak mutation) sehingga boleh berjalan tanpa authority
        eksekusi (M13 separation).
        """
        if not os.path.exists(path):
            return PDFPerformanceInvestigation(path=path, ok=False,
                                               error="file not found")

        size = os.path.getsize(path)
        try:
            with open(path, "rb") as f:
                head = f.read(1024)
                # baca sampai beberapa KB pertama + tail utk hitung objek
                f.seek(0)
                head_block = f.read(min(size, 256 * 1024))
                is_valid = head.startswith(b"%PDF-")
        except OSError as e:
            return PDFPerformanceInvestigation(path=path, ok=False,
                                               error=f"read error: {e}")

        if not is_valid:
            return PDFPerformanceInvestigation(
                path=path, ok=True, size_bytes=size, is_valid=False,
                findings=("not a valid PDF (missing %PDF- header)",),
                performance_level="unknown",
            )

        obj_count = len(self._OBJ_RE.findall(head_block))
        stream_count = len(self._STREAM_RE.findall(head_block))
        flate = bool(self._FLATE_RE.search(head_block))
        page_refs = len(self._PAGE_RE.findall(head_block))

        findings: List[str] = []
        # performance verdict (deterministic heuristic)
        if size > 20 * 1024 * 1024:
            level = "heavy"
            findings.append("PDF >20MB - heavy (slow open/render)")
        elif size > 5 * 1024 * 1024:
            level = "large"
            findings.append("PDF >5MB - large, consider compression")
        else:
            level = "healthy"
        if not flate and stream_count > 50:
            findings.append("many uncompressed streams - file may be bloated")
        if page_refs > 100:
            findings.append("high page count - expect slower render")

        return PDFPerformanceInvestigation(
            path=path, ok=True, size_bytes=size, is_valid=True,
            obj_count=obj_count, stream_count=stream_count,
            flate_compressed=flate, page_references=page_refs,
            performance_level=level, findings=tuple(findings),
        )
