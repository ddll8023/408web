@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
:: 408Web FastAPI 启动脚本
:: ============================================

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%backend-fastapi"
set "VENV_DIR=%PROJECT_DIR%\.conda"
set "VENV_PYTHON=%VENV_DIR%\python.exe"
set "REQUIREMENTS=%PROJECT_DIR%\requirements.txt"
set "PORT=8081"
set "HOST=0.0.0.0"

:: 默认不使用 reload（Windows 上更可靠）
set "USE_RELOAD=false"

:: 解析参数
if "%1"=="/reload" set "USE_RELOAD=true"
if "%1"=="-r" set "USE_RELOAD=true"

title 408Web FastAPI Server

echo ============================================
echo   408Web FastAPI 启动脚本
echo ============================================
echo.
echo 用法: startup.bat [/reload] [-r]
echo   不带参数: 稳定模式，手动重启生效修改
echo   /reload   : 热重载模式，代码修改自动生效（Windows 可能不稳定）
echo.

:: 检查 Python 虚拟环境
if not exist "%VENV_PYTHON%" (
    echo [ERROR] 未找到虚拟环境: %VENV_DIR%
    echo [INFO] 请先安装依赖: cd backend-fastapi ^&^& pip install -r requirements.txt
    goto :end
)

echo [1/3] 切换到项目目录...
cd /d "%PROJECT_DIR%"
echo       当前目录: %CD%

echo [2/3] 检查环境...
echo       Python 路径: %VENV_PYTHON%
echo       端口: %PORT%

if "%USE_RELOAD%"=="true" (
    echo       模式: 热重载
) else (
    echo       模式: 稳定模式
)

:: 检查端口是否被占用
echo.
echo [检查] 端口 %PORT% ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
    set "BUSY_PID=%%a"
    goto :port_busy
)
echo       端口空闲
goto :port_ok

:port_busy
echo [警告] 端口 %PORT% 被进程 %BUSY_PID% 占用
echo [信息] 正在终止进程...
taskkill /PID %BUSY_PID% /F >nul 2>&1
timeout /t 2 /nobreak >nul
:: 验证是否已释放
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul
if errorlevel 1 (
    echo       进程已终止，端口已释放
) else (
    echo [错误] 无法释放端口，请手动关闭后重试
    echo       运行: netstat -ano ^| findstr :%PORT%
    goto :end
)

:port_ok
echo [3/3] 启动服务...
echo.
echo ============================================
echo   服务启动中...
echo   API 文档: http://localhost:%PORT%/docs
echo   健康检查: http://localhost:%PORT%/health
echo ============================================
echo.
echo [信息] 按 Ctrl+C 或关闭窗口可停止服务
echo.

:: 构建启动命令
set "CMD=%VENV_PYTHON% -m uvicorn app.main:app --host %HOST% --port %PORT%"
if "%USE_RELOAD%"=="true" set "CMD=%CMD% --reload"

:: 在新窗口运行服务
start "408Web FastAPI" %CMD%

:: 等待服务启动
timeout /t 3 /nobreak >nul

echo [完成] 服务已在新窗口启动
echo [信息] 如需停止，在新窗口按 Ctrl+C 或点击 X 关闭

:end
endlocal
pause
