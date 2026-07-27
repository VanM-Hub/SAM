$path = "C:\Users\vanma\.openclaw\workspace\MEMORY.md"
$lines = Get-Content $path

# Take lines 0..37 (header, quick ref, van, alur, preferensi, and SAM header up to but not including RC3 section)
$headerLines = $lines[0..37]

# Find where "33 sprints" repeated line starts (the line after the RC3 section)
# Find line index where line starts with "**33 sprints" AND it's not the first one
$secondRepeatIdx = -1
$foundFirst = $false
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "\*\*33 sprints") {
        if (-not $foundFirst) {
            $foundFirst = $true
        } else {
            $secondRepeatIdx = $i
            break
        }
    }
}

if ($secondRepeatIdx -eq -1) {
    Write-Host "ERROR: Could not find second occurrence of 33 sprints"
    exit 1
}

$footerLines = $lines[$secondRepeatIdx..($lines.Count-1)]

# New GA section
$newSection = @()
$newSection += "### GA Status (2026-07-27)"
$newSection += "- **SAM Framework v1.0.0 GA resmi dirilis!**"
$newSection += "- **Commit final:** aeb20d5"
$newSection += "- **Tag:** v1.0.0 pushed ke origin"
$newSection += "- **Branch:** feature/sprint13-plugin-runtime"
$newSection += "- **Soak test:** 18,2 jam, 0 error, memory stabil ~21 MB, CPU idle"
$newSection += "- **Kesimpulan:** LOLOS - siap produksi"
$newSection += "- **CLI:** sam.ps1 health"

$newContent = ($headerLines + $newSection + $footerLines) -join "`r`n"
[System.IO.File]::WriteAllText($path, $newContent, [System.Text.UTF8Encoding]::new($false))
Write-Host "Updated MEMORY.md - Lines: header=$($headerLines.Count) section=$($newSection.Count) footer=$($footerLines.Count)"
