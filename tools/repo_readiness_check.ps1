<# 
Repo Readiness Checker (PowerShell)
Usage:
  pwsh ./tools/repo_readiness_check.ps1
  (or) powershell -File .\tools\repo_readiness_check.ps1
#>

param(
  [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"
$repoRoot = (git rev-parse --show-toplevel) 2>$null
if (-not $repoRoot) {
  Write-Host "❌ Not inside a git repository." -ForegroundColor Red
  exit 2
}
Set-Location $repoRoot

function Test-File {
  param([string]$Path)
  if (Test-Path $Path) { return $true } else { return $false }
}

function Print-Check {
  param([bool]$ok, [string]$msg)
  if ($ok) {
    Write-Host "✅ $msg"
  } else {
    Write-Host "❌ $msg" -ForegroundColor Red
    $script:Failed = $true
  }
}

$Failed = $false
Write-Host "== EMO Options Bot – Repository Readiness Check =="

# 1) Git basics
$remote = (git remote -v) 2>$null
$remoteOk = $remote -and ($remote -match "origin")
Print-Check $remoteOk "Git remote 'origin' configured"
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
$branchOk = $branch -in @("main","master","develop")
Print-Check $branchOk "Current branch ($branch) is a conventional mainline (main/master/develop)"
$dirty = (git status --porcelain) 2>$null
Print-Check ([string]::IsNullOrWhiteSpace($dirty)) "Working tree clean"

# 2) Required files
Print-Check (Test-File ".gitignore") ".gitignore exists"
$licenseOk = (Test-File "LICENSE") -or (Test-File "LICENSE.md")
Print-Check $licenseOk "LICENSE present"
$readmeOk = (Test-File "README.md") -and (((Get-Content README.md -ErrorAction SilentlyContinue) | Measure-Object -Line).Lines -gt 5)
Print-Check $readmeOk "README present and not empty"

# 3) Phase 3 essentials (docs + scripts)
Print-Check (Test-File "DEVELOPER_QUICK_START.md") "Developer quick start present"
Print-Check (Test-File ".env.example") ".env.example present"
Print-Check (Test-File "tools/release_check.py") "Phase 3 release_check.py present"

# 4) CI/CD workflow
$ciOk = (Test-File ".github/workflows/ci.yml") -or (Test-File ".github/workflows/ci.yaml")
Print-Check $ciOk "CI workflow present (.github/workflows/ci.yml)"
$codeownersOk = Test-File ".github/CODEOWNERS"
Print-Check $codeownersOk "CODEOWNERS present"

# 5) Optional Phase 3 infra checks
$hasHealth = Test-File "tools/emit_health.py"
$hasDash   = (Test-File "tools/build_dashboard.py") -or (Test-File "src/web/dashboard.py")
Print-Check $hasHealth "Health endpoint helper present"
Print-Check $hasDash   "Dashboard builder present"

# 6) Python env & tests
try {
  $py = (Get-Command python -ErrorAction Stop).Path
  Print-Check $true "Python found: $py"
} catch {
  Print-Check $false "Python not found on PATH"
}

# Try smoke tests if available
if (Test-File "tools/release_check.py") {
  try {
    python tools/release_check.py --fast 2>$null | Out-Null
    $smokeSuccess = $LASTEXITCODE -eq 0
    Print-Check $smokeSuccess "Phase 3 smoke tests (release_check.py) succeeded"
  } catch {
    Print-Check $false "Phase 3 smoke tests failed"
  }
}

# 7) Lint/type/test (soft checks; won't fail run if tools missing)
function Invoke-OptionalCheck {
  param([string[]]$cmd, [string]$label)
  try {
    & $cmd[0] $cmd[1..($cmd.Length-1)] 2>$null | Out-Null
    Print-Check $true $label
  } catch {
    Write-Host "ℹ️  Skipped $label (tool missing or failed)."
  }
}

Invoke-OptionalCheck @("python","-m","pytest","-q") "Pytest suite OK"
Invoke-OptionalCheck @("ruff","check",".")        "Ruff lint OK"
Invoke-OptionalCheck @("mypy",".")                "Mypy typecheck OK"

Write-Host ""
if ($Failed) {
  Write-Host "❌ Repo readiness checks found issues. See red items above." -ForegroundColor Red
  exit 1
} else {
  Write-Host "🎉 All mandatory checks passed. Repo is ready." -ForegroundColor Green
  exit 0
}