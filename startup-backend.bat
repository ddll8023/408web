@echo off
chcp 65001 >nul
echo ========================================
echo   408Web FastAPI 后端服务启动脚本
echo ========================================
echo.

cd /d "%~dp0backend-fastapi"

echo [INFO] 检查虚拟环境...
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] 虚拟环境未找到，请先运行 pip install -r requirements.txt
    pause
    exit /b 1
)

echo [INFO] 启动 FastAPI 服务...
echo [INFO] 服务地址: http://localhost:8081
echo [INFO] API文档:   http://localhost:8081/docs
echo.

.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload

pause
