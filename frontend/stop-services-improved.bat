@echo off
chcp 65001 >nul
echo ================================================
echo 停止 LLM Batch Tool 服务 (改进版)
echo ================================================

echo 正在查找并停止服务...

:: 停止占用端口3001的进程 (后端服务)
echo 清理端口3001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001.*LISTENING"') do (
    if not "%%a"=="" (
        echo 发现后端服务进程: %%a，正在终止...
        taskkill /PID %%a /F >nul 2>&1
        if !errorlevel! equ 0 (
            echo 成功终止后端进程 %%a
        ) else (
            echo 无法终止进程 %%a
        )
    )
)

:: 停止占用端口5173的进程 (前端服务)
echo 清理端口5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173.*LISTENING"') do (
    if not "%%a"=="" (
        echo 发现前端服务进程: %%a，正在终止...
        taskkill /PID %%a /F >nul 2>&1
        if !errorlevel! equ 0 (
            echo 成功终止前端进程 %%a
        ) else (
            echo 无法终止进程 %%a
        )
    )
)

:: 清理可能的残留Node.js进程
echo 清理残留的Node.js进程...
wmic process where "commandline like '%%index.js%%' or commandline like '%%vite%%'" get processid /format:value 2>nul | find "ProcessId" | for /f "tokens=2 delims==" %%a in ('more') do (
    if not "%%a"=="" (
        echo 清理残留进程: %%a
        taskkill /PID %%a /F >nul 2>&1
    )
)

timeout /t 2 /nobreak > nul

echo 最终检查端口状态...
netstat -an | findstr ":3001.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo 警告: 端口3001仍被占用
) else (
    echo 端口3001已释放
)

netstat -an | findstr ":5173.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo 警告: 端口5173仍被占用
) else (
    echo 端口5173已释放
)

echo 服务停止操作完成
pause 