### Running Tests
```powershell
$env:PYTHONPATH = ".\src"
$env:PYTHONIOENCODING = "utf-8"
python -m pytest tests/unit/ tests/integration/ -v --tb=short
```

> Jalankan perintah di atas dari root direktori SAM menggunakan PowerShell.
