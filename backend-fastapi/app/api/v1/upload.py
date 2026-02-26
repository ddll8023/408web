"""
文件上传模块路由
提供图片上传、列表管理、引用检查和清理功能
"""
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import SessionDep
from app.services.upload_service import UploadService
from app.schemas.common import Response
from app.schemas.image import ImageResourceResponse
from app.middleware.auth import get_current_admin, AuthUser
from app.exception import ValidationException


router = APIRouter()


def get_upload_service(session: AsyncSession) -> UploadService:
    """获取上传服务实例"""
    from app.config.settings import settings
    upload_dir = settings.upload.upload_dir
    return UploadService(session, upload_dir)


@router.post(
    "/image",
    summary="上传图片",
    description="上传图片文件，返回可访问的URL地址",
    response_model=Response[str],
    tags=["文件上传"]
)
async def upload_image(
    session: SessionDep,
    file: UploadFile = File(..., description="图片文件")
) -> Response[str]:
    """
    上传图片接口

    - 权限：公开
    - 支持格式：jpg, jpeg, png, gif, webp
    """
    upload_service = get_upload_service(session)
    file_url = await upload_service.upload_image(file)
    return Response(data=file_url, message="图片上传成功")


@router.get(
    "/images",
    summary="查询已上传图片列表",
    description="列出uploads/images目录下的所有图片",
    response_model=Response[list[ImageResourceResponse]],
    tags=["文件上传"]
)
async def list_images(
    session: SessionDep,
    only_unreferenced: bool = Query(False, description="是否只查询未引用的图片")
) -> Response[list[ImageResourceResponse]]:
    """
    查询已上传图片列表

    - 权限：ADMIN
    - 返回每张图片的元数据和引用状态
    """
    upload_service = get_upload_service(session)
    images = await upload_service.list_images(only_unreferenced)
    return Response(data=images, message="查询成功")


@router.post(
    "/images/cleanup",
    summary="删除所有未被真题引用的图片",
    description="扫描真题引用后删除未被引用的图片",
    response_model=Response[int],
    tags=["文件上传"]
)
async def cleanup_unreferenced_images(
    session: SessionDep,
    current_user: AuthUser = Depends(get_current_admin)
) -> Response[int]:
    """
    删除未引用图片

    - 权限：ADMIN
    - 清理真题和模拟题都未引用的图片
    """
    upload_service = get_upload_service(session)
    delete_count = await upload_service.cleanup_unreferenced_images()
    return Response(data=delete_count, message=f"已删除未引用图片 {delete_count} 张")


@router.post(
    "/image/delete",
    summary="删除已上传图片",
    description="根据文件名删除图片",
    response_model=Response[None],
    tags=["文件上传"]
)
async def delete_image(
    session: SessionDep,
    filename: str = Query(..., description="文件名"),
    current_user: AuthUser = Depends(get_current_admin)
) -> Response[None]:
    """
    删除指定图片

    - 权限：ADMIN
    - 注意：不会检查图片是否被引用，直接删除
    """
    upload_service = get_upload_service(session)
    upload_service.delete_image(filename)
    return Response(message="删除成功")
