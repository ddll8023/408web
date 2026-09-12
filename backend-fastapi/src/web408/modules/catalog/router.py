"""目录模块路由聚合。"""
from fastapi import APIRouter

from web408.modules.catalog.routers import category, chapter, subject


router = APIRouter()

router.include_router(subject.router, prefix="/subject", tags=["科目管理"])
router.include_router(chapter.router, prefix="/chapter", tags=["章节管理"])
router.include_router(category.router, prefix="/exam-category", tags=["分类管理"])
