@echo off
REM =================================================================
REM sSLiM Project Environment Setup Batch File
REM =================================================================
REM This script checks for Python and Pip, then installs all
REM necessary libraries for the sSLiM simulator and its GUI.
REM =================================================================

echo [1/4] Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python is not installed or not found in your PATH.
    echo Please install Python 3.x from python.org and ensure it is added to the system PATH.
    pause
    exit /b 1
)
echo Python found.

echo.
echo [2/4] Checking for Pip (Python Package Installer)...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Pip is not found. Your Python installation might be corrupted.
    echo Please try reinstalling Python.
    pause
    exit /b 1
)
echo Pip found.

echo.
echo [3/4] Upgrading Pip to the latest version...
python -m pip install --upgrade pip
echo Pip upgrade complete.

echo.
echo [4/4] Installing required Python libraries...
echo Installing core libraries (pandas, numpy, matplotlib)...
python -m pip install pandas numpy matplotlib

echo.
echo Installing GUI libraries (PyQt6, pyqtgraph)...
python -m pip install PyQt6 pyqtgraph

echo.
echo Installing Web UI libraries (dash, dash-bootstrap-components)...
python -m pip install dash dash-bootstrap-components

echo.
echo =================================================================
echo.
echo     Environment setup complete!
echo.
echo     You can now run the GUI with:
echo     python gui.py
echo.
echo     Or run the batch simulation with:
echo     python main.py
echo.
echo =================================================================
pause