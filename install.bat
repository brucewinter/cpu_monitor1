@echo off
echo ========================================
echo CPU Monitor & App Restarter - Installer
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python found!
python --version
echo.

echo Installing required dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo You can now run the application using:
echo   - run_cpu_monitor.bat (double-click)
echo   - run_cpu_monitor.ps1 (PowerShell)
echo   - python cpu_monitor.py (command line)
echo.
echo For best results, run as Administrator
echo.
pause
