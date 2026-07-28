# OP-201 — Desktop Architecture Blueprint

## 1. Prinsip: Host Agnostic Architecture

**Desktop hanyalah satu dari banyak host.** Setiap host (Console, Desktop, Web, CLI) adalah konsumen yang **setara** dari Conversation API + DTO + RendererProtocol.

```
                         ┌──────────────┐
                         │   Domain     │
                         │  (SAM Core)  │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │ Conversation │
                         │     API      │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │     DTO     │
                         └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
             ┌──────▼──┐ ┌─────▼────┐ ┌────▼────┐
             │ Console │ │ Desktop  │ │   Web   │
             │  Host   │ │   Host   │ │   Host  │
             └─────────┘ └──────────┘ └─────────┘
```

### Aturan Mutlak

1. **Desktop tidak boleh mengakses domain langsung.** Tidak ada `import sam.operations.mission`, `import sam.storage`, `import sam.telemetry`, dll.
2. **Desktop tidak boleh memanggil Conversation API langsung.** Semua data via DTO.
3. **Desktop tidak boleh memiliki business logic.** Desktop adalah view — tidak ada validasi, tidak ada decision, tidak ada routing.
4. **Desktop hanya mengonsumsi DTO** yang sudah ada — tidak membuat DTO baru.
5. **Desktop menggunakan RendererProtocol yang sudah ada** — tidak membuat renderer baru.
6. **Console tetap bisa berjalan tanpa Desktop.** Desktop adalah host alternatif, bukan pengganti.

---

## 2. Pipeline Desktop

```
Conversation API
        │
        ▼
DTO (dashboard_model, action_center, notification, summary_builder, ...)
        │
        ▼
DashboardComposer.compose()
        │
        ▼
ConsoleDashboard
        │
        ▼
ConsoleSession (Presentation orchestrator — Sprint 13)
        │
        ▼
RendererProtocol (render_dashboard, render_widget, render_notification, ...)
        │
        ▼
DesktopRendererAdapter ────► Qt Widgets
        │
        ▼
DesktopApplication (lifecycle, window, layout, navigation, theme, session)
```

### Alur Berlapis

| Layer | File | Tanggung Jawab |
|---|---|---|
| **Lifecycle** | `application.py` | Desktop lifecycle (INIT→READY→RUNNING→STOPPING→STOPPED) |
| **Session** | `session.py` | Menghubungkan ConsoleSession ke Desktop runtime |
| **Window** | `main_window.py` | Model window (menu, toolbar, navigation, content, statusbar, notification) |
| **Layout** | `layout.py` | Model layout (left nav, center, bottom log, right panel, status bar) |
| **Navigation** | `navigation.py` | Menggunakan Screen model Sprint 12 (Dashboard, Mission, dll.) |
| **Theme** | `theme.py` | Menggunakan ThemeRuntime Sprint 12/13 |
| **Adapter** | `renderer_adapter.py` | Bridge RendererProtocol → Qt widgets (belum implementasi widget) |

---

## 3. Desktop Lifecycle

```
INITIALIZING
     │
     ▼
    READY ◄────┐
     │          │
     ▼          │
   RUNNING ─────┤ (restart)
     │          │
     ▼          │
  STOPPING     │
     │          │
     ▼          │
   STOPPED ────┘
```

State transitions identik dengan ConsoleApp (Sprint 14, OP-181). Desktop adalah **consumer** yang sama, bukan duplikasi.

### Startup Sequence

1. DesktopApplication.startup() → READY
2. Inisialisasi ConsoleSession
3. Inisialisasi ThemeRuntime (dari Sprint 12/13)
4. Inisialisasi DesktopNavigation (menggunakan Screen model Sprint 12)
5. READY → RUNNING

### Shutdown Sequence

1. RUNNING → STOPPING
2. ConsoleSession.stop()
3. Shutdown resources
4. STOPPED

---

## 4. Model Window

```
┌─────────────────────────────────────────────────────┐
│ Menu Bar                                             │
├─────────────────────────────────────────────────────┤
│ Tool Bar                                             │
├──────────┬────────────────────────┬──────────────────┤
│          │                        │                  │
│ Nav      │    Content Area        │  Right Panel     │
│ Panel    │    (Dashboard,         │  (Detail,        │
│          │     Missions,          │   Properties,    │
│ Dashboard │     Timeline,         │   Preview)       │
│ Missions  │     Approvals,        │                  │
│ Timeline  │     Settings,         │                  │
│ Approvals │     Help, ...)        │                  │
│ Trust     │                        │                  │
│ Settings  │                        │                  │
│          │                        │                  │
├──────────┴────────────────────────┴──────────────────┤
│ Log Panel (collapsible, bottom)                       │
├─────────────────────────────────────────────────────┤
│ Status Bar                                            │
└─────────────────────────────────────────────────────┘
```

