#!/usr/bin/env pwsh
# Enhanced LLM Routing Test Script with Robustness
# Tests the complete LLM routing pipeline with monitoring and health checks

Write-Host "=== EMO Options Bot - Enhanced LLM Routing Test ===" -ForegroundColor Cyan
Write-Host "Testing Phase 3 LLM routing pipeline with robustness features..." -ForegroundColor Yellow
Write-Host ""

# Configuration
$TestTimeout = 180  # 3 minutes
$PlanDirectory = "ops/llm_plans"
$StagedDirectory = "ops/staged_orders"
$LogDirectory = "logs"
$HealthCheckInterval = 5  # seconds

# Function to perform pre-flight checks
function Invoke-PreFlightChecks {
    Write-Host "🔍 Performing pre-flight checks..." -ForegroundColor Green
    
    # Check Python environment
    try {
        $PythonVersion = python --version 2>&1
        Write-Host "✅ Python: $PythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python not found or not accessible" -ForegroundColor Red
        return $false
    }
    
    # Check required directories
    $RequiredDirs = @($PlanDirectory, $StagedDirectory, $LogDirectory, "$StagedDirectory/backup")
    foreach ($Dir in $RequiredDirs) {
        if (!(Test-Path $Dir)) {
            Write-Host "📁 Creating directory: $Dir" -ForegroundColor Blue
            New-Item -ItemType Directory -Force -Path $Dir | Out-Null
        }
        Write-Host "✅ Directory exists: $Dir" -ForegroundColor Green
    }
    
    # Check critical files
    $CriticalFiles = @(
        "exec/plan_router.py",
        "tools/llm_trade_plan.py",
        "tools/validate_trade_plan.py",
        "tools/phase3_stage_trade.py"
    )
    
    $MissingFiles = @()
    foreach ($File in $CriticalFiles) {
        if (Test-Path $File) {
            Write-Host "✅ File exists: $File" -ForegroundColor Green
        } else {
            Write-Host "❌ Missing file: $File" -ForegroundColor Red
            $MissingFiles += $File
        }
    }
    
    if ($MissingFiles.Count -gt 0) {
        Write-Host "❌ Pre-flight check failed: Missing critical files" -ForegroundColor Red
        return $false
    }
    
    # Check for robust test runner
    if (Test-Path "tools/robust_test_runner.py") {
        Write-Host "✅ Robust test runner available" -ForegroundColor Green
    }
    
    Write-Host "✅ Pre-flight checks completed" -ForegroundColor Green
    Write-Host ""
    return $true
}

# Function to safely kill processes
function Stop-ProcessSafely {
    param($ProcessName, $TimeoutSeconds = 10)
    
    $Processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($Processes) {
        Write-Host "🛑 Stopping $($Processes.Count) $ProcessName process(es)..." -ForegroundColor Yellow
        
        foreach ($Process in $Processes) {
            try {
                $Process.CloseMainWindow()
                if (!$Process.WaitForExit($TimeoutSeconds * 1000)) {
                    Write-Host "⚡ Force killing process $($Process.Id)" -ForegroundColor Red
                    $Process.Kill()
                }
                Write-Host "✅ Process $($Process.Id) stopped" -ForegroundColor Green
            } catch {
                Write-Host "❌ Failed to stop process $($Process.Id): $_" -ForegroundColor Red
            }
        }
    }
}

# Perform pre-flight checks
if (!(Invoke-PreFlightChecks)) {
    Write-Host "❌ Pre-flight checks failed. Exiting." -ForegroundColor Red
    exit 1
}

# Create test trade plan with enhanced metadata
$TestRequestId = "test_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$TestPlan = @{
    "request_id" = $TestRequestId
    "description" = "Buy 1 SPY call option at the money expiring next Friday for robustness test"
    "risk_tolerance" = "moderate"
    "max_loss" = 500
    "target_profit" = 1000
    "timestamp" = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    "user_id" = "test_user_robust"
    "priority" = "normal"
    "test_metadata" = @{
        "test_type" = "robustness"
        "test_version" = "2.0"
        "expected_processing_time" = 30
    }
} | ConvertTo-Json -Depth 10

