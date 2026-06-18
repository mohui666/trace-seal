param(
    [ValidateSet("Source", "Artifacts")]
    [string]$Mode = "Artifacts"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")

Write-Host "=== TraceSeal Release Verification ===" -ForegroundColor Cyan
Write-Host "Mode: $Mode"
Write-Host "Repository: $RepoRoot"
Write-Host ""

$ExitCode = 0
$Warnings = @()
$Errors = @()

function Write-Pass { Write-Host "  PASS: $args" -ForegroundColor Green }
function Write-Fail { Write-Host "  FAIL: $args" -ForegroundColor Red }
function Write-Warn { Write-Host "  WARN: $args" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# 1. Git working tree check
# ---------------------------------------------------------------------------
Push-Location $RepoRoot
try {
    $gitStatus = git status --porcelain 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Unable to read git status (not a git repository or git not available)"
        $Warnings += "Git working tree check skipped"
    } elseif ($gitStatus) {
        Write-Warn "Working tree is not clean"
        $Warnings += "Git working tree has uncommitted changes"
        Write-Host "  Uncommitted files:"
        $gitStatus | ForEach-Object { Write-Host "    $_" }
    } else {
        Write-Pass "Git working tree is clean"
    }
} finally { Pop-Location }

# ---------------------------------------------------------------------------
# 2. Version consistency
# ---------------------------------------------------------------------------
function Get-JsonVersion {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $content = Get-Content $Path -Raw | ConvertFrom-Json
    return $content.version
}

function Get-PyprojectVersion {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $content = Get-Content $Path -Raw
    if ($content -match 'version\s*=\s*"([^"]+)"') {
        return $Matches[1]
    }
    return $null
}

$rendererVersion = Get-JsonVersion (Join-Path $RepoRoot "desktop/renderer/package.json")
$electronVersion = Get-JsonVersion (Join-Path $RepoRoot "desktop/electron/package.json")
$pythonVersion = Get-PyprojectVersion (Join-Path $RepoRoot "pyproject.toml")

Write-Host ""
Write-Host "--- Version Consistency ---"

$versions = @($rendererVersion, $electronVersion, $pythonVersion) | Where-Object { $_ }
$uniqueVersions = $versions | Select-Object -Unique

if ($null -eq $rendererVersion) {
    Write-Fail "desktop/renderer/package.json version not found"
    $Errors += "Missing renderer version"
}
if ($null -eq $electronVersion) {
    Write-Fail "desktop/electron/package.json version not found"
    $Errors += "Missing electron version"
}
if ($null -eq $pythonVersion) {
    Write-Fail "pyproject.toml version not found"
    $Errors += "Missing Python version"
}

if ($rendererVersion -and $electronVersion -and $pythonVersion) {
    Write-Host "  Renderer: $rendererVersion"
    Write-Host "  Electron:  $electronVersion"
    Write-Host "  Python:    $pythonVersion"

    if ($uniqueVersions.Count -eq 1) {
        Write-Pass "All versions consistent: $($uniqueVersions | Select-Object -First 1)"
    } else {
        Write-Fail "Version mismatch: $($versions -join ', ')"
        $Errors += "Version inconsistency detected"
    }
}

# ---------------------------------------------------------------------------
# 3. Branch / tag validation
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "--- Branch / Tag Validation ---"

Push-Location $RepoRoot
try {
    $branch = git rev-parse --abbrev-ref HEAD 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Unable to determine current branch"
        $Warnings += "Branch detection failed"
    } else {
        Write-Host "  Current branch: $branch"

        $prevEAP = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $tag = git describe --tags --exact-match 2>$null
        $isTag = ($LASTEXITCODE -eq 0)
        $ErrorActionPreference = $prevEAP

        if ($Mode -eq "Source") {
            # Source mode: allow main, chore/v0.2-release-prep, or other dev branches
            if ($branch -eq "main" -or $branch -eq "chore/v0.2-release-prep") {
                Write-Pass "Branch '$branch' is valid for Source mode"
            } elseif ($branch -eq "master") {
                Write-Fail "Branch 'master' is NOT a valid release baseline. Default branch is 'main'."
                $Errors += "Branch 'master' is not a valid release baseline"
            } else {
                Write-Warn "Branch '$branch' is not a standard release branch; proceeding with warning"
                $Warnings += "Non-standard branch: $branch"
            }
        } elseif ($Mode -eq "Artifacts") {
            # Artifacts mode: allow main, v* tag detached HEAD
            if ($branch -eq "main") {
                Write-Pass "Branch 'main' is valid for Artifacts mode"
            } elseif ($isTag -and $tag -match '^v') {
                Write-Pass "Tag '$tag' is valid for Artifacts mode"
            } elseif ($branch -eq "HEAD" -and $isTag -and $tag -match '^v') {
                Write-Pass "Detached HEAD at tag '$tag' is valid for Artifacts mode"
            } elseif ($branch -eq "master") {
                Write-Fail "Branch 'master' is NOT a valid release baseline. Default branch is 'main'."
                $Errors += "Branch 'master' is not a valid release baseline"
            } else {
                Write-Fail "Branch '$branch' is not valid for Artifacts mode. Expected 'main' or v* tag."
                $Errors += "Invalid branch for Artifacts mode: $branch"
            }
        }
    }
} finally { Pop-Location }

