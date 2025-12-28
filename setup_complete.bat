@echo off
echo ========================================
echo StockFlow Pro - Complete Setup
echo ========================================
echo.

echo [1/5] Cleaning duplicate files...
if exist "app\api\auth.py" del "app\api\auth.py"
if exist "app\api\articles.py" del "app\api\articles.py"
if exist "app\api\dashboard.py" del "app\api\dashboard.py"
if exist "app\api\mouvements.py" del "app\api\mouvements.py"
echo Done!
echo.

echo [2/5] Generating Prisma client...
call prisma generate
if %errorlevel% neq 0 (
    echo ERROR: Prisma generate failed!
    pause
    exit /b 1
)
echo Done!
echo.

echo [3/5] Starting Docker services...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Docker services failed to start!
    pause
    exit /b 1
)
echo Done!
echo.

echo [4/5] Waiting for database (10 seconds)...
timeout /t 10 /nobreak >nul
echo Done!
echo.

echo [5/5] Pushing database schema...
call prisma db push
if %errorlevel% neq 0 (
    echo ERROR: Database push failed!
    pause
    exit /b 1
)
echo Done!
echo.

echo ========================================
echo Setup Complete! 
echo ========================================
echo.
echo Next steps:
echo 1. Run: python seed.py (to add test data)
echo 2. Run: uvicorn app.main:app --reload
echo 3. Open: http://localhost:8000/docs
echo.
echo Test credentials:
echo   Email: patron@epicerie.tn
echo   Password: password123
echo.
pause
