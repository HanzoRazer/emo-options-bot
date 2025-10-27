<#  tools/repo_check.ps1
    Repo health checker for EMO Options Bot

    What it checks:
    - Inside a git repo, branch, clean working tree, ahead/behind status
    - origin remote presence and URL
    - tags exist, semver-ish format, shows latest
    - required files exist (README, LICENSE, .gitignore, CI, CODEOWNERS, templates, envs)
    - Python smoke test (tools/release_check.py --fast) if present
    - Optional GitHub checks via `gh` (visibility, workflows, recent runs)

    Usage:
      pwsh -File tools/repo_check.ps1
      pwsh -File tools/repo_check.ps1 -ExpectedRemote "https://github.com/HanzoRazer/emo-options-bot.git" -ExpectedBranch "main" -Strict
#>

[CmdletBinding()]
param(
  [string]$ExpectedRemote = "",
  [string]$ExpectedBranch = "main",
  [switch]$Strict,             # Fail build on WARNs too
  [switch]$NoGh,               # Skip GitHub CLI checks
  [switch]$VerboseOutput       # Extra diagnostics
)

$ErrorActionPreference = "Stop"

function Write-Section($t){ Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function Write-OK($t){ Write-Host "  ✔ $t" -ForegroundColor Green }
function Write-Warn($t){ Write-Host "  ! $t" -ForegroundColor Yellow }
function Write-Err($t){ Write-Host "  ✖ $t" -ForegroundColor Red }
function Has-Cmd($name){ $null -ne (Get-Command $name -ErrorAction SilentlyContinue) }

$FAILS = 0
$WARNS = 0
function Fail($msg){ Write-Err $msg; $script:FAILS++ }
function Warn($msg){ Write-Warn $msg; $script:WARNS++ }

Write-Section "Basics"

if (-not (Has-Cmd git)) { Fail "git is not available in PATH"; exit 2 }
if (-not (Has-Cmd python) -and -not (Has-Cmd py)) { Warn "Python not found in PATH (smoke tests may be skipped)" }

# Ensure we're inside a repo
try {
  $inside = git rev-parse --is-inside-work-tree 2>$null
  if ($inside -ne "true") { Fail "Not inside a git repository"; exit 2 }
  Write-OK "Inside a git repository"
} catch { Fail "git rev-parse failed: $($_.Exception.Message)"; exit 2 }

# Branch / status
try {
  $branch = (git rev-parse --abbrev-ref HEAD).Trim()
  Write-OK "Current branch: $branch"
  if ($ExpectedBranch -and $branch -ne $ExpectedBranch) { Warn "Expected branch '$ExpectedBranch' but on '$branch'" }

  $short = (git status -sb)
  Write-Host ($short | Out-String).Trim()
  if ($short -match "ahead|behind") { Warn "Branch diverged (ahead/behind). Consider syncing with remote." }
  if (-not (git diff --quiet) -or -not (git diff --cached --quiet)) {
    Warn "Working tree not clean (uncommitted changes)"
  } else {
    Write-OK "Working tree clean"
  }
} catch { Fail "git status failed: $($_.Exception.Message)" }

Write-Section "Remotes"
try {
  $remotes = git remote -v
  if (-not $remotes) { Fail "No remotes configured (git remote -v is empty)" }
  else {
    Write-Host ($remotes | Out-String).Trim()
    $originLine = ($remotes | Select-String "origin\s+(.+)\s+\(push\)").Matches.Value
    if (-not $originLine) { Warn "No 'origin' push remote found" }
    else {
      $originUrl = ($originLine -split "\s+")[1]
      Write-OK "origin remote: $originUrl"
      if ($ExpectedRemote -and $originUrl -ne $ExpectedRemote) { Warn "Expected remote '$ExpectedRemote' but found '$originUrl'" }
    }
  }
} catch { Fail "git remote -v failed: $($_.Exception.Message)" }

Write-Section "Tags"
try {
  $tags = (git tag) | Sort-Object
  if (-not $tags) { Warn "No tags found. Use tools/git_tag_helper.ps1 to create semver tags." }
  else {
    $latest = (git tag --list --sort=-creatordate | Select-Object -First 1)
    Write-OK "Latest tag: $latest"
    $bad = @()
    foreach ($t in $tags) {
      if ($t -notmatch '^v\d+\.\d+\.\d+(-[A-Za-z0-9\.-]+)?$') { $bad += $t }
    }
    if ($bad.Count -gt 0) { Warn "Non-semver-ish tags detected: $($bad -join ', ')" }
  }
} catch { Fail "git tag enumeration failed: $($_.Exception.Message)" }

Write-Section "Required Files"
$mustExist = @(
  "README.md",
  "LICENSE",
  ".gitignore",
  ".env.example",
  "CODEOWNERS",
  ".github/workflows/ci.yml",
  ".github/ISSUE_TEMPLATE/bug_report.yml",
  "tools/release_check.py",   # Phase 3 smoke tests
  "tools/git_tag_helper.ps1", # Release helper
  "tools/repo_check.ps1"      # This script
)

foreach ($f in $mustExist) {
  if (Test-Path $f) { Write-OK "$f" } else { Warn "Missing: $f" }
}

Write-Section "Python/CI Config Hints"
$niceToHave = @(
  "requirements.txt",
  "requirements-ml.txt",
  "pyproject.toml",
  "mypy.ini",
  "ruff.toml"
)
foreach ($f in $niceToHave) {
  if (Test-Path $f) { Write-OK "$f" } else { Write-Host "  · (optional) $f" }
}

Write-Section "Phase 3 Smoke Test"
$pyExe = if (Has-Cmd python) { "python" } elseif (Has-Cmd py) { "py -3" } else { $null }
if ($pyExe -and (Test-Path "tools/release_check.py")) {
  try {
    # Try with --fast flag first, fall back to basic run
    try {
      & $pyExe tools/release_check.py --fast 2>$null
      if ($LASTEXITCODE -eq 0) { Write-OK "release_check.py --fast passed" }
      else { throw "Fast check failed" }
    } catch {
      # Fallback to basic release check
      & $pyExe tools/release_check.py
      if ($LASTEXITCODE -eq 0) { Write-OK "release_check.py passed" }
      else { Fail "release_check.py failed with exit $LASTEXITCODE" }
    }
  } catch {
    Fail "Failed to run release_check.py: $($_.Exception.Message)"
  }
} else {
  Warn "Skipping smoke test (python or tools/release_check.py not found)"
}

if (-not $NoGh -and (Has-Cmd gh)) {
  Write-Section "GitHub Status (via gh)"
  try {
    $origin = (git remote get-url origin 2>$null)
    if ($origin -and $origin -match "github.com[:/](.+?)(\.git)?$") {
      $repoFull = $Matches[1]
      Write-Host "  Repo: $repoFull"
      
      # Basic repo info
      try {
        $repoInfo = gh repo view $repoFull --json name,visibility,defaultBranchRef,description 2>$null | ConvertFrom-Json
        Write-Host "  $($repoInfo.name) ($($repoInfo.visibility)), default branch: $($repoInfo.defaultBranchRef.name)"
        if ($repoInfo.description) { Write-Host "  $($repoInfo.description)" }
        Write-OK "Repository accessible via GitHub CLI"
      } catch {
        Warn "Could not fetch repository info via gh CLI"
      }
      
      # Workflow status
      try {
        gh workflow list --repo $repoFull --limit 3 2>$null | Out-Host
        Write-OK "Workflows listed"
      } catch {
        Warn "Could not list workflows"
      }
      
      # Recent runs
      try {
        gh run list --repo $repoFull --limit 5 2>$null | Out-Host
        Write-OK "Recent runs listed"
      } catch {
        Warn "Could not list recent runs"
      }
    } else {
      Warn "origin is not GitHub or unreachable; skipping gh checks"
    }
  } catch {
    Warn "GitHub CLI inspection failed: $($_.Exception.Message)"
  }
} else {
  Write-Host "Skipping GitHub CLI checks (use -NoGh to silence or install gh)"
}

Write-Section "Summary"
if ($FAILS -gt 0) { Write-Err "FAILS: $FAILS" } else { Write-OK "FAILS: 0" }
if ($WARNS -gt 0) { Write-Warn "WARNS: $WARNS" } else { Write-OK "WARNS: 0" }

if ($FAILS -gt 0 -or ($Strict -and $WARNS -gt 0)) {
  Write-Host "`nResult: NOT OK" -ForegroundColor Red
  exit 1
} else {
  Write-Host "`nResult: OK" -ForegroundColor Green
  exit 0
}