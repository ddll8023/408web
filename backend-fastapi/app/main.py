"""408Web FastAPI 应用入口。"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# 显式加载 SQLModel 表模型，避免依赖路由或 Repository 的间接导入顺序。
from app.models import entities as _entities
from app.api.router import router as api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.database.connection import engine, init_db
from app.core.exceptions import register_exception_handlers
from app.middleware.cors import GlobalCorsMiddleware
from app.schemas.common import ApiResponse


configure_logging(
    log_dir=settings.logging.log_dir,
    log_file=settings.logging.log_file,
    level=settings.logging.log_level,
    backup_count=settings.logging.backup_count,
)
logger = logging.getLogger(__name__)


def ensure_directories() -> None:
    """确保运行时目录存在。"""
    os.makedirs(settings.upload.upload_dir, exist_ok=True)
    os.makedirs("data", exist_ok=True)


# StaticFiles 在应用创建时挂载，因此目录需要先准备好。
ensure_directories()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用启动和关闭生命周期。"""
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(
    title="408Web API",
    description="408 考研真题知识点阅读网站后端 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    redirect_slashes=False,
)

register_exception_handlers(app)

app.add_middleware(GlobalCorsMiddleware)

app.mount(
    "/uploads/images",
    StaticFiles(directory=settings.upload.upload_dir),
    name="uploads",
)

app.include_router(api_router, prefix=settings.server.api_prefix)


@app.post("/", response_model=ApiResponse[dict[str, str]])
async def root() -> ApiResponse[dict[str, str]]:
    """根路径健康检查。"""
    return ApiResponse(
        data={
            "status": "ok",
            "message": "408Web API 服务运行中",
            "docs": "/docs",
        }
    )


@app.post("/health", response_model=ApiResponse[dict[str, str]])
async def health_check() -> ApiResponse[dict[str, str]]:
    """健康检查端点。"""
    return ApiResponse(data={"status": "healthy"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=True,
        reload_delay=0.5,
        reload_dirs=[str(settings.upload.upload_dir)],
    )
