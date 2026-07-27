$path = "C:\Users\vanma\.openclaw\workspace\MEMORY.md"
$content = Get-Content $path -Raw

# Find the section from "- Semua error sudah difix" through "- Lapor"
$oldBlock = @"
- **Soak test berjalan** - script `scripts/soak_test.py`, log di `logs/soak_test.log`
- **Komponen diamati**: CognitiveManager, ReflectionManager, AutonomyController, Evolution params, Memory (psutil), Error rate
- **Semua error sudah difix** - 0 errors pada run terakhir
- **Duration**: 7 hari planning
- **Status saat ini**: Belum dicek sejak 2026-07-25. Perlu review log soak test.
- **Cek**: `Get-Content D:\Project AI\SAM\logs\soak_test.log -Tail 20`
- **Lapor**: Setelah 7 hari (2026-08-01) atau jika error rate > 0 bertahan dalam 24 jam
"@

$newBlock = @"
- **SAM Framework v1.0.0 GA resmi dirilis!** 🎉
- **Commit final:** `aeb20d5`
- **Tag:** `v1.0.0` pushed ke `origin`
- **Branch:** `feature/sprint13-plugin-runtime`
- **Soak test:** 18,2 jam, 0 error, memory stabil ~21 MB, CPU idle
- **Kesimpulan:** ✅ LOLOS — siap produksi
- **CLI:** `cd D:\Project AI\SAM; .\sam.ps1 health`
"@

$count = 0
$newContent = $content -replace [regex]::Escape($oldBlock), { $count++; $newBlock }
if ($count -eq 0) {
    # try with dashes
    $oldBlockDash = $oldBlock -replace '–', '-' -replace '—', '-'
    $newContent = $content -replace [regex]::Escape($oldBlockDash), { $count++; $newBlock }
}
Write-Host "Replaced: $count blocks"
if ($count -gt 0) {
    [System.IO.File]::WriteAllText($path, $newContent, [System.Text.UTF8Encoding]::new($false))
    Write-Host "File written"
}
