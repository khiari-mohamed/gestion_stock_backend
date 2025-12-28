@echo off
echo ========================================
echo StockFlow Pro - Test Suite Runner
echo ========================================
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Running all tests with coverage...
echo.

pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

echo.
echo ========================================
echo Test Results Summary
echo ========================================
echo Coverage report generated in htmlcov/index.html
echo.

pause
