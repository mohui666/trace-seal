[CmdletBinding()]
param(
    [switch]$SkipNode,
    [switch]$SkipElectron,
    [switch]$KeepArtifacts
)

$ErrorActionPreference = "Stop"

function Assert-Windows {
    $isWindowsVariable = Get-Variable -Name IsWindows -ErrorAction SilentlyContinue
    if ($null -ne $isWindowsVariable) {
        if (-not [bool]$isWindowsVariable.Value) {
            throw "windows-guard-smoke requires Windows."
        }
        return
    }

    if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
        throw "windows-guard-smoke requires Windows."
    }
}

function Assert-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw "required command not found on PATH: $Name"
    }
    Write-Verbose "found $Name at $($command.Source)"
}

function Assert-ChildPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Parent
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $fullParent = [System.IO.Path]::GetFullPath($Parent)
    if (-not $fullParent.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $fullParent = $fullParent + [System.IO.Path]::DirectorySeparatorChar
    }
    if (-not $fullPath.StartsWith($fullParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "refusing to operate outside expected parent: path=$fullPath parent=$fullParent"
    }
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $repoRoot
    )

    Write-Host ""
    Write-Host "== $Label =="
    Push-Location -LiteralPath $WorkingDirectory
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & $FilePath @Arguments 2>&1
        $exitCode = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
        Pop-Location
    }

    foreach ($line in @($output)) {
        Write-Host $line
    }

    if ($exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode"
    }

    return @($output | ForEach-Object { $_.ToString() })
}

function Get-RustPassedCount {
    param([string[]]$Output)

    $count = 0
    foreach ($match in [regex]::Matches(($Output -join "`n"), "test result: ok\.\s+(\d+) passed")) {
        $count += [int]$match.Groups[1].Value
    }
    return $count
}

function Get-PythonTestCount {
    param([string[]]$Output)

    $matches = [regex]::Matches(($Output -join "`n"), "Ran\s+(\d+)\s+tests?")
    if ($matches.Count -eq 0) {
        return 0
    }
    return [int]$matches[$matches.Count - 1].Groups[1].Value
}

function Test-NpmScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PackageJson,
        [Parameter(Mandatory = $true)]
        [string]$Script
    )

    if (-not (Test-Path -LiteralPath $PackageJson)) {
        return $false
    }
    $package = Get-Content -LiteralPath $PackageJson -Raw | ConvertFrom-Json
    if ($null -eq $package.scripts) {
        return $false
    }
    return $package.scripts.PSObject.Properties.Name -contains $Script
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Content
    )

    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

Assert-Windows

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$runsRoot = Join-Path $repoRoot "runs"
$runRoot = Join-Path $runsRoot "windows-guard-smoke"
$runDir = Join-Path $runRoot "run_windows_guard_smoke"
$guardJsonl = Join-Path $runRoot "guard-events.jsonl"
$sentinel = Join-Path $runRoot "should_not_exist.txt"
$policyFixture = Join-Path $repoRoot "tests\fixtures\policy_guard_warn_process_spawn.yaml"
$pythonSmoke = Join-Path $runRoot "python-smoke.py"
$summaryJson = Join-Path $runRoot "summary.json"

Write-Host "TraceSeal Windows Guard smoke validation"
Write-Host "repo: $repoRoot"
Write-Host "PowerShell: $($PSVersionTable.PSVersion)"

Assert-Command git
Assert-Command python
Assert-Command cargo
Assert-Command rustc
if (-not $SkipNode) {
    Assert-Command npm.cmd
}

