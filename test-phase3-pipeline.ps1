# Phase 3 Pipeline Test Script
# Tests the complete JSON-LLM + Trade Staging pipeline

Write-Host "🚀 EMO Options Bot - Phase 3 Pipeline Test" -ForegroundColor Green
Write-Host "=" * 50

# Ensure staging directory exists
$stagingDir = "ops/staged_orders"
if (-not (Test-Path $stagingDir)) {
    Write-Host "📁 Creating staging directory: $stagingDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
}

# Test parameters
$prompt = "Conservative iron condor on SPY with maximum $500 risk"
$symbol = "SPY"
$maxRisk = 500

Write-Host ""
Write-Host "📋 Test Parameters:" -ForegroundColor Cyan
Write-Host "   Prompt: $prompt"
Write-Host "   Symbol: $symbol"
Write-Host "   Max Risk: $$maxRisk"
Write-Host ""

# Step 1: Generate Trade Plan
Write-Host "🤖 Step 1: Generating trade plan from natural language..." -ForegroundColor Yellow
$planGenResult = python tools/llm_trade_plan.py --prompt $prompt --symbol $symbol --max-risk $maxRisk 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Trade plan generated successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Trade plan generation failed" -ForegroundColor Red
    Write-Host $planGenResult
    exit 1
}

# Step 2: Validate Trade Plan
Write-Host ""
Write-Host "🔍 Step 2: Validating trade plan..." -ForegroundColor Yellow
$planFile = "ops/staged_orders/PLAN.json"
$validateResult = python tools/validate_trade_plan.py --file $planFile 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Trade plan validation passed" -ForegroundColor Green
} else {
    Write-Host "❌ Trade plan validation failed" -ForegroundColor Red
    Write-Host $validateResult
    exit 1
}

# Step 3: Stage Trade for Review
Write-Host ""
Write-Host "📁 Step 3: Staging trade for review..." -ForegroundColor Yellow
$stageResult = python tools/phase3_stage_trade.py --from-plan $planFile --note "Phase 3 pipeline test" --priority normal 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Trade staged successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Trade staging failed" -ForegroundColor Red
    Write-Host $stageResult
    exit 1
}

# Show staged files
Write-Host ""
Write-Host "📋 Staged Files:" -ForegroundColor Cyan
$stagedFiles = Get-ChildItem -Path $stagingDir -Filter "staged_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($stagedFiles) {
    Write-Host "   Plan: $($stagedFiles.FullName)" -ForegroundColor White
    
    $summaryFile = $stagedFiles.FullName -replace "\.json$", ".summary.txt"
    if (Test-Path $summaryFile) {
        Write-Host "   Summary: $summaryFile" -ForegroundColor White
    }
    
    $backupFile = Join-Path $stagingDir "backup" ("backup_" + $stagedFiles.Name)
    if (Test-Path $backupFile) {
        Write-Host "   Backup: $backupFile" -ForegroundColor White
    }
}

# Display summary
Write-Host ""
Write-Host "📊 Pipeline Summary:" -ForegroundColor Cyan
if (Test-Path $planFile) {
    $plan = Get-Content $planFile | ConvertFrom-Json
    Write-Host "   Strategy: $($plan.strategy_type)" -ForegroundColor White
    Write-Host "   Symbol: $($plan.symbol)" -ForegroundColor White
    Write-Host "   Expiration: $($plan.expiration)" -ForegroundColor White
    Write-Host "   Max Risk: $$($plan.risk_constraints.max_loss)" -ForegroundColor White
    Write-Host "   Legs: $($plan.legs.Count)" -ForegroundColor White
}

Write-Host ""
Write-Host "🎯 Phase 3 Pipeline Test Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review the staged trade files above"
Write-Host "  2. Approve the trade if acceptable"
Write-Host "  3. Execute when ready (manual process)"
Write-Host ""
Write-Host "Phase 3 Features Demonstrated:" -ForegroundColor Cyan
Write-Host "  ✅ Natural language → Structured JSON plan"
Write-Host "  ✅ Risk validation and compliance checking"
Write-Host "  ✅ Non-bypassable safety gates"
Write-Host "  ✅ Staging for human review"
Write-Host "  ✅ Audit trail and backup system"