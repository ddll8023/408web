"""API 路由聚合模块。"""
from fastapi import APIRouter

from app.api import exam, mock, upload
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router


router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(catalog_router, tags=["目录管理"])
router.include_router(exam.router, prefix="/exam", tags=["真题管理"])
router.include_router(mock.router, prefix="/mock", tags=["模拟题管理"])
router.include_router(upload.router, prefix="/upload", tags=["文件上传"])
