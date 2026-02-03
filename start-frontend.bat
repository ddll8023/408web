@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
:: 408Web 前端启动脚本
:: ============================================

set "SCRIPT_DIR=%~dp0"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"
set "PORT=5174"

:: 检查前端目录是否存在
if not exist "%FRONTEND_DIR%" (
    echo [ERROR] 未找到前端目录: %FRONTEND_DIR%
    goto :end
)

:: 检查 package.json 是否存在
if not exist "%FRONTEND_DIR%\package.json" (
    echo [ERROR] 未找到 package.json，请确认前端项目已初始化
    goto :end
)

:: 检查 node_modules 是否存在
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [ERROR] 未找到 node_modules，请先运行 npm install 安装依赖
    goto :end
)

title 408Web Frontend Server

echo ============================================
echo   408Web 前端启动脚本
echo ============================================
echo.

echo [1/3] 切换到前端目录...
cd /d "%FRONTEND_DIR%"
echo       当前目录: %CD%

echo.
echo [2/3] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 Node.js，请先安装 Node.js
    goto :end
)
echo       Node.js 版本: 
node --version

echo.
echo [3/3] 检查端口 %PORT% 占用状态...
netstat -an | find ":%PORT%" >nul
if not errorlevel 1 (
    echo [WARNING] 端口 %PORT% 已被占用，启动后可能无法访问
    echo.
)

echo.
echo ============================================
echo   启动前端开发服务器...
echo   访问地址: http://localhost:%PORT%
echo ============================================
echo.
echo [INFO] 按 Ctrl+C 停止服务
echo.

:: 启动 Vite 开发服务器
call npm run dev

:end
endlocal
pause