Assert-ChildPath -Path $runRoot -Parent $runsRoot
if (Test-Path -LiteralPath $runRoot) {
    Remove-Item -LiteralPath $runRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

$manifest = [ordered]@{
    schema_version = 1
    run_id = "run_windows_guard_smoke"
    command = @("windows-guard-smoke")
    command_display = "windows-guard-smoke"
    started_at = (Get-Date).ToUniversalTime().ToString("o")
    completed_at = (Get-Date).ToUniversalTime().ToString("o")
    status = "completed"
    exit_code = 0
}
Write-Utf8NoBom -Path (Join-Path $runDir "manifest.json") -Content (($manifest | ConvertTo-Json -Depth 8) + "`n")
Write-Utf8NoBom -Path (Join-Path $runDir "events.jsonl") -Content ""

$summary = [ordered]@{
    result = "FAIL"
    guard_health = "not run"
    process_spawn_dry_run = "not run"
    target_command_executed = "unknown"
    sentinel_absent = "unknown"
    python_import = "not run"
    guard_policy_dry_run = "not run"
    dashboard_guard_metadata = "not run"
    rust_fmt = "not run"
    rust_tests = "not run"
    python_compileall = "not run"
    python_unittest = "not run"
    renderer = if ($SkipNode) { "skipped (-SkipNode)" } else { "not run" }
    electron = if ($SkipNode) { "skipped (-SkipNode)" } elseif ($SkipElectron) { "skipped (-SkipElectron)" } else { "not run" }
    git_diff_check = "not run"
    enforcement = "no"
    daemon_service = "no"
    artifacts_committed = "unknown"
    artifacts_path = "runs/windows-guard-smoke/"
}

try {
    Invoke-Checked `
        -Label "Rust Guard guard.health smoke" `
        -FilePath "cargo" `
        -Arguments @("run", "-p", "traceseal-guard", "--", "health", "--out", $guardJsonl, "--workspace", $repoRoot) | Out-Null
    $summary.guard_health = "passed"

    $targetCommand = "Set-Content -LiteralPath '$sentinel' -Value executed"
    Invoke-Checked `
        -Label "Rust Guard process.spawn dry-run smoke" `
        -FilePath "cargo" `
        -Arguments @(
            "run", "-p", "traceseal-guard", "--",
            "process-spawn",
            "--out", $guardJsonl,
            "--workspace", $repoRoot,
            "--program", "powershell",
            "--arg", "-NoProfile",
            "--arg", "-Command",
            "--arg", $targetCommand,
            "--cwd", $repoRoot
        ) | Out-Null
    $summary.process_spawn_dry_run = "passed"

    if (Test-Path -LiteralPath $sentinel) {
        throw "target command was executed unexpectedly; sentinel exists: $sentinel"
    }
    $summary.target_command_executed = "no"
    $summary.sentinel_absent = "yes"

    @'
from __future__ import annotations

import json
import sys
from pathlib import Path

from dashboard.export import export_dashboard_data
from traceseal.guard_import import import_guard_events
from traceseal.guard_policy import apply_guard_policy_dry_run, get_guard_policy_summary
from traceseal.guard_schema import load_guard_events

run_dir = Path(sys.argv[1])
guard_jsonl = Path(sys.argv[2])
policy_path = Path(sys.argv[3])
sentinel = Path(sys.argv[4])

# Verify metadata.dry_run and metadata.executed stay in the dry-run/non-executed shape.
events = load_guard_events(guard_jsonl)
event_types = [event["event_type"] for event in events]
assert "guard.health" in event_types, "missing guard.health"
assert "process.spawn" in event_types, "missing process.spawn"
spawn_event = [event for event in events if event["event_type"] == "process.spawn"][-1]
assert spawn_event["metadata"]["dry_run"] is True, "process.spawn dry_run must be true"
assert spawn_event["metadata"]["executed"] is False, "process.spawn executed must be false"
assert not sentinel.exists(), "target command was executed unexpectedly"

metadata = import_guard_events(run_dir, guard_jsonl)
assert metadata["guard_event_count"] >= 2, metadata
assert set(metadata["guard_event_types"]) >= {"guard.health", "process.spawn"}, metadata

summary = apply_guard_policy_dry_run(run_dir, policy_path)
assert summary["dry_run"] is True, summary
assert summary["enforcement_applied"] is False, summary
assert summary["evaluated_event_count"] >= 2, summary

policy_summary = get_guard_policy_summary(run_dir)
assert policy_summary["available"] is True, policy_summary
assert policy_summary["dry_run"] is True, policy_summary
assert policy_summary["enforcement_applied"] is False, policy_summary

payload = export_dashboard_data(run_dir)
guard = payload.get("guard")
assert guard, "dashboard payload missing guard"
assert guard["available"] is True, guard
assert guard["event_count"] >= 2, guard
assert "guard.health" in guard["event_types"], guard
assert "process.spawn" in guard["event_types"], guard
policy = guard.get("policy")
assert policy, "dashboard payload missing guard.policy"
assert policy["available"] is True, policy
assert policy["dry_run"] is True, policy
assert policy["enforcement_applied"] is False, policy
json.dumps(payload, ensure_ascii=False)

print("windows guard python smoke ok")
print(json.dumps({
    "guard_event_count": guard["event_count"],
    "guard_event_types": guard["event_types"],
    "policy_decision_counts": policy["decision_counts"],
    "enforcement_applied": policy["enforcement_applied"],
}, sort_keys=True))
'@ | ForEach-Object { Write-Utf8NoBom -Path $pythonSmoke -Content $_ }

    Invoke-Checked `
        -Label "Python import, Guard policy dry-run, dashboard-data smoke" `
        -FilePath "python" `
        -Arguments @($pythonSmoke, $runDir, $guardJsonl, $policyFixture, $sentinel) | Out-Null
    $summary.python_import = "passed"
    $summary.guard_policy_dry_run = "passed (enforcement_applied=false)"
    $summary.dashboard_guard_metadata = "passed"

    Invoke-Checked -Label "cargo fmt --check" -FilePath "cargo" -Arguments @("fmt", "--check") | Out-Null
    $summary.rust_fmt = "passed"

    $rustTestOutput = Invoke-Checked -Label "cargo test" -FilePath "cargo" -Arguments @("test")
    $rustPassedCount = Get-RustPassedCount -Output $rustTestOutput
    $summary.rust_tests = if ($rustPassedCount -gt 0) { "passed ($rustPassedCount tests)" } else { "passed" }

    Invoke-Checked `
        -Label "python compileall" `
        -FilePath "python" `
        -Arguments @("-m", "compileall", "-q", "traceseal", "sdk", "recorder", "replay", "minimizer", "policy", "sandbox", "dashboard", "examples", "tests") | Out-Null
    $summary.python_compileall = "passed"

    $pythonTestOutput = Invoke-Checked `
        -Label "python unittest discover" `
        -FilePath "python" `
        -Arguments @("-m", "unittest", "discover", "-s", "tests", "-v")
    $pythonTestCount = Get-PythonTestCount -Output $pythonTestOutput
    $summary.python_unittest = if ($pythonTestCount -gt 0) { "passed ($pythonTestCount tests)" } else { "passed" }

    if (-not $SkipNode) {
        $rendererDir = Join-Path $repoRoot "desktop\renderer"
        $rendererPackage = Join-Path $rendererDir "package.json"
        if (Test-NpmScript -PackageJson $rendererPackage -Script "test") {
            Invoke-Checked -Label "renderer npm test" -FilePath "npm.cmd" -Arguments @("test") -WorkingDirectory $rendererDir | Out-Null
        }
        if (Test-NpmScript -PackageJson $rendererPackage -Script "typecheck") {
            Invoke-Checked -Label "renderer npm run typecheck" -FilePath "npm.cmd" -Arguments @("run", "typecheck") -WorkingDirectory $rendererDir | Out-Null
        }
        if (Test-NpmScript -PackageJson $rendererPackage -Script "build") {
            Invoke-Checked -Label "renderer npm run build" -FilePath "npm.cmd" -Arguments @("run", "build") -WorkingDirectory $rendererDir | Out-Null
        }
        $summary.renderer = "passed"

        if (-not $SkipElectron) {
            $electronDir = Join-Path $repoRoot "desktop\electron"
            $electronPackage = Join-Path $electronDir "package.json"
            if (Test-NpmScript -PackageJson $electronPackage -Script "test") {
                Invoke-Checked -Label "electron npm test" -FilePath "npm.cmd" -Arguments @("test") -WorkingDirectory $electronDir | Out-Null
            }
            if (Test-NpmScript -PackageJson $electronPackage -Script "typecheck") {
                Invoke-Checked -Label "electron npm run typecheck" -FilePath "npm.cmd" -Arguments @("run", "typecheck") -WorkingDirectory $electronDir | Out-Null
            }
            $summary.electron = "passed"
        }
    }

    Invoke-Checked -Label "git diff --check" -FilePath "git" -Arguments @("diff", "--check") | Out-Null
    $summary.git_diff_check = "passed"

    $trackedArtifacts = & git -C $repoRoot ls-files -- "runs/windows-guard-smoke"
    if ($trackedArtifacts) {
        throw "run artifacts are tracked unexpectedly: $trackedArtifacts"
    }
    $summary.artifacts_committed = "no"

    $summary.result = "PASS"
    Write-Utf8NoBom -Path $summaryJson -Content (($summary | ConvertTo-Json -Depth 8) + "`n")

    Write-Host ""
    Write-Host "== Windows Guard smoke summary =="
    $summary.GetEnumerator() | ForEach-Object {
        Write-Host ("{0}: {1}" -f $_.Key, $_.Value)
    }

    if (-not $KeepArtifacts) {
        Assert-ChildPath -Path $runRoot -Parent $runsRoot
        Remove-Item -LiteralPath $runRoot -Recurse -Force
        Write-Host "artifacts removed: $runRoot"
    }

    exit 0
}
catch {
    Write-Utf8NoBom -Path $summaryJson -Content (($summary | ConvertTo-Json -Depth 8) + "`n")
    Write-Error -Message ($_.Exception.Message) -ErrorAction Continue
    Write-Host "artifacts retained for debugging: $runRoot"
    exit 1
}
