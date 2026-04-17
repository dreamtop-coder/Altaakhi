@echo off
mkdir "%~dp0logs" 2>nul
"%~dp0.venv\Scripts\python.exe" "%~dp0manage.py" run_recurring_expenses >> "%~dp0logs\recurring.log" 2>&1
