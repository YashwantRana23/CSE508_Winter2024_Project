$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot 'backend/.venv/Scripts/python.exe'
$nextPath = Join-Path $projectRoot 'frontend/node_modules/next/dist/bin/next'
if (!(Test-Path -LiteralPath $pythonPath) -or !(Test-Path -LiteralPath $nextPath)) {
    throw 'Install backend and frontend dependencies first; see README.md.'
}
if (!(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue)) {
    $backend = Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'backend.stdout.log') -RedirectStandardError (Join-Path $projectRoot 'backend.stderr.log') -PassThru
    Write-Host "Started backend PID $($backend.Id)"
} else { Write-Host 'Port 8000 is already occupied; no second backend started.' }
if (!(Get-NetTCPConnection -State Listen -LocalPort 3000 -ErrorAction SilentlyContinue)) {
    $frontend = Start-Process -FilePath (Get-Command node.exe).Source -ArgumentList 'node_modules/next/dist/bin/next','dev','--hostname','127.0.0.1' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'frontend.stdout.log') -RedirectStandardError (Join-Path $projectRoot 'frontend.stderr.log') -PassThru
    Write-Host "Started frontend PID $($frontend.Id)"
} else { Write-Host 'Port 3000 is already occupied; no second frontend started.' }
Write-Host 'Dashboard: http://localhost:3000/dashboard'
Write-Host 'API docs: http://localhost:8000/docs'
Write-Host 'Allow a few seconds for startup. See *.stdout.log and *.stderr.log for status.'
