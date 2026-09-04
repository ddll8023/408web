"""408Web FastAPI 应用入口。"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as api_v1_router
from app.config.settings import settings
from app.database.connection import engine, init_db
from app.exception import register_exception_handlers
from app.middleware.cors import GlobalCorsMiddleware
from app.schemas.common import ApiResponse
from app.utils.logger import setup_logger


logger = setup_logger(level=settings.logging.log_level, console=True)


def ensure_directories() -> None:
    """确保运行时目录存在。"""
    os.makedirs(settings.upload.upload_dir, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs(settings.logging.log_dir, exist_ok=True)


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

app.include_router(api_v1_router, prefix=settings.server.api_prefix)


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
