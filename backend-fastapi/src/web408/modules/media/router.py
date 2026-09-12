"""图片上传、资源列表和清理 HTTP 路由。"""
from fastapi import APIRouter, Depends, File, UploadFile

from web408.api.dependencies import SessionDep
from web408.core.config import settings
from web408.modules.auth.dependencies import AuthUser, get_current_admin
from web408.modules.media.schemas import (
    ImageCleanupRequest,
    ImageDeleteRequest,
    ImageListRequest,
    ImageResourceResponse,
)
from web408.modules.media.service import UploadService
from web408.schemas.common import ApiResponse


router = APIRouter()


def get_upload_service(session: SessionDep) -> UploadService:
    """构造上传服务。"""
    return UploadService(
        session,
        settings.upload.upload_dir,
        settings.upload.max_file_size,
    )


@router.post(
    "/image",
    summary="上传图片",
    description="上传并校验图片文件，仅管理员可访问",
    response_model=ApiResponse[str],
)
async def upload_image(
    session: SessionDep,
    file: UploadFile = File(..., description="图片文件"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[str]:
    """上传图片。"""
    file_url = await get_upload_service(session).upload_image(file)
    return ApiResponse(data=file_url, message="图片上传成功")


@router.post(
    "/images",
    summary="查询已上传图片列表",
    description="列出图片及引用状态，仅管理员可访问",
    response_model=ApiResponse[list[ImageResourceResponse]],
)
async def list_images(
    request: ImageListRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[list[ImageResourceResponse]]:
    """查询图片列表。"""
    images = await get_upload_service(session).list_images(request.only_unreferenced)
    return ApiResponse(data=images, message="查询成功")


@router.post(
    "/images/cleanup",
    summary="删除所有未引用图片",
    description="重新扫描引用后清理未引用图片，仅管理员可访问",
    response_model=ApiResponse[int],
)
async def cleanup_unreferenced_images(
    request: ImageCleanupRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[int]:
    """清理未引用图片。"""
    delete_count = await get_upload_service(session).cleanup_unreferenced_images(
        confirm=request.confirm,
    )
    return ApiResponse(data=delete_count, message=f"已删除未引用图片 {delete_count} 张")


@router.post(
    "/image/delete",
    summary="删除已上传图片",
    description="删除未被题目引用的图片，仅管理员可访问",
    response_model=ApiResponse[None],
)
async def delete_image(
    request: ImageDeleteRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[None]:
    """删除指定图片。"""
    await get_upload_service(session).delete_image(
        request.filename,
        confirm=request.confirm,
    )
    return ApiResponse(message="删除成功")
