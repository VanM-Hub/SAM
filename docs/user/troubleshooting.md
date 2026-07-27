# Troubleshooting

> Panduan mengatasi masalah umum di SAM Framework.

## Masalah Instalasi

### `pip install -e .` gagal

**Gejala:** Error saat menjalankan `pip install -e .`

**Solusi:**
1. Pastikan Python 3.8+ sudah terinstal
2. Coba upgrade pip: `python -m pip install --upgrade pip`
3. Jika error `setuptools`, instal: `pip install setuptools>=68.0`
4. Coba instal tanpa cache: `pip install --no-cache-dir -e .`

### `ModuleNotFoundError: No module named 'sam'`

**Gejala:** Python tidak bisa mengimpor modul SAM

**Solusi:**
```bash
cd D:\Project AI\SAM
pip install -e .
# atau
set PYTHONPATH=%cd%\src
```

## Masalah Database

### Database error saat inisialisasi

**Gejala:** Error `database locked` atau `no such table`

**Solusi:**
1. Hapus file `sam.db`
2. Hapus file `test_rc2.db` dan file `.db` lain yang tidak perlu
3. Jalankan ulang aplikasi

### Migration gagal

**Gejala:** Error saat menjalankan migration

**Solusi:**
1. Hapus database (`sam.db`)
2. Jalankan ulang — migration akan jalan dari awal

## Masalah CLI

### `sam cluster status` error

**Gejala:** Error karena butuh database infrastructure

**Solusi:** Ini adalah **known issue** untuk standalone mode. Gunakan fallback output yang menampilkan "running as single node". Full cluster status membutuhkan database infrastructure tambahan.

### `sam health` error database

**Gejala:** Database status "ERROR"

**Solusi:**
1. Pastikan database sudah dimigrasi: jalankan `sam health` sekali, database akan otomatis dimigrasi saat pertama kali diakses
2. Jika terus error, hapus `sam.db` dan coba lagi

### CLI tidak merespon

**Gejala:** Command hang/tidak ada output

**Solusi:**
1. Tekan `Ctrl+C` untuk membatalkan
2. Periksa apakah ada proses Python lain yang mengunci database
3. Restart terminal

## Masalah Plugin

### Plugin gagal dimuat

**Gejala:** Error `Failed to load plugin`

**Solusi:**
1. Periksa file `plugin.yaml` — pastikan format YAML benar
2. Pastikan `entrypoint` mengarah ke direktori yang ada
3. Periksa semua dependencies plugin
4. Cek log untuk detail error

### Plugin tidak muncul di list

**Gejala:** `sam plugin list` tidak menampilkan plugin yang sudah diinstal

**Solusi:**
1. Jalankan `sam plugin install ./path-ke-plugin` lagi
2. Pastikan plugin manifest valid

## Masalah Workflow

### Workflow gagal di tengah jalan

**Gejala:** Workflow berhenti dengan error

**Solusi:**
1. Periksa log untuk detail error pada step yang gagal
2. Jika timeout, tambahkan nilai timeout yang lebih besar
3. Jika capability tidak ditemukan, periksa ID capability

### Step dependency tidak terpenuhi

**Gejala:** Error `Unknown step dependency`

**Solusi:** Periksa file workflow — pastikan semua `depends_on` mengarah ke `id` step yang ada.

## Masalah Performa

### Memory usage naik terus

**Gejala:** Memory SAM terus meningkat seiring waktu

**Solusi:**
1. Periksa apakah ada loop yang tidak terkendali
2. Restart SAM
3. Jika terjadi terus, laporkan sebagai issue

### Database terlalu besar

**Gejala:** File `sam.db` membesar tidak terkendali

**Solusi:**
1. Hapus log lama atau data histori yang tidak diperlukan
2. Vacuum database: jalankan `VACUUM;` melalui SQLite
3. Atur retensi data di konfigurasi

## Mendapatkan Bantuan

Jika masalah tidak terselesaikan:
1. Periksa [FAQ](faq.md)
2. Buka issue di [GitHub](https://github.com/VanM-Hub/SAM/issues)
3. Hubungi tim pengembang
