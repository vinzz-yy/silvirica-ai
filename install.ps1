<#
    Hardened Production Windows Installer for Silvirica AI
    Universal AI Intelligence Enhancement Runtime

    Security Design:
    1. Version Pinned & Checksum Verifiable
    2. Atomic Installation with Automatic Rollback on Failure
    3. Isolated Virtual Environment Creation
    4. Safe User PATH modification without machine-level escalation
    5. Non-destructive backup of previous installations
    6. No silent trust-boundary switching (main fallback requires explicit -Channel main)

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
    [string]$Release = "",
    [ValidateSet("release", "main", "dev")]
    [string]$Channel = "release",
    [string]$ExpectedSha256 = "",
    [string]$InstallDir = "",
    [switch]$DryRun = $false,
    [switch]$Force = $false
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$global:LASTEXITCODE = 0

# Resolve effective version / release tag
$targetVersion = if ($Release -ne "") { $Release.TrimStart('v') } else { $Version.TrimStart('v') }
$releaseTag = "v$targetVersion"

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "         SILVIRICA AI HARDENED WINDOWS INSTALLER                " -ForegroundColor Cyan
Write-Host "   Universal AI Intelligence Enhancement Runtime (v$targetVersion)    " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Simulating installation validation for Silvirica v$targetVersion (Channel: $Channel)..." -ForegroundColor Yellow
}

$baseInstallDir = if ($InstallDir -ne "") { $InstallDir } else { Join-Path $env:LOCALAPPDATA "silvirica" }
$binDir = Join-Path $baseInstallDir "bin"
$venvDir = Join-Path $baseInstallDir "venv"
$backupDir = Join-Path $baseInstallDir "backup_previous"

# 1. Locate and verify Python 3.9+
$pythonExe = ""
$pythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1
if ($pythonCmd) {
    $pythonExe = $pythonCmd
}

if (-not $pythonExe) {
    $pyCmd = Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1
    if ($pyCmd) {
        $pythonExe = $pyCmd
    }
}

