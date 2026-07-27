# sam.ps1 — SAM CLI wrapper
# Usage: .\sam <command> [args...]
# Example: .\sam health
#          .\sam autonomy status

$env:PYTHONPATH = "D:\Project AI\SAM\src"
$samArgs = $args -join " "
python -m sam.cli.main $samArgs 2>&1 | Where-Object { $_ -notmatch "warning|warn|UserWarning|allow_mutation" }
