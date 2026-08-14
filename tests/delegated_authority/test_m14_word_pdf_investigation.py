"""M14-011/012 tests — Word Investigation + PDF Performance Investigation.

Membuat .docx (zip berisi document.xml + docProps) dan .pdf (dgn objek/stream)
utk membuktikan investigasi struktur read-only; TANPA mengekspos isi teks.
"""
import sys
import os
import io
import zipfile
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


from sam.delegated_authority.real_word_investigation import WordInvestigator
from sam.delegated_authority.real_pdf_investigation import PDFPerformanceInvestigator


def _make_docx(path, with_doc=False):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<?xml version='1.0'?>")
        z.writestr(
            "docProps/core.xml",
            "<?xml version='1.0'?><cp:coreProperties>"
            "<dc:title>Laporan Test</dc:title><dc:creator>Van</dc:creator>"
            "</cp:coreProperties>",
        )
        body = "<w:body>"
        if with_doc:
            for _ in range(5):
                body += "<w:p><w:r><w:t>x</w:t></w:r></w:p>"
            body += "<w:tbl><w:tr><w:tc><w:p/></w:tc></w:tr></w:tbl>"
            body += "<w:p/><w:p/>"
        body += "</w:body>"
        z.writestr("word/document.xml", "<w:document>" + body + "</w:document>")
    with open(path, "wb") as f:
        f.write(buf.getvalue())


def _make_pdf(path, big=False, many_streams=False):
    with open(path, "wb") as f:
        f.write(b"%PDF-1.7\n")
        for i in range(40):
            f.write(f"{i} 0 obj\n".encode())
            f.write(b"<< /Type /Page >>\nendobj\n")
            if many_streams or i % 2 == 0:
                f.write(f"{i+100} 0 obj\n".encode())
                f.write(b"<< /Length 10 >>\nstream\nabcdefg\nendstream\nendobj\n")
    # tambah padding utk ukuran kalau big
    if big:
        with open(path, "ab") as f:
            f.write(b"0" * (6 * 1024 * 1024))
        # pastikan ukuran > 5MB tapi valid header tetap di awal
    return path


class TestWordInvestigation:
    def test_investigate_valid_docx(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "laporan.docx")
        _make_docx(p, with_doc=True)
        res = WordInvestigator().investigate(p)
        assert res.ok is True
        assert res.is_valid is True
        assert res.title == "Laporan Test"
        assert res.creator == "Van"
        assert res.paragraph_count >= 5
        assert res.table_count >= 1

    def test_investigate_missing_file(self):
        res = WordInvestigator().investigate("NONEXISTENT.docx")
        assert res.ok is False
        assert "not found" in res.error

    def test_investigate_invalid_zip(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "bad.docx")
        with open(p, "wb") as f:
            f.write(b"not a zip file at all")
        res = WordInvestigator().investigate(p)
        assert res.ok is False
        assert res.is_valid is False
        assert res.error

    def test_no_paragraph_text_exposed(self):
        # investigasi TIDAK mengembalikan isi teks (hanya counts)
        d = tempfile.mkdtemp()
        p = os.path.join(d, "d.docx")
        _make_docx(p, with_doc=True)
        res = WordInvestigator().investigate(p)
        dumped = str(res.as_dict())
        assert "<w:t>" not in dumped      # struktur tidak bocor isi
        assert "paragraph_count" in dumped


class TestPDFPerformanceInvestigation:
    def test_valid_pdf(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "doc.pdf")
        _make_pdf(p)
        res = PDFPerformanceInvestigator().investigate(p)
        assert res.ok is True
        assert res.is_valid is True
        assert res.obj_count > 0
        assert res.performance_level in ("healthy", "large", "heavy")

    def test_invalid_pdf_header(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "bad.pdf")
        with open(p, "wb") as f:
            f.write(b"GARBAGE content not pdf")
        res = PDFPerformanceInvestigator().investigate(p)
        assert res.is_valid is False

    def test_large_pdf_performance_heuristic(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "big.pdf")
        _make_pdf(p, big=True)
        res = PDFPerformanceInvestigator().investigate(p)
        assert res.size_bytes >= 5 * 1024 * 1024
        assert res.performance_level in ("large", "heavy")
        assert res.findings               # ada finding performa
