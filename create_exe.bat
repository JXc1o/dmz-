@echo off
setlocal

REM =================================================================
REM SERM Simulator EXE-Packager using PyInstaller (PyQt6 Fix Applied)
REM - This script creates a single .exe file in the 'dist' folder.
REM - Includes hooks for common PyQt6 packaging issues.
REM =================================================================

set APP_NAME=SERM_Simulator
set ENTRY_SCRIPT=gui_main.py
set ICON_FILE=icon.ico

echo.
echo [1/4] Starting the SERM Simulator packaging process...
echo      - App Name: %APP_NAME%
echo      - Entry Point: %ENTRY_SCRIPT%
echo.

REM --- Check and install required packages ---
echo [2/4] Verifying/installing required packages from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ##### ERROR: Package installation failed. Please check if pip is installed and configured correctly.
    pause
    exit /b
)
echo      - Package installation complete.
echo.

REM --- Clean up previous build files ---
echo [3/4] Cleaning up previous build directories and files...
if exist "dist" ( rmdir /s /q "dist" )
if exist "build" ( rmdir /s /q "build" )
if exist "%APP_NAME%.spec" ( del "%APP_NAME%.spec" )
echo      - Cleanup complete.
echo.

REM --- Run PyInstaller with PyQt6 Hooks ---
echo [4/4] Creating the .exe file with PyInstaller and PyQt6 hooks...
echo      - This process may take a few minutes.
echo.

REM --- PyInstaller Command ---
REM --hidden-import: Forces PyInstaller to include modules it might miss.
REM                  This is crucial for solving the "AttributeError: 'pyqtSignal' object has no attribute 'connect'" error.

set PYINSTALLER_CMD=pyinstaller --name %APP_NAME% ^
            --onefile ^
            --windowed ^
            --add-data "config.json;." ^
            --add-data "deer.json;." ^
            --hidden-import "PyQt6.sip" ^
            --hidden-import "PyQt6.QtWidgets" ^
            --hidden-import "PyQt6.QtGui" ^
            --hidden-import "PyQt6.QtCore"

if exist "%ICON_FILE%" (
    set PYINSTALLER_CMD=%PYINSTALLER_CMD% --icon=%ICON_FILE%
)

%PYINSTALLER_CMD% %ENTRY_SCRIPT%
            
if %errorlevel% neq 0 (
    echo.
    echo ##### ERROR: PyInstaller failed to execute.
    pause
    exit /b
)

echo.
echo =================================================================
echo  SUCCESS! '%APP_NAME%.exe' has been created in the 'dist' folder.
echo =================================================================
echo.

pause
endlocal