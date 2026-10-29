$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Backend virtual environment not found. Run .\setup.ps1 first." }
Push-Location $Backend
try { & $Python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 }
finally { Pop-Location }