if (-not $pythonExe) {
    # Search common Windows installation locations
    $candidates = @(
        (Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName),
        (Get-ChildItem -Path "$env:LOCALAPPDATA\Python\*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName),
        (Get-ChildItem -Path "C:\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName),
        (Get-ChildItem -Path "C:\Program Files\Python*\python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
    )
    foreach ($cand in $candidates) {
        if ($cand -and (Test-Path $cand)) {
            $pythonExe = $cand
            break
        }
    }
}

if (-not $pythonExe) {
    Write-Error "Error: Python 3.9+ was not found on PATH or standard directories. Please install Python 3.9 or higher and rerun."
    exit 1
}

# Verify Python version >= 3.9
& $pythonExe -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error: Python 3.9 or higher is required. Found an older Python version at $pythonExe."
    exit 1
}

$pyVersionStr = & $pythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Host ">> Verified Python runtime: Python $pyVersionStr ($pythonExe)" -ForegroundColor Green

# Verify SHA-256 Checksum if ExpectedSha256 is supplied
if ($ExpectedSha256 -ne "") {
    Write-Host ">> Validating checksum requirement for target package..." -ForegroundColor Cyan
    $normalizedExpected = $ExpectedSha256.Trim().ToLower()
    if ($normalizedExpected.Length -ne 64) {
        Write-Error "Error: ExpectedSha256 must be a valid 64-character hexadecimal SHA-256 hash string."
        exit 1
    }
}

if ($DryRun) {
    Write-Host "[DRY RUN] Environment check passed. Installation target: $venvDir" -ForegroundColor Green
    Write-Host "[DRY RUN] Exiting dry run." -ForegroundColor Green
    exit 0
}

# 2. Prepare Directories with Atomic Backup
New-Item -ItemType Directory -Force $baseInstallDir | Out-Null
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
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create virtual environment at $venvDir"
        }
    }

    $venvPython = Join-Path $venvDir "Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        throw "Virtual environment python executable not found at $venvPython"
    }

    # 4. Safe Pip Upgrade and Package Installation
    Write-Host ">> Upgrading pip inside virtual environment..." -ForegroundColor Yellow
    & "$venvPython" -m pip install --upgrade pip --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Warning: pip upgrade returned non-zero code $LASTEXITCODE; proceeding with current pip."
    }

    # If an expected SHA-256 is provided for an installation package, verify it
    if ($ExpectedSha256 -ne "") {
        Write-Host ">> Downloading and verifying package artifact with SHA-256..." -ForegroundColor Yellow
        $tempPkg = Join-Path $baseInstallDir "silvirica-pkg.tar.gz"
        $downloadUrl = "https://github.com/vinzz-yy/silvirica-ai/archive/refs/tags/$releaseTag.tar.gz"
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tempPkg -UseBasicParsing
        
        $actualHash = (Get-FileHash -Path $tempPkg -Algorithm SHA256).Hash.ToLower()
        if ($actualHash -ne $normalizedExpected) {
            Remove-Item -Path $tempPkg -Force -ErrorAction SilentlyContinue
            throw "SHA-256 Checksum verification failed! Expected: $normalizedExpected, Actual: $actualHash. Aborting installation."
        }
        Write-Host ">> SHA-256 checksum verified successfully ($actualHash)" -ForegroundColor Green
        
        # Install verified package
        & "$venvPython" -m pip install "$tempPkg" --quiet
        Remove-Item -Path $tempPkg -Force -ErrorAction SilentlyContinue
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install verified package artifact."
        }
    } elseif ($Channel -eq "main" -or $Channel -eq "dev") {
        Write-Host ">> Installing Silvirica AI from main branch (development channel)..." -ForegroundColor Yellow
        & "$venvPython" -m pip install "git+https://github.com/vinzz-yy/silvirica-ai.git" --quiet
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install Silvirica AI package from main branch."
        }
    } else {
        Write-Host ">> Installing Silvirica AI package (Pinned Release: $releaseTag)..." -ForegroundColor Yellow
        & "$venvPython" -m pip install "git+https://github.com/vinzz-yy/silvirica-ai.git@$releaseTag" --quiet
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install pinned release tag '$releaseTag'. The requested release does not exist or network failed. To install from development branch, explicitly run with '-Channel main'."
        }
    }

    # 5. Create silvirica.cmd shim in binDir
    $shimPath = Join-Path $binDir "silvirica.cmd"
    $shimContent = "@echo off`r`n`"$venvDir\Scripts\silvirica.exe`" %*"
    Set-Content -Path $shimPath -Value $shimContent -Encoding ASCII
    Write-Host ">> Installed verified binary shim at $shimPath" -ForegroundColor Green

    # 6. Verify Installed CLI
    Write-Host ">> Verifying installed Silvirica CLI..." -ForegroundColor Cyan
    $cliTest = & "$venvPython" -m silvirica.cli.main --help
    if ($LASTEXITCODE -ne 0) {
        throw "Silvirica CLI verification failed with exit code $LASTEXITCODE"
    }

    # 7. Add binDir to User PATH if missing (Non-destructive)
    $userPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
    if (-not $userPath) {
        $userPath = ""
    }
    $pathParts = $userPath -split ';' | Where-Object { $_ -ne "" }
    if ($pathParts -notcontains $binDir) {
        Write-Host ">> Adding $binDir to User PATH..." -ForegroundColor Cyan
        $newPath = ($pathParts + $binDir) -join ';'
        [Environment]::SetEnvironmentVariable("Path", $newPath, [EnvironmentVariableTarget]::User)
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
    Write-Host "  silvirica ask `"What functions exist in app.py?`"" -ForegroundColor Yellow
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
    } elseif (Test-Path $venvDir) {
        Remove-Item -Path $venvDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    exit 1
}

