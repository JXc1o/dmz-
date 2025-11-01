@echo off
title sSLiM Batch Experiment Runner

REM ================== Settings ==================
set NUM_RUNS=5
REM ============================================

echo ==================================================
echo      Starting sSLiM Batch Experiments
echo      Number of runs to perform: %NUM_RUNS%
echo ==================================================

IF EXIST venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

IF NOT EXIST results (
    echo Creating 'results' directory...
    mkdir results
)

FOR /L %%i IN (1,1,%NUM_RUNS%) DO (
    echo.
    echo --------------------------------------------------
    echo      Executing Run %%i of %NUM_RUNS%
    echo --------------------------------------------------
    python main.py %%i
)

echo.
echo ==================================================
echo      All Batch Experiments Complete!
echo ==================================================
echo.
echo      Check the 'results' folder for all output files.
echo.
pause