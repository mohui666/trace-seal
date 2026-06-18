param(
    [switch]$SkipInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Npm = if (Get-Command npm.cmd -ErrorAction SilentlyContinue) { "npm.cmd" } else { "npm" }
$Python = if (Get-Command python.exe -ErrorAction SilentlyContinue) { "python.exe" } else { "python" }

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Script
    )
    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Script
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Name (exit code $LASTEXITCODE)"
    }
}

function Push-StepLocation {
    param([Parameter(Mandatory = $true)][string]$Path)
    Push-Location $Path
}

Write-Host "TraceSeal Windows build root: $RepoRoot" -ForegroundColor Green
Set-Location $RepoRoot

Invoke-Step "Python unittest" {
    & $Python -m unittest discover -s tests -v
}

Invoke-Step "Ensure PyInstaller" {
    $PyInstallerExit = 0
    try {
        & $Python -m PyInstaller --version *> $null
        $PyInstallerExit = $LASTEXITCODE
    }
    catch {
        $PyInstallerExit = 1
    }
    if ($PyInstallerExit -ne 0) {
        if ($SkipInstall) {
            throw "PyInstaller is not installed and -SkipInstall was set"
        }
        & $Python -m pip install pyinstaller
    }
}

Invoke-Step "Build PyInstaller TraceSeal Core" {
    $DistDir = Join-Path $RepoRoot "packaging\dist"
    $BuildDir = Join-Path $RepoRoot "packaging\build"
    $SpecDir = Join-Path $RepoRoot "packaging"
    $CoreDir = Join-Path $DistDir "traceseal-core"
    if (Test-Path $CoreDir) {
        Remove-Item -LiteralPath $CoreDir -Recurse -Force
    }
    $DataSep = if ($env:OS -eq "Windows_NT") { ";" } else { ":" }
    $PolicyData = "$(Join-Path $RepoRoot "policy\default_policy.json")${DataSep}policy"
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onedir `
        --name traceseal-core `
        --distpath $DistDir `
        --workpath $BuildDir `
        --specpath $SpecDir `
        --add-data $PolicyData `
        packaging\traceseal_core_entry.py
}

Invoke-Step "Smoke test bundled TraceSeal Core" {
    $CoreExe = Join-Path $RepoRoot "packaging\dist\traceseal-core\traceseal-core.exe"
    if (-not (Test-Path $CoreExe)) {
        throw "Missing bundled core executable: $CoreExe"
    }
    & $CoreExe dashboard-data policy | Out-Null
}

Invoke-Step "Renderer install/typecheck/test/build" {
    Push-StepLocation (Join-Path $RepoRoot "desktop\renderer")
    try {
        if (-not $SkipInstall) {
            & $Npm install
        }
        & $Npm run typecheck
        & $Npm test
        & $Npm run build
    }
    finally {
        Pop-Location
    }
}

Invoke-Step "Electron install/typecheck/test" {
    Push-StepLocation (Join-Path $RepoRoot "desktop\electron")
    try {
        if (-not $SkipInstall) {
            & $Npm install
        }
        & $Npm run typecheck
        & $Npm test
    }
    finally {
        Pop-Location
    }
}

Invoke-Step "Electron Forge make" {
    Push-StepLocation (Join-Path $RepoRoot "desktop\electron")
    try {
        & $Npm run make
    }
    finally {
        Pop-Location
    }
}

$Installer = Get-ChildItem -Path (Join-Path $RepoRoot "desktop\electron\out\make") -Recurse -Filter "TraceSeal-Setup.exe" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Installer) {
    throw "TraceSeal-Setup.exe was not produced"
}

Write-Host ""
Write-Host "TraceSeal Windows installer:" -ForegroundColor Green
Write-Host $Installer.FullName
