# Phase 3 Release Check - PowerShell Runner
# Validates production readiness for Phase 3 completion
# Exit codes: 0=ready, 1=warnings, 2=failures

param(
    [string]$WorkspaceRoot = (Get-Location),
    [switch]$Verbose = $false,
    [switch]$SkipPython = $false,
    [switch]$Help
)

function Show-Usage {
    Write-Host @"
Phase 3 Release Check - PowerShell Runner

USAGE:
    .\run_release_check.ps1 [OPTIONS]

OPTIONS:
    -WorkspaceRoot <path>    Set workspace root directory (default: current)
    -Verbose                 Enable detailed output
    -SkipPython             Skip Python environment checks
    -Help                   Show this help message

EXAMPLES:
    .\run_release_check.ps1
    .\run_release_check.ps1 -Verbose
    .\run_release_check.ps1 -WorkspaceRoot "C:\path\to\workspace"

EXIT CODES:
    0 - Production ready (all checks passed)
    1 - Warnings detected (review recommended)
    2 - Critical failures (not ready for production)

"@
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host " $Message" -ForegroundColor White
    Write-Host "============================================" -ForegroundColor Cyan
}

function Write-Status {
    param(
        [string]$Status,
        [string]$Message
    )
    $color = switch ($Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
        "INFO" { "Cyan" }
        default { "White" }
    }
    Write-Host "[$Status] $Message" -ForegroundColor $color
}

function Test-PythonAvailable {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "PASS" "Python available: $pythonVersion"
            return $true
        }
    } catch {}
    
    Write-Status "FAIL" "Python not found in PATH"
    return $false
}

function Test-VirtualEnvironment {
    if ($env:VIRTUAL_ENV) {
        Write-Status "PASS" "Virtual environment active: $env:VIRTUAL_ENV"
        return $true
    }
    
    # Check for common venv directories
    $venvPaths = @("venv", ".venv", "env", ".env")
    foreach ($venvPath in $venvPaths) {
        $fullPath = Join-Path $WorkspaceRoot $venvPath
        if (Test-Path $fullPath) {
            Write-Status "WARN" "Virtual environment found but not activated: $fullPath"
            return $false
        }
    }
    
    Write-Status "WARN" "No virtual environment detected"
    return $false
}

function Test-RequiredFiles {
    $requiredFiles = @(
        "tools\phase3_release_check.py",
        "src\phase3\schemas.py",
        "src\phase3\orchestrator.py",
        "src\phase3\synthesizer.py",
        "src\phase3\gates.py",
        "scripts\stage_order_cli.py"
    )
    
    $allFound = $true
    foreach ($file in $requiredFiles) {
        $fullPath = Join-Path $WorkspaceRoot $file
        if (Test-Path $fullPath) {
            if ($Verbose) {
                Write-Status "PASS" "Found: $file"
            }
        } else {
            Write-Status "FAIL" "Missing: $file"
            $allFound = $false
        }
    }
    
    if ($allFound) {
        Write-Status "PASS" "All required Phase 3 files present"
    }
    
    return $allFound
}

# Main execution
if ($Help) {
    Show-Usage
    exit 0
}

Write-Header "Phase 3 Release Check - PowerShell Runner"
Write-Host "Workspace: $WorkspaceRoot" -ForegroundColor Gray
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

# Change to workspace directory
if (-not (Test-Path $WorkspaceRoot)) {
    Write-Status "FAIL" "Workspace directory not found: $WorkspaceRoot"
    exit 2
}

Set-Location $WorkspaceRoot
Write-Status "INFO" "Changed to workspace directory"

$warnings = 0
$failures = 0

# Pre-flight checks
Write-Header "Pre-flight Checks"

if (-not $SkipPython) {
    if (-not (Test-PythonAvailable)) {
        $failures++
    }
    
    if (-not (Test-VirtualEnvironment)) {
        $warnings++
    }
}

if (-not (Test-RequiredFiles)) {
    $failures++
}

# If pre-flight failed, exit early
if ($failures -gt 0) {
    Write-Header "Pre-flight Failed"
    Write-Status "FAIL" "Cannot proceed with release check ($failures failures)"
    exit 2
}

# Run the main Python release checker
Write-Header "Running Phase 3 Release Check"

$pythonArgs = @("tools\phase3_release_check.py")
if ($Verbose) {
    $pythonArgs += "--verbose"
}

try {
    Write-Status "INFO" "Executing: python $($pythonArgs -join ' ')"
    & python $pythonArgs
    $exitCode = $LASTEXITCODE
    
    Write-Header "Release Check Complete"
    
    switch ($exitCode) {
        0 {
            Write-Status "PASS" "Production ready! All checks passed."
            Write-Host ""
            Write-Host "🚀 Phase 3 is ready for production deployment!" -ForegroundColor Green
        }
        1 {
            Write-Status "WARN" "Warnings detected. Review recommended."
            Write-Host ""
            Write-Host "⚠️  Phase 3 has warnings but may be deployable." -ForegroundColor Yellow
            $warnings++
        }
        2 {
            Write-Status "FAIL" "Critical failures detected. Not ready for production."
            Write-Host ""
            Write-Host "❌ Phase 3 is not ready for production deployment." -ForegroundColor Red
            $failures++
        }
        default {
            Write-Status "FAIL" "Unexpected exit code: $exitCode"
            $failures++
        }
    }
    
    # Summary
    Write-Host ""
    Write-Host "Summary: $failures failures, $warnings warnings" -ForegroundColor Gray
    
    # Final exit code
    if ($failures -gt 0) {
        exit 2
    } elseif ($warnings -gt 0) {
        exit 1
    } else {
        exit 0
    }
    
} catch {
    Write-Status "FAIL" "Failed to run release check: $($_.Exception.Message)"
    exit 2
}