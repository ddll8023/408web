"""API 路由聚合模块。"""
from fastapi import APIRouter

from web408.modules.auth.router import router as auth_router
from web408.modules.catalog.router import router as catalog_router
from web408.modules.exam.router import router as exam_router
from web408.modules.mock.router import router as mock_router
from web408.modules.reporting.router import router as reporting_router
from web408.modules.media.router import router as media_router


router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(catalog_router, tags=["目录管理"])
router.include_router(reporting_router, prefix="/exam", tags=["真题管理"])
router.include_router(exam_router, prefix="/exam", tags=["真题管理"])
router.include_router(mock_router, prefix="/mock", tags=["模拟题管理"])
router.include_router(media_router, prefix="/upload", tags=["文件上传"])
