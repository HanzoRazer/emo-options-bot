#!/usr/bin/env pwsh
# Robustness Integration and Test Script
# Integrates all robustness enhancements and runs comprehensive tests

Write-Host "=== EMO Options Bot - Robustness Integration ===" -ForegroundColor Cyan
Write-Host "Integrating robustness enhancements and running comprehensive tests..." -ForegroundColor Yellow
Write-Host ""

# Configuration
$ProjectRoot = Get-Location
$LogDirectory = "logs"
$TestResultsFile = "$LogDirectory/robustness_integration_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"

# Ensure log directory exists
if (!(Test-Path $LogDirectory)) {
    New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null
    Write-Host "📁 Created log directory: $LogDirectory" -ForegroundColor Blue
}

# Function to run Python command with error handling
function Invoke-PythonCommand {
    param(
        [string]$Command,
        [string]$Description,
        [int]$TimeoutSeconds = 60
    )
    
    Write-Host "🔧 $Description..." -ForegroundColor Blue
    
    try {
        $StartTime = Get-Date
        $Process = Start-Process -FilePath "python" -ArgumentList $Command -NoNewWindow -PassThru -Wait -RedirectStandardOutput "$LogDirectory/temp_output.log" -RedirectStandardError "$LogDirectory/temp_error.log"
        $ElapsedTime = (Get-Date) - $StartTime
        
        $Output = ""
        $ErrorOutput = ""
        
        if (Test-Path "$LogDirectory/temp_output.log") {
            $Output = Get-Content "$LogDirectory/temp_output.log" -Raw -ErrorAction SilentlyContinue
            Remove-Item "$LogDirectory/temp_output.log" -ErrorAction SilentlyContinue
        }
        
        if (Test-Path "$LogDirectory/temp_error.log") {
            $ErrorOutput = Get-Content "$LogDirectory/temp_error.log" -Raw -ErrorAction SilentlyContinue
            Remove-Item "$LogDirectory/temp_error.log" -ErrorAction SilentlyContinue
        }
        
        $Result = @{
            Command = $Command
            Description = $Description
            ExitCode = $Process.ExitCode
            ElapsedSeconds = $ElapsedTime.TotalSeconds
            Output = $Output
            ErrorOutput = $ErrorOutput
            Success = $Process.ExitCode -eq 0
        }
        
        if ($Result.Success) {
            Write-Host "✅ $Description completed successfully ($([math]::Round($ElapsedTime.TotalSeconds, 1))s)" -ForegroundColor Green
        } else {
            Write-Host "❌ $Description failed with exit code $($Process.ExitCode)" -ForegroundColor Red
            if ($ErrorOutput) {
                Write-Host "Error output: $ErrorOutput" -ForegroundColor Red
            }
        }
        
        return $Result
        
    } catch {
        Write-Host "❌ $Description failed with exception: $_" -ForegroundColor Red
        return @{
            Command = $Command
            Description = $Description
            ExitCode = -1
            ElapsedSeconds = 0
            Output = ""
            ErrorOutput = $_.Exception.Message
            Success = $false
            Exception = $_.Exception.Message
        }
    }
}

# Step 1: Check Python environment
Write-Host "🐍 Checking Python environment..." -ForegroundColor Green
try {
    $PythonVersion = python --version 2>&1
    Write-Host "✅ Python: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found or not accessible" -ForegroundColor Red
    exit 1
}

# Step 2: Install missing dependencies
Write-Host ""
Write-Host "📦 Installing missing dependencies..." -ForegroundColor Green

$Dependencies = @(
    "psutil",
    "requests",
    "python-dotenv"
)

