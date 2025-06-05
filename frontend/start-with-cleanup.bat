@echo off
chcp 65001 >nul
echo ================================================
echo LLM Batch Tool - 智能启动脚本
echo ================================================

echo [1/4] 清理端口占用...

:: 强制清理端口3001 (后端服务)
echo 检查并清理端口3001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3001.*LISTENING"') do (
    if not "%%a"=="" (
        echo 发现占用端口3001的进程: %%a，正在强制终止...
        taskkill /PID %%a /F >nul 2>&1
        if !errorlevel! equ 0 (
            echo 成功终止进程 %%a
        ) else (
            echo 无法终止进程 %%a，可能需要管理员权限
        )
    )
)

:: 强制清理端口5173 (前端服务)
echo 检查并清理端口5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173.*LISTENING"') do (
    if not "%%a"=="" (
        echo 发现占用端口5173的进程: %%a，正在强制终止...
        taskkill /PID %%a /F >nul 2>&1
        if !errorlevel! equ 0 (
            echo 成功终止进程 %%a
        ) else (
            echo 无法终止进程 %%a，可能需要管理员权限
        )
    )
)

:: 额外保险：清理可能的残留node进程
echo 清理可能的残留进程...
wmic process where "commandline like '%%index.js%%' or commandline like '%%vite%%'" get processid /format:value 2>nul | find "ProcessId" | for /f "tokens=2 delims==" %%a in ('more') do (
    if not "%%a"=="" (
        echo 清理残留进程: %%a
        taskkill /PID %%a /F >nul 2>&1
    )
)

echo 端口清理完成
timeout /t 2 /nobreak > nul

echo [2/4] 最终检查端口状态...

:: 最终确认端口已释放
netstat -an | findstr ":3001.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo 警告: 端口3001仍被占用，但继续启动...
) else (
    echo 端口3001已释放
)

netstat -an | findstr ":5173.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo 警告: 端口5173仍被占用，但继续启动...
) else (
    echo 端口5173已释放
)

echo [3/4] 启动后端服务...

:: 启动后端服务
cd /d %~dp0server
start /B node index.js > ../backend.log 2>&1

:: 等待后端启动
echo 等待后端服务启动...
timeout /t 5 /nobreak > nul

:: 验证后端启动成功
netstat -an | findstr ":3001.*LISTENING" >nul
if %errorlevel% equ 0 (
    echo 后端服务启动成功 (端口3001)
) else (
    echo 后端服务启动失败，请检查 backend.log
    echo 继续启动前端服务...
)

echo [4/4] 启动前端服务...
cd /d %~dp0

echo 启动前端开发服务器...
npm run dev

echo.
echo ================================================
echo 服务启动完成！
echo 前端地址: http://localhost:5173
echo 后端地址: http://localhost:3001
echo ================================================
pause 