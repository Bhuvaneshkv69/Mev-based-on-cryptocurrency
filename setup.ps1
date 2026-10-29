$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Write-Host "[1/4] Checking Python..." -ForegroundColor Cyan
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.11+ and enable the Python Launcher."
}
Write-Host "[2/4] Creating backend virtual environment..." -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $Backend ".venv\Scripts\python.exe"))) {
    py -3.11 -m venv (Join-Path $Backend ".venv")
}
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $Backend "requirements.txt")

if (-not (Test-Path (Join-Path $Backend ".env"))) {
    Copy-Item (Join-Path $Backend ".env.example") (Join-Path $Backend ".env")
    Write-Host "Created backend\.env from backend\.env.example. Edit its PostgreSQL settings before migrating." -ForegroundColor Yellow
} else {
    Write-Host "backend\.env already exists; leaving it unchanged." -ForegroundColor Yellow
}

if (-not (Test-Path (Join-Path $Frontend ".env"))) {
    Copy-Item (Join-Path $Frontend ".env.example") (Join-Path $Frontend ".env")
}
Write-Host "[4/4] Installing frontend packages..." -ForegroundColor Cyan
Push-Location $Frontend
try { npm install } finally { Pop-Location }
Write-Host "Setup completed. Review backend\.env and make sure PostgreSQL is running before applying migrations." -ForegroundColor Green
