# FAQ — Pertanyaan Umum

> Pertanyaan yang sering diajukan tentang SAM Framework.

## Instalasi

### Apa prasyarat untuk menjalankan SAM?
Python 3.8+, pip, dan git. Lihat [panduan instalasi](installation.md) untuk detail.

### SAM bisa jalan di Windows?
Ya. SAM sudah diuji di Windows 10/11, Linux, dan macOS.

### Apakah SAM butuh database?
SAM menggunakan SQLite secara default (built-in, tidak perlu instalasi terpisah). Untuk production, PostgreSQL bisa ditambahkan di versi mendatang.

## Penggunaan

### Bagaimana cara menjalankan SAM?
SAM adalah framework, bukan service yang berjalan terus. Jalankan perintah CLI sesuai kebutuhan:

```bash
sam health
sam run diagnose-runtime
```

### Apakah SAM auto-healing?
SAM menyediakan pipeline healing (observe → diagnose → plan → execute → verify → learn), tetapi eksekusi tergantung level autonomy yang dipilih.

### Apa perbedaan level autonomy?

| Level | Deskripsi |
|---|---|
| Observe | Hanya amati, lapor |
| Recommend | Rekomendasikan tindakan |
| Assist | Jalankan dengan persetujuan |
| Supervise | Jalankan dengan supervisi |
| Autonomous | Jalankan sendiri |

## Troubleshooting

### `ModuleNotFoundError: No module named 'sam'`
Jalankan `pip install -e .` dari direktori SAM.

### Database error saat pertama kali
Hapus `sam.db` dan jalankan ulang. Database akan dibuat ulang secara otomatis.

### CLI error "sam: command not found"
Gunakan `python -m sam.cli.main` sebagai alternatif, atau instal SAM dengan `pip install -e .` yang benar.

### Test gagal dengan error migration
Pastikan database bersih: hapus `sam.db` lalu jalankan test lagi.

## Development

### Bagaimana cara membuat capability baru?
Ikuti [Capability Guide](capability_guide.md). Buat class yang mewarisi `BaseCapability`, daftarkan di plugin manifest.

### Bagaimana cara berkontribusi?
Lihat [CONTRIBUTING.md](../../CONTRIBUTING.md). Kami menerima pull request, issue, dan saran.

### Apakah SAM open source?
Ya. MIT License. Repository di [GitHub](https://github.com/VanM-Hub/SAM).

## Umum

### SAM itu singkatan dari apa?
System Administration Manager — framework untuk operasi sistem yang dapat berevolusi secara mandiri.

### Apakah SAM bisa diintegrasikan dengan tools lain?
Ya. Melalui plugin system, capability custom, dan knowledge federation.

### SAM versi berapa sekarang?
v1.0.0 (stable). RC3 sedang dalam tahap validasi.
