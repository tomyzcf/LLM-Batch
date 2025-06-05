@echo off
chcp 65001 >nul
echo ================================================
echo LLM Batch Tool - Startup Script
echo ================================================

echo [1/3] Checking service status...

:: Check if backend port 3001 is in use
netstat -an | findstr ":3001" >nul
if %errorlevel% equ 0 (
    echo Backend service already running on port 3001
) else (
    echo [2/3] Starting backend service...
    cd /d %~dp0server
    start /B node index.js > ../backend.log 2>&1
    
    :: Wait for backend to start
    echo Waiting for backend service...
    timeout /t 5 /nobreak > nul
    
    :: Verify backend started successfully
    netstat -an | findstr ":3001" >nul
    if %errorlevel% equ 0 (
        echo Backend service started successfully
    ) else (
        echo Backend service failed to start, check backend.log
        pause
        exit /b 1
    )
)

echo [3/3] Starting frontend service...
cd /d %~dp0

:: Check if frontend port 5173 is in use
netstat -an | findstr ":5173" >nul
if %errorlevel% equ 0 (
    echo Frontend port 5173 is occupied, please close other services first
    pause
    exit /b 1
)

echo Starting frontend development server...
npm run dev

echo.
echo ================================================
echo If services started successfully, visit: http://localhost:5173
echo Backend service: http://localhost:3001
echo ================================================