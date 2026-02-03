"""
API 路由模块 v1
所有 API 路由在此注册
"""
from fastapi import APIRouter
from app.api.v1 import auth, subject, chapter, exam_category, exam, mock, upload

router = APIRouter()

# 注册各模块路由
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(subject.router, prefix="/subject", tags=["科目管理"])
router.include_router(chapter.router, prefix="/chapter", tags=["章节管理"])
router.include_router(exam_category.router, prefix="/exam-category", tags=["分类管理"])
router.include_router(exam.router, prefix="/exam", tags=["真题管理"])
router.include_router(mock.router, prefix="/mock", tags=["模拟题管理"])
router.include_router(upload.router, prefix="/upload", tags=["文件上传"])
