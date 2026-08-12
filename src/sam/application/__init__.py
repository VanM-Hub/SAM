"""Application Layer — SAM.

Lapisan aplikasi (use case boundary). Berisi orchestration use case yang
memanggil boundary domain/runtime yang sudah ada (canonical). TIDAK berisi
implementation domain, TIDAK punya authority, TIDAK membuat executor kedua.

M9 — Productization: application/ux = product entry point (M9-001) yang
menjadi satu-satunya pintu manusia memakai kemampuan nyata SAM melalui UI.
"""
