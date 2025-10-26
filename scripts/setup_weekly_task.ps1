# EMO Options Bot - Enhanced Weekly Task Setup
# Creates Windows Scheduled Tasks for automated EMO operations

param(
    [string]$ProjectRoot = "C:\Users\thepr\Downloads\emo_options_bot_sqlite_plot_upgrade",
    [string]$Environment = "dev",
    [switch]$Production,
    [switch]$RemoveOnly,
    [switch]$ShowStatus
)

# Set environment based on parameters
if ($Production) {
    $Environment = "prod"
}

Write-Host "=== EMO Bot Scheduled Task Setup ===" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Green
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Green

# Validate project directory
if (-not (Test-Path $ProjectRoot)) {
    Write-Error "Project directory not found: $ProjectRoot"
    exit 1
}

Set-Location $ProjectRoot

# Define Python executable path
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Warning "Python virtual environment not found. Using system Python."
    $PythonExe = "python.exe"
}

# Task definitions
$Tasks = @(
    @{
        Name = "EMO_RetrainWeekly"
        Script = "scripts\automation\enhanced_weekly_retrain.py"
        Schedule = "Weekly"
        DaysOfWeek = "Sunday"
        Time = "04:00"
        Description = "Weekly ML model retraining for EMO Options Bot"
        Priority = "High"
    },
    @{
        Name = "EMO_IngestData"
        Script = "scripts\ingestion\enhanced_ingestion.py"
        Arguments = "--continuous --interval 15"
        Schedule = "AtStartup"
        Description = "Continuous market data ingestion for EMO Options Bot"
        Priority = "Normal"
        RunContinuous = $true
    },
    @{
        Name = "EMO_GenerateOutlook"
        Script = "scripts\ml\enhanced_ml_outlook.py"
        Arguments = "--export --save-db"
        Schedule = "Daily"
        Time = "08:30"
        Description = "Daily ML outlook generation for EMO dashboard"
        Priority = "Normal"
    },
    @{
        Name = "EMO_DatabaseMaintenance"
        Script = "scripts\migration\migrate_timescale.py"
        Arguments = "--action status"
        Schedule = "Daily"
        Time = "02:00"
        Description = "Daily database health check and maintenance"
        Priority = "Low"
    }
)

function Remove-EMOTasks {
    Write-Host "Removing existing EMO scheduled tasks..." -ForegroundColor Yellow
    
    foreach ($task in $Tasks) {
        if (Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue) {
            try {
                Unregister-ScheduledTask -TaskName $task.Name -Confirm:$false
                Write-Host "✅ Removed: $($task.Name)" -ForegroundColor Green
            } catch {
                Write-Warning "Failed to remove: $($task.Name) - $_"
            }
        }
    }
}

function Show-TaskStatus {
    Write-Host "=== EMO Scheduled Tasks Status ===" -ForegroundColor Cyan
    
    foreach ($task in $Tasks) {
        $scheduledTask = Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue
        if ($scheduledTask) {
            $taskInfo = Get-ScheduledTaskInfo -TaskName $task.Name -ErrorAction SilentlyContinue
            $status = if ($taskInfo) { $taskInfo.LastTaskResult } else { "Unknown" }
            $lastRun = if ($taskInfo) { $taskInfo.LastRunTime } else { "Never" }
            
            Write-Host "Task: $($task.Name)" -ForegroundColor White
            Write-Host "  Status: $($scheduledTask.State)" -ForegroundColor $(if ($scheduledTask.State -eq "Ready") { "Green" } else { "Yellow" })
            Write-Host "  Last Run: $lastRun" -ForegroundColor Gray
            Write-Host "  Last Result: $status" -ForegroundColor $(if ($status -eq 0) { "Green" } else { "Red" })
            Write-Host ""
        } else {
            Write-Host "Task: $($task.Name) - NOT FOUND" -ForegroundColor Red
        }
    }
}

