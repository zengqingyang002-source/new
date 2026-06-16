$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ProjectRoot "work\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host "Starting backend on http://localhost:8000"
Start-Process -FilePath "python" `
  -ArgumentList "run.py" `
  -WorkingDirectory (Join-Path $ProjectRoot "backend") `
  -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $LogDir "backend.out.log") `
  -RedirectStandardError (Join-Path $LogDir "backend.err.log")

Write-Host "Starting frontend on http://localhost:5173"
Start-Process -FilePath "npm.cmd" `
  -ArgumentList "run", "dev" `
  -WorkingDirectory (Join-Path $ProjectRoot "frontend") `
  -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $LogDir "frontend.out.log") `
  -RedirectStandardError (Join-Path $LogDir "frontend.err.log")

Write-Host "Done. Logs are in $LogDir"
