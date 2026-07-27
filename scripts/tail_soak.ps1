# tail_soak.ps1 — Streaming real-time log soak test
# Jalankan: pwsh scripts\tail_soak.ps1
# Atau: powershell scripts\tail_soak.ps1

$logPath = Join-Path $PSScriptRoot ".." "logs" "soak_test.log"

if (-not (Test-Path $logPath)) {
    Write-Host "❌ Log tidak ditemukan: $logPath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "║  SAM Soak Test — Live Monitor" -ForegroundColor Cyan
Write-Host "║  Log: $logPath" -ForegroundColor Cyan
Write-Host "║  Tekan Ctrl+C untuk berhenti" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Get-Content $logPath -Tail 5 -Wait | ForEach-Object {
    $line = $_
    $time = $null
    if ($line -match "(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})") {
        $time = $Matches[1]
    }

    # Colorize
    if ($line -match "error|ERROR|Error|failed|FAILED") {
        Write-Host $line -ForegroundColor Red
    } elseif ($line -match "metrics:") {
        Write-Host $line -ForegroundColor Green
    } elseif ($line -match "diagnose_ok|reflection_ok|autonomy_ok|evolution_ok|attention_ok|assessment_ok") {
        Write-Host $line -ForegroundColor Yellow
    } elseif ($line -match "soak_test_started") {
        Write-Host $line -ForegroundColor Cyan
    } elseif ($line -match "Summary|========") {
        Write-Host $line -ForegroundColor Magenta
    } else {
        Write-Host $line -ForegroundColor Gray
    }
}
