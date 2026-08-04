# EC-023 — Engineering Anti-Patterns

Hindari:

- Runtime baru.
- Manager baru.
- Coordinator baru.
- Service Locator baru.
- Composition Root kedua.
- Approval kedua.
- Execution Pipeline kedua.
- Runtime Registry kedua.
- Business Logic di Presentation.
- Provider dipanggil langsung dari Presentation.
- Wiring langsung ke RuntimeCoordinator untuk activation baru.
- Framework tanpa consumer.
- Refactor kosmetik.
- Abstraction tanpa manfaat operasional.
- Dokumentasi tanpa implementasi.
- Menyatakan host Not Fully Operational sebagai "Operational".
- Menganggap RuntimeCoordinator sebagai satu-satunya jalur.
- Menganggap dormant sebagai dead code.

Selalu tanyakan:

Apakah perubahan ini membuat SAM lebih operasional?
