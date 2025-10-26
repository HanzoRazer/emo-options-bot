@echo off
echo ========================================
echo EMO Options Bot - Phase 3 Pipeline Test
echo ========================================
echo.

echo Step 1: Generate Trade Plan
python tools\llm_trade_plan.py --prompt "Conservative iron condor on SPY" --max-risk 500
if %errorlevel% neq 0 goto error

echo.
echo Step 2: Validate Trade Plan  
python tools\validate_trade_plan.py --file ops\staged_orders\PLAN.json
if %errorlevel% neq 0 goto error

echo.
echo Step 3: Stage Trade for Review
python tools\phase3_stage_trade.py --from-plan ops\staged_orders\PLAN.json --note "Phase 3 pipeline test"
if %errorlevel% neq 0 goto error

echo.
echo ========================================
echo Phase 3 Pipeline Test COMPLETED
echo ========================================
echo.
echo Files created in ops\staged_orders\:
dir ops\staged_orders\staged_*.json /b 2>nul | findstr /r "staged_.*\.json$"
echo.
echo Features demonstrated:
echo [X] Natural language to structured JSON plan
echo [X] Risk validation and compliance checking  
echo [X] Non-bypassable safety gates
echo [X] Staging for human review
echo [X] Audit trail and backup system
goto end

:error
echo.
echo Pipeline test FAILED at step above
echo Check the error messages for details
exit /b 1

:end