### Layout Regions

| Region | Posisi | Konten |
|---|---|---|
| **Navigation Panel** | Left | Screen list dengan icon + label |
| **Content Area** | Center | Screen utama (dashboard, missions, timeline, dll.) |
| **Right Panel** | Right | Detail panel untuk item terpilih (collapsible) |
| **Log Panel** | Bottom | Log viewer (collapsible, resizable) |
| **Status Bar** | Bottom | StatusBar dari Sprint 15 (OP-196) |

Semua region adalah **model data** — belum ada implementasi Qt widget.

---

## 5. Navigation

Menggunakan **screen identifiers yang sudah ada** dari Sprint 12 (`navigation.py`):

| Screen | ID | Shortcut |
|---|---|---|
| Dashboard | `dashboard` | 1 |
| Missions | `missions` | 2 |
| Timeline | `timeline` | 3 |
| Approvals | `approvals` | 4 |
| Trust | `trust` | 5 |
| History | `history` | 6 |
| Settings | `settings` | 7 |
| Help | `help` | 8 |

Navigation adalah **wrapper tipis** di atas `NavigationRuntime` Sprint 13. Tidak ada duplikasi.

---

## 6. Theme

Menggunakan `ThemeRuntime` dari Sprint 12/13 secara **langsung**.

```
ThemeRuntime (Sprint 12/13)
     │
     ▼
DesktopThemeAdapter
     │
     ├── color scheme → Qt palette
     ├── font tokens → Qt font
     ├── spacing tokens → Qt layout
     └── style hints → Qt stylesheet
```

Desktop tidak menyimpan atau mendefinisikan theme independen. Semua warna dan token berasal dari `ThemeRuntime`.

---

## 7. Renderer Adapter

```
RendererProtocol (Sprint 12)
     │
     ▼
DesktopRendererAdapter (Sprint 16)
     │
     ├── render_dashboard() → QWidget content
     ├── render_widget() → QWidget snippet
     ├── render_notification() → System tray / QNotification
     ├── render_summary() → Status bar text
     └── render_timeline() → QListWidget / QTreeWidget
```

Adapter adalah **bridge** yang mengimplementasikan `RendererProtocol` dan menerjemahkan panggilan render ke Qt widget actions. **Belum ada implementasi widget** di Sprint 16 — hanya definisi adapter.

---

## 8. Host Independence

**Console tetap bisa berjalan tanpa Desktop.** Keduanya adalah host alternatif:

```
# Console mode
python run.py --console

# Desktop mode (future)
python run.py --desktop
```

Keduanya mengonsumsi pipeline yang sama:

```
Conversation API → DTO → DashboardComposer → ConsoleDashboard → ConsoleSession → RendererProtocol
```

---

## 9. Dependency Map

```
desktop/
  application.py     → ConsoleApp (Sprint 14) — pola lifecycle yang sama
  session.py         → ConsoleSession (Sprint 13) — orkestrasi presentasi
  main_window.py     → model murni (frozen dataclass)
  layout.py          → model murni (frozen dataclass)
  navigation.py      → navigation.py (Sprint 12) + NavigationRuntime (Sprint 13)
  theme.py           → ThemeRuntime (Sprint 13) — adaptasi warna/token
  renderer_adapter.py→ RendererProtocol (Sprint 12) — bridge interface
```

Tidak ada dependency silang antar file desktop. Setiap file hanya bergantung pada **satu** layer di bawah (presentation layer Sprint 12/13/14/15).

---

## 10. Constraints Summary

| Constraint | Pemenuhan |
|---|---|
| ✅ Tidak mengubah Domain | Desktop tidak import domain |
| ✅ Tidak mengubah Conversation API | Desktop tidak panggil Conversation API |
| ✅ Tidak mengubah Repository | Desktop tidak import storage |
| ✅ Tidak mengubah Console Runtime | Desktop hanya konsumen |
| ✅ Desktop hanya shell | Desktop = view, tidak ada business logic |
| ✅ Python 3.8+ | `from __future__ import annotations` |
| ✅ Console tetap jalan tanpa Desktop | Host independen |
| ✅ Pipeline tetap | Conversation API → DTO → Composer → Session → Renderer |
| ✅ tidak ada renderer baru | Renderer sudah ada, adapter belum implementasi widget |
| ✅ 681 tests tetap hijau | Tidak ada perubahan pada domain/operations |
