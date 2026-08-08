# EA-001-005 — Template & Sample Assessment

**Mission:** MISSION-2E — Program E (Early Adopter Experience)
**Package:** AP-2E-001
**Workstream:** WP-E5 — Template & Sample Experience
**Bersifat:** Assessment (read-only, berbasis evidence)

---

## Ruang Lingkup

Menilai pengalaman template & sample untuk early adopter: starter project, example Mission, example Workflow, example Runtime, template repository.

---

## Inventory Evidence

### 1. Direktori contoh

- `examples/` — direktori contoh top-level.
- `examples/plugins/sample-plugin` — contoh plugin nyata.

### 2. Template

- `docs/templates/` — template dokumentasi (format laporan/ADR/dokumen).
- `docs/engineering/templates/` — template engineering (Format_Laporan_Engineer, dsb.).
- `src/sam/web/templates/` — template web/UI (render).
- `src/sam/operations/reasoning/templates.py` & `src/sam/reasoning/templates.py` — template reasoning (internal).

### 3. Starter / scaffold

- Belum ditemukan skrip `starter`/`scaffold`/`init` yang menghasilkan project SAM baru.
- Tidak ada `cookiecutter` template repository.

### 4. Example Mission / Workflow / Runtime

- Mission/workflow dirancang sebagai runtime (`mission_runtime`, `workflow_runtime`), tetapi **belum ada contoh proyek sampel end-to-end** (starter yang berisi Mission + Workflow + Runtime) di `examples/`.

---

## Temuan Gap (Initial Assessment)

| ID | Severity | Temuan | Keterangan |
|---|---|---|---|
| E5-G1 | **High** | Tidak ada **starter project / template repository** untuk project SAM baru | Ada `examples/plugins/sample-plugin`, tetapi tidak ada scaffold yang menghasilkan struktur project lengkap (Mission + Workflow + Runtime) |
| E5-G2 | Medium | Tidak ada **example Mission / Workflow / Runtime** end-to-end | Contoh terbatas pada plugin; belum ada contoh pemakaian public API (observe()/Conversation) |
| E5-G3 | Low | Tidak ada cookiecutter/cli init scaffold | Otomasi pembuatan project baru tidak tersedia di CLI (terkait E2-G1 `sam init`) |

---

## Kesimpulan

Contoh plugin tersedia, tetapi **template/starter untuk project SAM baru belum ada** — early adopter tidak punya titik awal untuk membuat Mission/Workflow/Runtime mereka sendiri selain membaca dokumentasi. Ini gap terbesar di area template & sample.
