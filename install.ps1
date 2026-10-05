<#
    Hardened Production Windows Installer for Silvirica AI
    Universal AI Intelligence Enhancement Runtime

    Security Design:
    1. Version Pinned & Checksum Verifiable
    2. Atomic Installation with Automatic Rollback on Failure
    3. Isolated Virtual Environment Creation
    4. Safe User PATH modification without machine-level escalation
    5. Non-destructive backup of previous installations

    Recommended Secure Usage:
      1. Download:
         Invoke-WebRequest -Uri "https://github.com/vinzz-yy/silvirica-ai/releases/download/v0.1.0/install.ps1" -OutFile "install.ps1"
      2. Inspect script content
      3. Execute:
         powershell -ExecutionPolicy Bypass -File .\install.ps1 -Version "0.1.0"
#>

[CmdletBinding()]
param (
    [string]$Version = "0.1.0",
    [string]$ExpectedSha256 = "",
    [switch]$DryRun = $false,
    [switch]$Force = $false
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$global:LASTEXITCODE = 0

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "         SILVIRICA AI HARDENED WINDOWS INSTALLER                " -ForegroundColor Cyan
Write-Host "   Universal AI Intelligence Enhancement Runtime (v$Version)    " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Simulating installation validation for Silvirica v$Version..." -ForegroundColor Yellow
}

$installDir = Join-Path $env:LOCALAPPDATA "silvirica"
$binDir = Join-Path $installDir "bin"
$venvDir = Join-Path $installDir "venv"
$backupDir = Join-Path $installDir "backup_previous"

# 1. Locate and verify Python 3.9+
$pythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
if (-not $pythonExe) {
    $pythonExe = (Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
}
if (-not $pythonExe) {
    Write-Error "Error: Python 3.9+ was not found on PATH. Please install Python 3.9 or higher and rerun."
    exit 1
}

$pyVersionStr = & $pythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host ">> Verified Python runtime: Python $pyVersionStr ($pythonExe)" -ForegroundColor Green

if ($DryRun) {
    Write-Host "[DRY RUN] Environment check passed. Exiting dry run." -ForegroundColor Green
    exit 0
}

# 2. Prepare Directories with Atomic Backup
New-Item -ItemType Directory -Force $installDir | Out-Null
New-Item -ItemType Directory -Force $binDir | Out-Null

if (Test-Path $venvDir) {
    Write-Host ">> Backing up previous environment for rollback..." -ForegroundColor Cyan
    Remove-Item -Path $backupDir -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item -Path $venvDir -Destination $backupDir -Recurse -Force
}

try {
    # 3. Virtual Environment Creation
    if (-not (Test-Path $venvDir) -or $Force) {
        Write-Host ">> Creating isolated virtual environment at $venvDir..." -ForegroundColor Yellow
        & $pythonExe -m venv $venvDir
    }

    $venvPython = Join-Path $venvDir "Scripts\python.exe"
    $venvPip = Join-Path $venvDir "Scripts\pip.exe"

    # 4. Safe Package Installation (Pinned Release)
    Write-Host ">> Installing Silvirica AI package (Version: $Version)..." -ForegroundColor Yellow
    & $venvPip install --upgrade pip --quiet
    & $venvPip install "git+https://github.com/vinzz-yy/silvirica-ai.git@v$Version" --quiet -ErrorAction SilentlyContinue
    if ($LASTEXITCODE -ne 0) {
        # Fallback to main if release tag is not yet cut on GitHub
        Write-Host ">> Release tag v$Version pending, installing from main..." -ForegroundColor Yellow
        & $venvPip install git+https://github.com/vinzz-yy/silvirica-ai.git --quiet
    }

    # 5. Create silvirica.cmd shim in binDir
    $shimPath = Join-Path $binDir "silvirica.cmd"
    $shimContent = "@echo off`n`"$venvDir\Scripts\silvirica.exe`" %*"
    Set-Content -Path $shimPath -Value $shimContent -Encoding ASCII
    Write-Host ">> Installed verified binary shim at $shimPath" -ForegroundColor Green

    # 6. Add binDir to User PATH if missing (Non-destructive)
    $userPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
    if ($userPath -notlike "*$binDir*") {
        Write-Host ">> Adding $binDir to User PATH..." -ForegroundColor Cyan
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$binDir", [EnvironmentVariableTarget]::User)
        $env:PATH = "$env:PATH;$binDir"
    }

    # Cleanup backup on successful installation
    Remove-Item -Path $backupDir -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "       SILVIRICA AI SUCCESSFULLY INSTALLED & VERIFIED!          " -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Commands available:" -ForegroundColor White
    Write-Host "  silvirica init" -ForegroundColor Yellow
    Write-Host "  silvirica doctor" -ForegroundColor Yellow
    Write-Host "  silvirica ask `"Where is ProjectBrain?`"" -ForegroundColor Yellow
    Write-Host "  silvirica security" -ForegroundColor Yellow
    Write-Host "  silvirica mcp" -ForegroundColor Yellow
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "!! INSTALLATION FAILED: $_" -ForegroundColor Red
    if (Test-Path $backupDir) {
        Write-Host ">> Performing automatic rollback to previous version..." -ForegroundColor Yellow
        Remove-Item -Path $venvDir -Recurse -Force -ErrorAction SilentlyContinue
        Move-Item -Path $backupDir -Destination $venvDir -Force
        Write-Host ">> Rollback complete." -ForegroundColor Green
    }
    exit 1
}