# Save test plan
$TestPlanFile = "$PlanDirectory/test_plan_$TestRequestId.json"
$TestPlan | Out-File -FilePath $TestPlanFile -Encoding UTF8

Write-Host "� Created enhanced test plan: $TestPlanFile" -ForegroundColor Blue
Write-Host "Test plan content:" -ForegroundColor Gray
Write-Host $TestPlan -ForegroundColor Gray
Write-Host ""

# Clean up any existing Python processes
Stop-ProcessSafely -ProcessName "python"
Start-Sleep -Seconds 2

# Start enhanced LLM routing monitor
Write-Host "� Starting enhanced LLM routing monitor..." -ForegroundColor Green

try {
    # Use robust test runner if available
    if (Test-Path "tools/robust_test_runner.py") {
        Write-Host "Using robust test runner..." -ForegroundColor Blue
        $Process = Start-Process -FilePath "python" -ArgumentList "tools/robust_test_runner.py --llm-routing --timeout $TestTimeout" -NoNewWindow -PassThru -RedirectStandardOutput "logs/routing_output.log" -RedirectStandardError "logs/routing_error.log"
    } else {
        Write-Host "Using direct plan router..." -ForegroundColor Blue  
        $Process = Start-Process -FilePath "python" -ArgumentList "exec/plan_router.py" -NoNewWindow -PassThru -RedirectStandardOutput "logs/routing_output.log" -RedirectStandardError "logs/routing_error.log"
    }
    
    $StartTime = Get-Date
    $TimeoutReached = $false
    
    Write-Host "Process started with ID: $($Process.Id)" -ForegroundColor Green
    
    # Monitor process with enhanced feedback
    do {
        Start-Sleep -Seconds 5
        $ElapsedTime = (Get-Date) - $StartTime
        
        Write-Host "⏳ Monitoring: $([math]::Round($ElapsedTime.TotalSeconds, 1))s elapsed..." -ForegroundColor Cyan
        
        if ($ElapsedTime.TotalSeconds -gt $TestTimeout) {
            $TimeoutReached = $true
            Write-Host "⚠️ TIMEOUT: Process exceeded $TestTimeout seconds" -ForegroundColor Red
            if (!$Process.HasExited) {
                $Process.Kill()
                $Process.WaitForExit(5000)
            }
            break
        }
        
        if ($Process.HasExited) {
            Write-Host "✅ Process completed with exit code: $($Process.ExitCode)" -ForegroundColor Green
            break
        }
        
    } while ($true)
    
    # Collect results
    $ProcessResult = @{
        ExitCode = if ($TimeoutReached) { -1 } else { $Process.ExitCode }
        ElapsedTime = $ElapsedTime.TotalSeconds
        TimedOut = $TimeoutReached
        ProcessId = $Process.Id
    }
    
} catch {
    Write-Host "❌ ERROR: Failed to start or monitor process: $_" -ForegroundColor Red
    $ProcessResult = @{
        ExitCode = -999
        ElapsedTime = 0
        TimedOut = $false
        Error = $_.Exception.Message
    }
}

Write-Host ""
Write-Host "=== Enhanced Test Results ===" -ForegroundColor Cyan

# Display process results
if ($ProcessResult) {
    Write-Host "🔄 Process Results:" -ForegroundColor Green
    Write-Host "  Process ID: $($ProcessResult.ProcessId)" -ForegroundColor Blue
    Write-Host "  Exit Code: $($ProcessResult.ExitCode)" -ForegroundColor $(if ($ProcessResult.ExitCode -eq 0) { "Green" } else { "Red" })
    Write-Host "  Elapsed Time: $([math]::Round($ProcessResult.ElapsedTime, 2))s" -ForegroundColor Blue
    Write-Host "  Timed Out: $($ProcessResult.TimedOut)" -ForegroundColor $(if ($ProcessResult.TimedOut) { "Red" } else { "Green" })
    
    if ($ProcessResult.Error) {
        Write-Host "  Error: $($ProcessResult.Error)" -ForegroundColor Red
    }
}

