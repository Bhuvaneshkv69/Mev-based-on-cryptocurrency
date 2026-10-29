$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Frontend = Join-Path $Root "frontend"
if (-not (Test-Path (Join-Path $Frontend "node_modules"))) { throw "Frontend dependencies not found. Run .\setup.ps1 first." }
Push-Location $Frontend
try { npm run dev }
finally { Pop-Location }
