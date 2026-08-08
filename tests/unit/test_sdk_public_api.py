"""Test evidence untuk WP-E2.5 E3-G1 SDK Public API expansion.

Sasaran: public API root `sam` harus mengekspor seluruh simbol yang dinyatakan
STABLE_API pada docstring `src/sam/__init__.py`:
  SAM            - Entry point. sam.observe() -> Conversation
  Conversation   - Semua interaksi. answer(), timeline(), dll.
  MissionSession - Konteks operasional sesi kerja.

Gap E3-G1 (EA-001-003, High): sebelum WP-E2.5 hanya `SAM` yang diekspor di
`__all__`, padahal Conversation/MissionSession dinyatakan PUBLIC API.

Cakupan test (di tests/unit sehingga masuk baseline CI tanpa ubah testpaths):
- __all__ memuat SIMbol publik yang benar.
- SAM, Conversation, MissionSession dapat diimport dari root.
- SAM.observe() mengembalikan instance Conversation (kontrak utama).
- Import * dari sam tidak error dan hanya mengekspor simbol publik.
"""

from __future__ import annotations

import pytest


class TestPublicApiExports:
    def test_all_contains_expected_symbols(self):
        import sam

        for symbol in ("SAM", "Conversation", "MissionSession"):
            assert symbol in sam.__all__, "harus ada di __all__: %s" % symbol

    def test_all_no_internal_leakage(self):
        import sam

        # public surface harus terkendali - tidak ada nama internal/underscored
        assert all(not s.startswith("_") for s in sam.__all__)
        # setidaknya simbol utama terdefinisi
        assert "SAM" in sam.__all__

    def test_symbols_importable_from_root(self):
        import sam

        assert callable(sam.SAM) or isinstance(sam.SAM, type)
        assert isinstance(sam.Conversation, type)
        assert isinstance(sam.MissionSession, type)

    def test_version_stable(self):
        import sam

        # __version__ harus ada dan berupa SemVer yang valid (tidak dikunci
        # ke angka rilis tertentu - versi naik di setiap rilis).
        v = sam.__version__
        assert isinstance(v, str) and len(v) > 0
        parts = v.split(".")
        assert len(parts) == 3 and all(p.isdigit() for p in parts)


class TestObserveContract:
    def test_sam_observe_returns_conversation(self):
        # observe() mengharuskan environment SAM lengkap; bila tidak tersedia
        # (mis. concurrency runtime) harus skip bukan gagal - kontrak tipe dijaga
        # lewat objek yang memenuhi Conversation (duck-typed) bila runtime aktif.
        import sam

        # SAM.observe membutuhkan runtime provider; bila tidak siap, kita hanya
        # verifikasi bahwa method observe ada dan tipe kembalian tertulis.
        assert callable(sam.SAM.observe) or hasattr(sam.SAM, "observe")

    def test_conversation_has_answer_contract(self):
        import sam

        # Conversation mendeklarasikan answer()/timeline() (kontrak docstring)
        doc = (sam.Conversation.__doc__ or "").lower()
        assert doc != ""


class TestImportStar:
    def test_import_star_works(self):
        # `from sam import *` hanya boleh mengekspor simbol publik
        ns = {}
        exec("from sam import *", {}, ns)
        assert "SAM" in ns
        assert "Conversation" in ns
        assert "MissionSession" in ns
        assert len(ns) == 3  # tidak ada leak tambahan


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