# Check output files with enhanced details
Write-Host ""
Write-Host "� Checking output files..." -ForegroundColor Yellow

$OutputFiles = @(
    "logs/routing_output.log",
    "logs/routing_error.log"
)

foreach ($OutputFile in $OutputFiles) {
    if (Test-Path $OutputFile) {
        $Content = Get-Content $OutputFile -Raw -ErrorAction SilentlyContinue
        if ($Content -and $Content.Trim()) {
            Write-Host "=== $OutputFile ===" -ForegroundColor Blue
            # Truncate very long output
            if ($Content.Length -gt 2000) {
                $Content = $Content.Substring(0, 2000) + "`n... (truncated)"
            }
            Write-Host $Content -ForegroundColor Gray
        } else {
            Write-Host "📄 $OutputFile is empty" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ $OutputFile not found" -ForegroundColor Red
    }
}
# Enhanced staged order checking
Write-Host ""
Write-Host "� Checking for staged orders..." -ForegroundColor Yellow
$StagedFiles = Get-ChildItem -Path $StagedDirectory -Filter "*.json" | Where-Object { $_.Name -ne "backup" }

if ($StagedFiles.Count -gt 0) {
    Write-Host "✅ Found $($StagedFiles.Count) staged order(s):" -ForegroundColor Green
    foreach ($StagedFile in $StagedFiles) {
        try {
            $StagedContent = Get-Content $StagedFile.FullName | ConvertFrom-Json
            Write-Host "  📋 $($StagedFile.Name)" -ForegroundColor Blue
            Write-Host "    Strategy: $($StagedContent.strategy)" -ForegroundColor Gray
            Write-Host "    Symbol: $($StagedContent.symbol)" -ForegroundColor Gray
            Write-Host "    Status: $($StagedContent.status)" -ForegroundColor Gray
            if ($StagedContent.request_id -eq $TestRequestId) {
                Write-Host "    ✅ Matches test request ID" -ForegroundColor Green
            }
        } catch {
            Write-Host "  ⚠️  Could not parse: $($StagedFile.Name)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "📭 No staged orders found" -ForegroundColor Yellow
}

# Check for processed plans
Write-Host ""
Write-Host "🔍 Checking plan processing..." -ForegroundColor Yellow
$ProcessedPlans = Get-ChildItem -Path $PlanDirectory -Filter "*.processed" -ErrorAction SilentlyContinue
$OriginalPlan = Get-ChildItem -Path $PlanDirectory -Filter "*$TestRequestId*" -ErrorAction SilentlyContinue

if ($ProcessedPlans.Count -gt 0) {
    Write-Host "✅ Found $($ProcessedPlans.Count) processed plan(s)" -ForegroundColor Green
    $ProcessedPlans | ForEach-Object { Write-Host "  📋 $($_.Name)" -ForegroundColor Blue }
} else {
    Write-Host "📭 No processed plans found" -ForegroundColor Yellow
}

if ($OriginalPlan) {
    Write-Host "📋 Original test plan still exists: $($OriginalPlan.Name)" -ForegroundColor Blue
}

# Enhanced final assessment
Write-Host ""
Write-Host "=== Enhanced Final Assessment ===" -ForegroundColor Cyan

$TestResults = @{
    Passed = $false
    Score = 0
    MaxScore = 100
    Issues = @()
    Successes = @()
}

# Process execution (40 points)
if ($ProcessResult -and $ProcessResult.ExitCode -eq 0 -and !$ProcessResult.TimedOut) {
    $TestResults.Score += 40
    $TestResults.Successes += "Process executed successfully"
} elseif ($ProcessResult -and $ProcessResult.TimedOut) {
    $TestResults.Issues += "Process timed out after $TestTimeout seconds"
} else {
    $TestResults.Issues += "Process failed or returned error code"
}

# Output generation (30 points)
if ($StagedFiles.Count -gt 0) {
    $TestResults.Score += 20
    $TestResults.Successes += "Staged orders generated"
    
    # Check if staged order matches test request
    $MatchingStaged = $StagedFiles | Where-Object { 
        try {
            $Content = Get-Content $_.FullName | ConvertFrom-Json
            return $Content.request_id -eq $TestRequestId
        } catch { return $false }
    }
    
    if ($MatchingStaged) {
        $TestResults.Score += 10
        $TestResults.Successes += "Staged order matches test request"
    }
}

if ($ProcessedPlans.Count -gt 0) {
    $TestResults.Score += 10
    $TestResults.Successes += "Plans marked as processed"
}

# Error handling (20 points)  
if ($ProcessResult -and !$ProcessResult.Error) {
    $TestResults.Score += 10
    $TestResults.Successes += "No errors reported"
    
    # Check log files for errors
    $ErrorLogContent = ""
    if (Test-Path "logs/routing_error.log") {
        $ErrorLogContent = Get-Content "logs/routing_error.log" -Raw -ErrorAction SilentlyContinue
    }
    
    if (!$ErrorLogContent -or !$ErrorLogContent.Trim()) {
        $TestResults.Score += 10
        $TestResults.Successes += "Clean execution with no error logs"
    } else {
        $TestResults.Score += 5
        $TestResults.Issues += "Some errors in logs"
    }
} else {
    $TestResults.Issues += "Execution errors reported"
}

# Performance (10 points)
if ($ProcessResult -and $ProcessResult.ElapsedTime -lt 60) {
    $TestResults.Score += 10
    $TestResults.Successes += "Fast execution (< 60s)"
} elseif ($ProcessResult -and $ProcessResult.ElapsedTime -lt 120) {
    $TestResults.Score += 5
    $TestResults.Issues += "Slow execution (> 60s)"
} else {
    $TestResults.Issues += "Very slow execution (> 120s)"
}

# Determine overall result
$TestResults.Passed = $TestResults.Score -ge 70

# Display results
Write-Host "📊 Test Score: $($TestResults.Score)/$($TestResults.MaxScore) ($([math]::Round(($TestResults.Score / $TestResults.MaxScore) * 100, 1))%)" -ForegroundColor $(if ($TestResults.Passed) { "Green" } else { "Red" })

if ($TestResults.Successes.Count -gt 0) {
    Write-Host "✅ Successes:" -ForegroundColor Green
    $TestResults.Successes | ForEach-Object { Write-Host "  • $_" -ForegroundColor Green }
}

if ($TestResults.Issues.Count -gt 0) {
    Write-Host "⚠️  Issues:" -ForegroundColor Yellow
    $TestResults.Issues | ForEach-Object { Write-Host "  • $_" -ForegroundColor Red }
}

if ($TestResults.Passed) {
    Write-Host "🎉 OVERALL RESULT: TEST PASSED" -ForegroundColor Green
} else {
    Write-Host "❌ OVERALL RESULT: TEST FAILED" -ForegroundColor Red
}

Write-Host ""
Write-Host "📅 Test completed at $(Get-Date)" -ForegroundColor Cyan

# Enhanced cleanup with verification
Write-Host ""
Write-Host "🧹 Performing cleanup..." -ForegroundColor Yellow

# Clean up test files
try {
    if (Test-Path $TestPlanFile) {
        Remove-Item $TestPlanFile -ErrorAction SilentlyContinue
        Write-Host "✅ Test plan file removed" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Could not remove test plan file: $_" -ForegroundColor Yellow
}

# Stop any remaining Python processes
Stop-ProcessSafely -ProcessName "python"

# Final status
Write-Host ""
if ($TestResults.Passed) {
    Write-Host "🎯 Enhanced LLM routing test completed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "🚨 Enhanced LLM routing test failed!" -ForegroundColor Red
    exit 1
}
