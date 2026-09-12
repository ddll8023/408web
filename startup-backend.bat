@echo off
chcp 65001 >nul
echo ========================================
echo   408Web FastAPI 后端服务启动脚本
echo ========================================
echo.

cd /d "%~dp0backend-fastapi"

echo [INFO] 检查虚拟环境...
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] 虚拟环境未找到，请先在 backend-fastapi 中运行 uv sync
    pause
    exit /b 1
)

.venv\Scripts\python.exe -c "import web408" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 后端包尚未安装，请先在 backend-fastapi 中运行 uv sync --locked
    pause
    exit /b 1
)

echo [INFO] 启动 FastAPI 服务...
echo [INFO] 服务地址: http://localhost:7785
echo [INFO] API文档:   http://localhost:7785/docs
echo.

.venv\Scripts\python.exe -m uvicorn web408.main:app --host 0.0.0.0 --port 7785 --reload --reload-dir src/web408

pause
