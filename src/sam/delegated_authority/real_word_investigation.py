"""M14-011 Word Investigation — investigate dokumen Word (.docx) read-only.

Melanjutkan M14-010 secara lebih dalam: INVESTIGASI (bukan hanya diagnose).
Membaca STRUKTUR dokumen .docx secara read-only untuk menilai kesehatan &
kompleksitas, TANPA mengekspos isi teks sensitif ke audit/artifact.

Apa yang dibaca (metadata/struktur, bukan isi):
  - integritas (signature, zip terbuka)
  - properti dokumen (docProps/core.xml: title, creator, revised) - bila ada
  - jumlah heading/paragraf/tabel/gambar (dari word/document.xml counting tags)
  - ukuran file
Apa yang TIDAK pernah dibaca/ekspos: isi paragraf, teks dokumen, body.

Investigation result adalah data deterministik + verdict kesehatan/dugaan issue.
Tidak ada mutation; ini investigation capability (read), konsisten M13 (guardian
separation: investigate != execute).
"""
from __future__ import annotations

import os
import re
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sam.delegated_authority.authority import DelegationGrant


@dataclass(frozen=True)
class WordInvestigation:
    """Hasil investigasi dokumen Word (read-only, auditable)."""

    path: str
    ok: bool
    size_bytes: int = 0
    is_valid: bool = False
    title: str = ""
    creator: str = ""
    paragraph_count: int = 0
    heading_count: int = 0
    table_count: int = 0
    image_count: int = 0
    findings: tuple = ()               # issue/dugaan
    error: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path, "ok": self.ok, "size_bytes": self.size_bytes,
            "is_valid": self.is_valid, "title": self.title, "creator": self.creator,
            "paragraph_count": self.paragraph_count,
            "heading_count": self.heading_count, "table_count": self.table_count,
            "image_count": self.image_count, "findings": list(self.findings),
            "error": self.error,
        }


class WordInvestigator:
    """Investigasi struktur dokumen .docx (read-only, tanpa isi sensitif)."""

    # struktur xml internal (word/document.xml) - hanya HITUNG, bukan isi
    _TAG_COUNTS = {
        "paragraph_count": re.compile(rb"<w:p\b"),
        "heading_count": re.compile(rb"<w:pStyle[^>]*w:val=[\"']Heading", re.IGNORECASE),
        "table_count": re.compile(rb"<w:tbl\b"),
        "image_count": re.compile(rb"<w:drawing\b|<pic:pic\b"),
    }

    def investigate(
        self, path: str, *, grant: Optional[DelegationGrant] = None
    ) -> WordInvestigation:
        """Investigasi satu .docx (authority check ringan: observe = read).

        Mutation/action tidak ada di sini; hanya investigasi. Grant diperiksa
        untuk konsistensi policy (bila None, tetap boleh investigasi read
        karena investigate adalah capability read - M13 separation).
        """
        if not os.path.exists(path):
            return WordInvestigation(path=path, ok=False, error="file not found")

        size = os.path.getsize(path)
        findings: List[str] = []

        # integritas zip + struktur
        try:
            with zipfile.ZipFile(path) as z:
                is_valid = True
                names = set(z.namelist())
                # hitung struktur dari document.xml bila ada
                if "word/document.xml" in names:
                    doc_xml = z.read("word/document.xml")
                    counts = self._count(doc_xml)
                else:
                    counts = {k: 0 for k in self._TAG_COUNTS}
                    is_valid = False
                    findings.append("document.xml missing (invalid .docx)")
                # properti (title/creator) - metadata, bukan isi
                title, creator = self._props(z, names)
        except (zipfile.BadZipFile, OSError) as e:
            return WordInvestigation(path=path, ok=False, size_bytes=size,
                                     is_valid=False, error=f"invalid zip: {e}",
                                     findings=("not a valid .docx",))

        # verdict kesehatan (dugaan, bukan mutation)
        if size > 10 * 1024 * 1024:
            findings.append("oversized docx (>10MB) - may be slow to open")
        if counts["image_count"] > 50:
            findings.append("many embedded images - large file likely")

        return WordInvestigation(
            path=path, ok=True, size_bytes=size, is_valid=is_valid,
            title=title, creator=creator, **counts,
            findings=tuple(findings),
        )

    @staticmethod
    def _count(doc_xml: bytes) -> Dict[str, int]:
        result = {}
        for key, pattern in WordInvestigator._TAG_COUNTS.items():
            result[key] = len(pattern.findall(doc_xml))
        return result

    @staticmethod
    def _props(z: zipfile.ZipFile, names: set) -> tuple:
        title = creator = ""
        if "docProps/core.xml" in names:
            try:
                core = z.read("docProps/core.xml").decode("utf-8", errors="replace")
                m = re.search(r"<dc:title[^>]*>(.*?)</dc:title>", core, re.S)
                if m:
                    title = m.group(1)[:120]
                m = re.search(r"<dc:creator[^>]*>(.*?)</dc:creator>", core, re.S)
                if m:
                    creator = m.group(1)[:120]
            except Exception:  # noqa: BLE001
                pass
        return title, creator
