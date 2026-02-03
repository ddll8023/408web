"""
408Web FastAPI 后端应用入口
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.database.connection import init_db, engine
from app.exception import register_exception_handlers
from app.api.v1.router import router as api_v1_router


# 配置日志（解决Windows终端ANSI转义码乱码问题）
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": os.path.join(settings.logging.log_dir, settings.logging.log_file),
            "maxBytes": settings.logging.max_bytes,
            "backupCount": settings.logging.backup_count,
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": settings.logging.log_level,
    },
    "loggers": {
        "uvicorn": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "sqlalchemy.engine": {"handlers": ["console", "file"], "level": "WARNING", "propagate": False},
    },
}

# 获取项目级日志记录器
logger = logging.getLogger("app")


# 确保必要的目录存在
def ensure_directories():
    """确保运行时需要的目录存在"""
    os.makedirs(settings.upload.upload_dir, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs(settings.logging.log_dir, exist_ok=True)


# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    - startup: 初始化数据库，创建表结构
    - shutdown: 清理资源
    """
    # 启动时
    ensure_directories()
    await init_db()  # 创建所有表结构
    yield
    # 关闭时
    await engine.dispose()


# 创建 FastAPI 应用
app = FastAPI(
    title="408Web API",
    description="408考研真题知识点阅读网站后端 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    redirect_slashes=False  # 禁用尾部斜杠自动重定向
)

# 注册异常处理器
register_exception_handlers(app)

# 注册全局响应中间件（在CORSMiddleware之后，确保CORS头始终注入）
from app.middleware.cors import GlobalCorsMiddleware
app.add_middleware(GlobalCorsMiddleware)

# 配置 CORS
print(f"[CORS] 已配置 origins: {settings.cors.origins}")

# 挂载静态文件目录（开发环境）
# 生产环境建议使用 Nginx 直接托管静态文件
if os.path.exists(settings.upload.upload_dir):
    app.mount(
        "/uploads/images",
        StaticFiles(directory=settings.upload.upload_dir),
        name="uploads"
    )

# 注册 API 路由
app.include_router(
    api_v1_router,
    prefix=settings.server.api_prefix
)


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "status": "ok",
        "message": "408Web API 服务运行中",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=True,
        reload_delay=0.5,  # Windows上增加reload延迟，避免竞态条件
        reload_dirs=[str(settings.upload.upload_dir)],  # 只监控指定目录
        log_config=LOGGING_CONFIG
    )
