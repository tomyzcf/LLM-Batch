@echo off
chcp 65001 >nul
echo ================================================
echo Stop LLM Batch Tool Services
echo ================================================

echo Finding and stopping services...

:: Stop processes using port 3001 (backend service)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001"') do (
    echo Stopping backend service (PID: %%a)
    taskkill /PID %%a /F >nul 2>&1
)

:: Stop processes using port 5173 (frontend service)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173"') do (
    echo Stopping frontend service (PID: %%a)
    taskkill /PID %%a /F >nul 2>&1
)

:: Stop all node.js processes (optional, use with caution)
:: taskkill /IM node.exe /F >nul 2>&1

echo Services stopped successfully
pause 