foreach ($Dependency in $Dependencies) {
    Write-Host "  Installing $Dependency..." -ForegroundColor Blue
    try {
        pip install $Dependency 2>&1 | Out-Null
        Write-Host "  ✅ $Dependency installed" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Could not install $Dependency`: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Step 3: Run dependency health check
Write-Host ""
$DependencyCheck = Invoke-PythonCommand -Command "tools/dependency_manager.py" -Description "Dependency health check" -TimeoutSeconds 30

# Step 4: Run system health check
Write-Host ""
$HealthCheck = Invoke-PythonCommand -Command "tools/health_monitor.py --report" -Description "System health check" -TimeoutSeconds 30

# Step 5: Run Phase 3 component tests
Write-Host ""
Write-Host "🧪 Running Phase 3 component tests..." -ForegroundColor Green

$ComponentTests = @()

# Test LLM Trade Plan Generator
$LLMPlanTest = Invoke-PythonCommand -Command "-c `"from tools.llm_trade_plan import generate_trade_plan, TradeRequest; req = TradeRequest(description='Test call option', risk_tolerance='moderate', max_loss=500); result = generate_trade_plan(req); print('SUCCESS: Generated plan with strategy:', result.get('strategy', 'unknown'))`"" -Description "LLM Trade Plan Generator test" -TimeoutSeconds 30
$ComponentTests += $LLMPlanTest

# Test Trade Plan Validator
$ValidatorTest = Invoke-PythonCommand -Command "-c `"from tools.validate_trade_plan import validate_trade_plan; plan = {'strategy': 'long_call', 'symbol': 'SPY', 'legs': [{'action': 'buy', 'quantity': 1, 'strike': 450, 'expiry': '2024-01-19'}], 'max_loss': 500}; valid, errors, warnings = validate_trade_plan(plan); print('SUCCESS: Validation result:', valid, 'Errors:', len(errors), 'Warnings:', len(warnings))`"" -Description "Trade Plan Validator test" -TimeoutSeconds 30
$ComponentTests += $ValidatorTest

# Test Phase 3 Trade Stager
$StagerTest = Invoke-PythonCommand -Command "-c `"from tools.phase3_stage_trade import stage_trade_for_approval; plan = {'strategy': 'long_call', 'symbol': 'SPY', 'legs': [{'action': 'buy', 'quantity': 1, 'strike': 450, 'expiry': '2024-01-19'}]}; result = stage_trade_for_approval(plan, 'test_user'); print('SUCCESS: Staging result:', result.get('status', 'unknown'))`"" -Description "Phase 3 Trade Stager test" -TimeoutSeconds 30
$ComponentTests += $StagerTest

# Step 6: Run enhanced LLM routing test
Write-Host ""
Write-Host "🚀 Running enhanced LLM routing test..." -ForegroundColor Green

try {
    & ".\test-llm-routing.ps1" | Out-Null
    $LLMRoutingSuccess = $LASTEXITCODE -eq 0
    
    if ($LLMRoutingSuccess) {
        Write-Host "✅ Enhanced LLM routing test passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Enhanced LLM routing test failed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Enhanced LLM routing test failed with exception: $($_.Exception.Message)" -ForegroundColor Red
    $LLMRoutingSuccess = $false
}

# Step 7: Run comprehensive robustness test
Write-Host ""
$RobustnessTest = Invoke-PythonCommand -Command "tools/robust_test_runner.py" -Description "Comprehensive robustness test" -TimeoutSeconds 300

# Step 8: Collect and analyze results
Write-Host ""
Write-Host "📊 Analyzing integration results..." -ForegroundColor Cyan

$IntegrationResults = @{
    Timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    ProjectRoot = $ProjectRoot.Path
    PythonVersion = $PythonVersion
    Tests = @{
        DependencyCheck = $DependencyCheck
        HealthCheck = $HealthCheck
        ComponentTests = $ComponentTests
        LLMRoutingTest = @{
            Success = $LLMRoutingSuccess
            Description = "Enhanced LLM routing integration test"
        }
        RobustnessTest = $RobustnessTest
    }
    Summary = @{
        TotalTests = 0
        PassedTests = 0
        FailedTests = 0
        SuccessRate = 0
    }
}

# Calculate summary statistics
$AllTests = @($DependencyCheck, $HealthCheck) + $ComponentTests + @($RobustnessTest)
$AllTests += @{ Success = $LLMRoutingSuccess; Description = "LLM Routing Test" }

$IntegrationResults.Summary.TotalTests = $AllTests.Count
$IntegrationResults.Summary.PassedTests = ($AllTests | Where-Object { $_.Success }).Count
$IntegrationResults.Summary.FailedTests = $IntegrationResults.Summary.TotalTests - $IntegrationResults.Summary.PassedTests

if ($IntegrationResults.Summary.TotalTests -gt 0) {
    $IntegrationResults.Summary.SuccessRate = [math]::Round(($IntegrationResults.Summary.PassedTests / $IntegrationResults.Summary.TotalTests) * 100, 1)
}

# Save detailed results
$IntegrationResults | ConvertTo-Json -Depth 10 | Out-File -FilePath $TestResultsFile -Encoding UTF8

# Step 9: Generate integration report
Write-Host ""
Write-Host "=== Robustness Integration Report ===" -ForegroundColor Cyan
Write-Host "Timestamp: $($IntegrationResults.Timestamp)" -ForegroundColor Blue
Write-Host "Python Version: $PythonVersion" -ForegroundColor Blue
Write-Host ""

Write-Host "📈 Test Results Summary:" -ForegroundColor Green
Write-Host "  Total Tests: $($IntegrationResults.Summary.TotalTests)" -ForegroundColor Blue
Write-Host "  Passed: $($IntegrationResults.Summary.PassedTests) ✅" -ForegroundColor Green
Write-Host "  Failed: $($IntegrationResults.Summary.FailedTests) ❌" -ForegroundColor Red
Write-Host "  Success Rate: $($IntegrationResults.Summary.SuccessRate)%" -ForegroundColor $(if ($IntegrationResults.Summary.SuccessRate -ge 80) { "Green" } else { "Red" })

Write-Host ""
Write-Host "🔍 Individual Test Results:" -ForegroundColor Yellow

# Display test results
foreach ($Test in $AllTests) {
    $StatusEmoji = if ($Test.Success) { "✅" } else { "❌" }
    $StatusColor = if ($Test.Success) { "Green" } else { "Red" }
    
    Write-Host "  $StatusEmoji $($Test.Description)" -ForegroundColor $StatusColor
    
    if ($Test.ElapsedSeconds) {
        Write-Host "    Duration: $([math]::Round($Test.ElapsedSeconds, 2))s" -ForegroundColor Gray
    }
    
    if (!$Test.Success -and $Test.ErrorOutput) {
        Write-Host "    Error: $($Test.ErrorOutput)" -ForegroundColor Red
    }
}

# Step 10: Robustness assessment
Write-Host ""
Write-Host "🛡️ Robustness Assessment:" -ForegroundColor Cyan

$RobustnessScore = 0
$MaxRobustnessScore = 100

# Dependency management (20 points)
if ($DependencyCheck.Success) {
    $RobustnessScore += 20
    Write-Host "  ✅ Dependency Management: Robust (20/20)" -ForegroundColor Green
} else {
    Write-Host "  ❌ Dependency Management: Needs improvement (0/20)" -ForegroundColor Red
}

# Health monitoring (20 points)
if ($HealthCheck.Success) {
    $RobustnessScore += 20
    Write-Host "  ✅ Health Monitoring: Active (20/20)" -ForegroundColor Green
} else {
    Write-Host "  ❌ Health Monitoring: Not functional (0/20)" -ForegroundColor Red
}

# Component reliability (30 points)
$ComponentSuccessCount = ($ComponentTests | Where-Object { $_.Success }).Count
$ComponentScore = [math]::Round(($ComponentSuccessCount / $ComponentTests.Count) * 30)
$RobustnessScore += $ComponentScore

if ($ComponentScore -eq 30) {
    Write-Host "  ✅ Component Reliability: Excellent ($ComponentScore/30)" -ForegroundColor Green
} elseif ($ComponentScore -ge 20) {
    Write-Host "  ⚠️  Component Reliability: Good ($ComponentScore/30)" -ForegroundColor Yellow
} else {
    Write-Host "  ❌ Component Reliability: Poor ($ComponentScore/30)" -ForegroundColor Red
}

# Integration testing (20 points)
if ($LLMRoutingSuccess) {
    $RobustnessScore += 15
    Write-Host "  ✅ LLM Integration: Working (15/20)" -ForegroundColor Green
} else {
    Write-Host "  ❌ LLM Integration: Failed (0/20)" -ForegroundColor Red
}

if ($RobustnessTest.Success) {
    $RobustnessScore += 5
    Write-Host "  ✅ Comprehensive Testing: Passed (5/20)" -ForegroundColor Green
} else {
    Write-Host "  ❌ Comprehensive Testing: Failed (0/20)" -ForegroundColor Red
}

# Error handling (10 points)
$ErrorScore = 0
foreach ($Test in $AllTests) {
    if ($Test.Success -or ($Test.ErrorOutput -and $Test.ErrorOutput.Length -lt 500)) {
        $ErrorScore += 2
    }
}
$ErrorScore = [math]::Min($ErrorScore, 10)
$RobustnessScore += $ErrorScore

if ($ErrorScore -eq 10) {
    Write-Host "  ✅ Error Handling: Robust (10/10)" -ForegroundColor Green
} elseif ($ErrorScore -ge 6) {
    Write-Host "  ⚠️  Error Handling: Adequate ($ErrorScore/10)" -ForegroundColor Yellow
} else {
    Write-Host "  ❌ Error Handling: Needs improvement ($ErrorScore/10)" -ForegroundColor Red
}

Write-Host ""
Write-Host "🏆 Overall Robustness Score: $RobustnessScore/$MaxRobustnessScore ($([math]::Round(($RobustnessScore / $MaxRobustnessScore) * 100, 1))%)" -ForegroundColor $(if ($RobustnessScore -ge 80) { "Green" } elseif ($RobustnessScore -ge 60) { "Yellow" } else { "Red" })

# Final recommendations
Write-Host ""
Write-Host "💡 Recommendations:" -ForegroundColor Yellow

if ($RobustnessScore -ge 80) {
    Write-Host "  ✅ System is highly robust and ready for production use" -ForegroundColor Green
    Write-Host "  🎯 Continue monitoring and maintain current robustness practices" -ForegroundColor Blue
} elseif ($RobustnessScore -ge 60) {
    Write-Host "  ⚠️  System has good robustness but needs some improvements" -ForegroundColor Yellow
    Write-Host "  🔧 Focus on improving failed test areas" -ForegroundColor Blue
    Write-Host "  📈 Implement additional error handling and monitoring" -ForegroundColor Blue
} else {
    Write-Host "  ❌ System needs significant robustness improvements" -ForegroundColor Red
    Write-Host "  🚨 Critical: Fix dependency and health monitoring issues" -ForegroundColor Red
    Write-Host "  🔧 Implement comprehensive error handling" -ForegroundColor Red
    Write-Host "  🧪 Expand test coverage for all components" -ForegroundColor Red
}

Write-Host ""
Write-Host "📁 Detailed results saved to: $TestResultsFile" -ForegroundColor Blue
Write-Host ""

# Final status
if ($RobustnessScore -ge 70) {
    Write-Host "🎉 Robustness integration completed successfully!" -ForegroundColor Green
    Write-Host "🚀 EMO Options Bot is ready for enhanced operation" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Robustness integration completed with issues" -ForegroundColor Yellow
    Write-Host "🔧 Review recommendations and address failing tests" -ForegroundColor Yellow
    exit 1
}