function Create-EMOTask {
    param($TaskDef)
    
    $TaskName = $TaskDef.Name
    Write-Host "Creating task: $TaskName" -ForegroundColor Cyan
    
    # Build command arguments
    $Arguments = $TaskDef.Script
    if ($TaskDef.Arguments) {
        $Arguments += " $($TaskDef.Arguments)"
    }
    
    # Create task action
    $Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $Arguments -WorkingDirectory $ProjectRoot
    
    # Create trigger based on schedule type
    $Trigger = switch ($TaskDef.Schedule) {
        "Weekly" {
            $Days = $TaskDef.DaysOfWeek -split ","
            $Time = [DateTime]::Parse($TaskDef.Time)
            New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Days -At $Time
        }
        "Daily" {
            $Time = [DateTime]::Parse($TaskDef.Time)
            New-ScheduledTaskTrigger -Daily -At $Time
        }
        "AtStartup" {
            New-ScheduledTaskTrigger -AtStartup
        }
        default {
            throw "Unsupported schedule type: $($TaskDef.Schedule)"
        }
    }
    
    # Create task settings
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    # Set priority
    if ($TaskDef.Priority -eq "High") {
        $Settings.Priority = 4
    } elseif ($TaskDef.Priority -eq "Low") {
        $Settings.Priority = 7
    } else {
        $Settings.Priority = 6  # Normal
    }
    
    # For continuous tasks, allow multiple instances
    if ($TaskDef.RunContinuous) {
        $Settings.MultipleInstances = "Parallel"
        $Settings.ExecutionTimeLimit = "PT0S"  # No time limit
    }
    
    # Environment variables for the task
    $EnvironmentVars = @(
        "EMO_ENV=$Environment",
        "EMO_SYMBOLS=SPY,QQQ,AAPL",
        "EMO_DATA_PROVIDER=alpaca"
    )
    
    # Add production-specific variables
    if ($Environment -eq "prod") {
        $EnvironmentVars += @(
            "EMO_DB_ENGINE=timescale",
            "EMO_EMAIL_NOTIFICATIONS=true"
        )
    }
    
    # Create the principal with environment variables
    $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    try {
        # Register the task
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description $TaskDef.Description
        
        Write-Host "✅ Created: $TaskName" -ForegroundColor Green
        Write-Host "   Schedule: $($TaskDef.Schedule)" -ForegroundColor Gray
        if ($TaskDef.Time) {
            Write-Host "   Time: $($TaskDef.Time)" -ForegroundColor Gray
        }
        Write-Host "   Script: $($TaskDef.Script)" -ForegroundColor Gray
        
        return $true
    } catch {
        Write-Error "Failed to create task $TaskName`: $_"
        return $false
    }
}

# Main execution
if ($ShowStatus) {
    Show-TaskStatus
    exit 0
}

if ($RemoveOnly) {
    Remove-EMOTasks
    Write-Host "All EMO tasks removed." -ForegroundColor Yellow
    exit 0
}

# Remove existing tasks first
Remove-EMOTasks

Write-Host ""
Write-Host "Creating EMO scheduled tasks..." -ForegroundColor Cyan

$SuccessCount = 0
$TotalTasks = $Tasks.Count

foreach ($task in $Tasks) {
    if (Create-EMOTask -TaskDef $task) {
        $SuccessCount++
    }
    Write-Host ""
}

Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Created: $SuccessCount/$TotalTasks tasks" -ForegroundColor $(if ($SuccessCount -eq $TotalTasks) { "Green" } else { "Yellow" })

if ($SuccessCount -eq $TotalTasks) {
    Write-Host ""
    Write-Host "🎉 All EMO scheduled tasks created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Management Commands:" -ForegroundColor Yellow
    Write-Host "View status:    .\scripts\setup_weekly_task.ps1 -ShowStatus" -ForegroundColor Gray
    Write-Host "Remove all:     .\scripts\setup_weekly_task.ps1 -RemoveOnly" -ForegroundColor Gray
    Write-Host "Start manually: Start-ScheduledTask -TaskName EMO_RetrainWeekly" -ForegroundColor Gray
    Write-Host "View logs:      Get-Content logs\*.log -Tail 50" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "Environment Configuration:" -ForegroundColor Yellow
    Write-Host "Set EMO_ENV=$Environment for manual runs" -ForegroundColor Gray
    if ($Environment -eq "prod") {
        Write-Host "Configure these for production:" -ForegroundColor Red
        Write-Host "  EMO_DB_URL (TimescaleDB connection)" -ForegroundColor Red
        Write-Host "  ALPACA_KEY_ID and ALPACA_SECRET_KEY" -ForegroundColor Red
        Write-Host "  EMO_EMAIL_USER and EMO_EMAIL_PASSWORD" -ForegroundColor Red
    }
} else {
    Write-Error "Some tasks failed to create. Check the errors above."
    exit 1
}  
Write-Host "Remove task: Unregister-ScheduledTask -TaskName EMO_RetrainWeekly -Confirm:$false" -ForegroundColor Gray