# ---------------------------------------------------------------------------
# 4. Artifact checks (Artifacts mode only)
# ---------------------------------------------------------------------------
if ($Mode -eq "Artifacts") {
    Write-Host ""
    Write-Host "--- Artifact Verification ---"

    $makeDir = Join-Path $RepoRoot "desktop/electron/out/make/squirrel.windows/x64"
    $setupExe = Join-Path $makeDir "TraceSeal-Setup.exe"
    $sha256File = Join-Path $makeDir "SHA256SUMS.txt"
    $rendererIndex = Join-Path $RepoRoot "desktop/electron/out/TraceSeal-win32-x64/resources/renderer/index.html"
    $coreExe = Join-Path $RepoRoot "desktop/electron/out/TraceSeal-win32-x64/resources/traceseal-core/traceseal-core.exe"

    # Check TraceSeal-Setup.exe
    if (Test-Path $setupExe) {
        Write-Pass "TraceSeal-Setup.exe found"
    } else {
        Write-Fail "TraceSeal-Setup.exe NOT found at: $setupExe"
        $Errors += "Missing TraceSeal-Setup.exe"
    }

    # Check SHA256SUMS.txt
    if (Test-Path $sha256File) {
        Write-Pass "SHA256SUMS.txt found"
    } else {
        Write-Fail "SHA256SUMS.txt NOT found at: $sha256File"
        $Errors += "Missing SHA256SUMS.txt"
    }

    # Check Renderer resources
    if (Test-Path $rendererIndex) {
        Write-Pass "Renderer resources found (index.html)"
    } else {
        Write-Fail "Renderer resources NOT found at: $rendererIndex"
        $Errors += "Missing Renderer resources"
    }

    # Check traceseal-core.exe
    if (Test-Path $coreExe) {
        Write-Pass "traceseal-core.exe found"
    } else {
        Write-Fail "traceseal-core.exe NOT found at: $coreExe"
        $Errors += "Missing traceseal-core.exe"
    }

    # Verify SHA256 if both files exist
    if ((Test-Path $setupExe) -and (Test-Path $sha256File)) {
        Write-Host ""
        Write-Host "--- SHA256 Verification ---"

        $expectedHash = (Get-Content $sha256File | Where-Object { $_ -match 'TraceSeal-Setup\.exe' } | ForEach-Object { ($_ -split '\s+')[0] }).Trim()
        if ($expectedHash) {
            $actualHash = (Get-FileHash -Path $setupExe -Algorithm SHA256).Hash.ToLower()
            if ($actualHash -eq $expectedHash.ToLower()) {
                Write-Pass "SHA256 matches: $actualHash"
            } else {
                Write-Fail "SHA256 mismatch!"
                Write-Host "  Expected: $expectedHash"
                Write-Host "  Actual:   $actualHash"
                $Errors += "SHA256 mismatch for TraceSeal-Setup.exe"
            }
        } else {
            Write-Warn "Could not find SHA256 entry for TraceSeal-Setup.exe in SHA256SUMS.txt"
            $Warnings += "SHA256 entry not found in SHA256SUMS.txt"
        }
    }
} else {
    Write-Host ""
    Write-Host "--- Artifact Verification ---"
    Write-Host "  Skipped (Source mode - artifacts not required)"
}

# ---------------------------------------------------------------------------
# 5. Final result
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($Errors.Count -gt 0) {
    Write-Host "RESULT: FAIL" -ForegroundColor Red
    Write-Host ""
    Write-Host "Errors ($($Errors.Count)):" -ForegroundColor Red
    $Errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    $ExitCode = 1
} else {
    Write-Host "RESULT: PASS" -ForegroundColor Green
    $ExitCode = 0
}

if ($Warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "Warnings ($($Warnings.Count)):" -ForegroundColor Yellow
    $Warnings | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
}

Write-Host ""
Write-Host "Mode: $Mode"
Write-Host "Exit code: $ExitCode"

exit $ExitCode