@ECHO OFF
TITLE sSLiM Ecosystem Simulator Launcher

REM --- 1. 파이썬 실행 가능 여부 확인 ---
python --version >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO ERROR: 'python' command not found.
    ECHO Please install Python 3 and ensure it is added to your system's PATH.
    ECHO (During installation, check the box 'Add Python to PATH')
    ECHO.
    PAUSE
    EXIT /B
)

REM --- 2. 필요한 라이브러리 자동 설치 ---
ECHO.
ECHO ==========================================================
ECHO  Checking and installing required Python packages...
ECHO ==========================================================
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO ERROR: Failed to install required packages.
    ECHO Please check your internet connection and pip installation.
    ECHO.
    PAUSE
    EXIT /B
)
ECHO.
ECHO All required packages are installed.
ECHO.
PAUSE
CLS

:MENU
CLS
ECHO.
ECHO ==========================================================
ECHO          sSLiM - Ecosystem Simulator Menu
ECHO ==========================================================
ECHO.
ECHO  1. Start Interactive Simulator (GUI)
ECHO  2. Run Batch Simulation (from config.json)
ECHO  3. Run Parameter Optimizer (Advanced)
ECHO  4. Exit
ECHO.
ECHO ==========================================================
ECHO.

SET /P "CHOICE=Enter your choice [1-4]: "

IF "%CHOICE%"=="1" GOTO GUI
IF "%CHOICE%"=="2" GOTO SIMULATOR
IF "%CHOICE%"=="3" GOTO OPTIMIZER
IF "%CHOICE%"=="4" GOTO END

ECHO Invalid choice. Please try again.
PAUSE
GOTO MENU

:GUI
CLS
ECHO Starting Interactive Simulator (GUI)...
ECHO Please wait for the application window to open.
python gui_main.py
ECHO.
ECHO GUI application closed.
PAUSE
GOTO MENU

:SIMULATOR
CLS
ECHO Starting Batch Simulation (main.py)...
ECHO This will run multiple simulations as defined in main.py
ECHO and process the results. Check the console for progress.
python main.py
ECHO.
ECHO Batch simulation finished. Check the 'results' folder.
PAUSE
GOTO MENU

:OPTIMIZER
CLS
ECHO Starting Parameter Optimizer (optimizer.py)...
ECHO.
ECHO WARNING: This is a CPU-intensive process and may take a
ECHO          very long time to complete.
ECHO.
python optimizer.py
ECHO.
ECHO Optimization finished. Check the console for the best parameters.
PAUSE
GOTO MENU

:END
ECHO Exiting.