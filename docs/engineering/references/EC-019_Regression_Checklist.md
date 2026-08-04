# EC-019 — Regression Checklist

## Sebelum Commit

- Build berhasil.
- Test lulus.
- Tidak ada circular dependency baru.
- Tidak ada public API rusak.
- Tidak ada Constitution dilanggar.

## Setelah Commit

- CLI entry tersedia dan fungsi inti berjalan.
- Web entry tersedia dan fungsi inti berjalan.
- REST entry tersedia dan fungsi inti berjalan.
- Desktop host tetap hidup.
- Runtime Status benar.
- Regression hijau.

Catatan: console / api_server / headless host diketahui Not Fully Operational (bukan regresi baru). Jangan memperburuk, tetapi jangan juga menganggapnya Operational.

## Setelah Merge

Pastikan:

- consumer bertambah ATAU
- technical debt berkurang.

Jika tidak, evaluasi ulang perubahan.

## Jangan Merge

Jika hanya menambah abstraksi tanpa manfaat operasional.

## Referensi

MISSION
SPECIFICATION_FREEZE
