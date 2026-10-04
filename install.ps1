<#
    Native Windows Installer for Silvirica AI
    Universal AI Intelligence Enhancement Runtime

    Usage:
      irm https://raw.githubusercontent.com/vinzz-yy/silvirica-ai/main/install.ps1 | iex
#>

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$global:LASTEXITCODE = 0

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "                SILVIRICA AI WINDOWS INSTALLER                  " -ForegroundColor Cyan
Write-Host "     Universal AI Intelligence Enhancement Runtime (V0.1.0)     " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$installDir = Join-Path $env:LOCALAPPDATA "silvirica"
$binDir = Join-Path $installDir "bin"
$venvDir = Join-Path $installDir "venv"

New-Item -ItemType Directory -Force $installDir | Out-Null
New-Item -ItemType Directory -Force $binDir | Out-Null

# 1. Locate Python
$pythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
if (-not $pythonExe) {
    $pythonExe = (Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
}
if (-not $pythonExe) {
    Write-Error "Python 3.9+ was not found on PATH. Please install Python and rerun."
    exit 1
}

Write-Host ">> Using Python: $pythonExe" -ForegroundColor Green

# 2. Setup Virtualenv
if (-not (Test-Path $venvDir)) {
    Write-Host ">> Creating virtual environment at $venvDir..." -ForegroundColor Yellow
    & $pythonExe -m venv $venvDir
}

$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip = Join-Path $venvDir "Scripts\pip.exe"

# 3. Install Package
Write-Host ">> Installing Silvirica AI runtime..." -ForegroundColor Yellow
& $venvPip install --upgrade pip --quiet
& $venvPip install git+https://github.com/vinzz-yy/silvirica-ai.git --quiet

# 4. Create silvirica.cmd shim in binDir
$shimPath = Join-Path $binDir "silvirica.cmd"
$shimContent = "@echo off`n`"$venvDir\Scripts\silvirica.exe`" %*"
Set-Content -Path $shimPath -Value $shimContent -Encoding ASCII

Write-Host ">> Installed binary shim at $shimPath" -ForegroundColor Green

# 5. Add binDir to User PATH if missing
$userPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
if ($userPath -notlike "*$binDir*") {
    Write-Host ">> Adding $binDir to User PATH..." -ForegroundColor Cyan
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$binDir", [EnvironmentVariableTarget]::User)
    $env:PATH = "$env:PATH;$binDir"
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "       SILVIRICA AI SUCCESSFULLY INSTALLED & READY!             " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Try running:" -ForegroundColor White
Write-Host "  silvirica init" -ForegroundColor Yellow
Write-Host "  silvirica doctor" -ForegroundColor Yellow
Write-Host "  silvirica ask `"Where is ProjectBrain?`"" -ForegroundColor Yellow
Write-Host "  silvirica benchmark" -ForegroundColor Yellow
Write-Host "  silvirica dashboard" -ForegroundColor Yellow
Write-Host ""
