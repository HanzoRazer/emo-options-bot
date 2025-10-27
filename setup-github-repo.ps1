#!/usr/bin/env powershell
<#
.SYNOPSIS
    GitHub Repository Setup Script for EMO Options Bot
.DESCRIPTION
    Automates the GitHub repository creation and initial setup process
.PARAMETER Username
    Your GitHub username (required)
.PARAMETER RepoName
    Repository name (default: emo-options-bot)
.EXAMPLE
    .\setup-github-repo.ps1 -Username "johnsmith"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "emo-options-bot"
)

Write-Host "🚀 Setting up GitHub repository for EMO Options Bot..." -ForegroundColor Green
Write-Host "Username: $Username" -ForegroundColor Cyan
Write-Host "Repository: $RepoName" -ForegroundColor Cyan

# Step 1: Update CODEOWNERS file
Write-Host "`n📝 Updating CODEOWNERS file..." -ForegroundColor Yellow
$codeownersContent = @"
* @$Username
.github/workflows/* @$Username
tools/* @$Username
"@
$codeownersContent | Out-File -FilePath "CODEOWNERS" -Encoding UTF8
Write-Host "✅ CODEOWNERS updated with @$Username" -ForegroundColor Green

# Step 2: Commit the CODEOWNERS update
Write-Host "`n📦 Committing CODEOWNERS update..." -ForegroundColor Yellow
git add CODEOWNERS
git commit -m "Update CODEOWNERS with actual GitHub username: @$Username"

# Step 3: Create GitHub repository
Write-Host "`n🏗️ Creating GitHub repository..." -ForegroundColor Yellow
Write-Host "Running: gh repo create $Username/$RepoName --public" -ForegroundColor Cyan
try {
    gh repo create "$Username/$RepoName" --public --description "AI-powered options trading system with Phase 3 intelligence and order staging"
    Write-Host "✅ Repository created successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create repository. Make sure you have gh CLI installed and authenticated." -ForegroundColor Red
    Write-Host "Install: winget install GitHub.cli" -ForegroundColor Yellow
    Write-Host "Auth: gh auth login" -ForegroundColor Yellow
    exit 1
}

# Step 4: Add remote origin
Write-Host "`n🔗 Adding remote origin..." -ForegroundColor Yellow
$repoUrl = "https://github.com/$Username/$RepoName.git"
Write-Host "Repository URL: $repoUrl" -ForegroundColor Cyan
git remote add origin $repoUrl
Write-Host "✅ Remote origin added" -ForegroundColor Green

# Step 5: Rename branch to main (if needed)
Write-Host "`n🌳 Setting up main branch..." -ForegroundColor Yellow
$currentBranch = git branch --show-current
if ($currentBranch -eq "master") {
    git branch -M main
    Write-Host "✅ Branch renamed from master to main" -ForegroundColor Green
} else {
    Write-Host "✅ Already on main branch" -ForegroundColor Green
}

# Step 6: Push everything including tags
Write-Host "`n⬆️ Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "Pushing all commits and tags..." -ForegroundColor Cyan
git push -u origin main --tags
Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green

# Step 7: Display success information
Write-Host "`n🎉 GitHub Repository Setup Complete!" -ForegroundColor Green
Write-Host "Repository URL: https://github.com/$Username/$RepoName" -ForegroundColor Cyan
Write-Host "CI/CD Status: https://github.com/$Username/$RepoName/actions" -ForegroundColor Cyan

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Visit your repository: https://github.com/$Username/$RepoName" -ForegroundColor White
Write-Host "2. Check CI/CD pipeline in Actions tab" -ForegroundColor White
Write-Host "3. Configure branch protection rules (optional)" -ForegroundColor White
Write-Host "4. Create your first issue or PR" -ForegroundColor White

Write-Host "`n🔄 The CI/CD pipeline will automatically run and test:" -ForegroundColor Cyan
Write-Host "  ✅ Dependency installation" -ForegroundColor White
Write-Host "  ✅ Code linting (ruff)" -ForegroundColor White
Write-Host "  ✅ Type checking (mypy)" -ForegroundColor White
Write-Host "  ✅ Unit tests (pytest)" -ForegroundColor White
Write-Host "  ✅ Phase 3 smoke tests" -ForegroundColor White

Write-Host "`n🚀 Your EMO Options Bot is now live on GitHub!" -ForegroundColor Green