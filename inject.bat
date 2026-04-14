@echo off
REM ATO Shield v2 - Quick Transaction Injector
REM Usage: inject.bat [count] [speed] [fraud_rate]
REM Example: inject.bat 50 0.3 0.20

set COUNT=%~1
set SPEED=%~2
set FRAUD_RATE=%~3

if "%COUNT%"=="" set COUNT=50
if "%SPEED%"=="" set SPEED=0.3
if "%FRAUD_RATE%"=="" set FRAUD_RATE=0.20

echo.
echo ========================================
echo  ATO Shield v2 - Transaction Injector
echo ========================================
echo  Count:      %COUNT%
echo  Speed:      %SPEED%s
echo  Fraud Rate: %FRAUD_RATE%
echo ========================================
echo.

python simulator/simulator.py --count %COUNT% --speed %SPEED% --fraud-rate %FRAUD_RATE%
