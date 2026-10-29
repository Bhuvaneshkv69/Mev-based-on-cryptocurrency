$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Backend virtual environment not found. Run .\setup.ps1 first." }
if (-not (Test-Path (Join-Path $Backend ".env"))) { throw "backend\.env is missing. Run .\setup.ps1 and configure the database settings." }
Push-Location $Backend
try { & $Python -m alembic upgrade head; if ($LASTEXITCODE -ne 0) { throw "Alembic migration failed with exit code $LASTEXITCODE." } }
finally { Pop-Location }
