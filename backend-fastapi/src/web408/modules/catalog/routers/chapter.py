"""章节管理 HTTP 路由。"""
from fastapi import APIRouter, Depends, Path, status

from web408.api.dependencies import SessionDep
from web408.modules.auth.dependencies import AuthUser, get_current_admin
from web408.modules.catalog.schemas.chapter import (
    ChapterCreateRequest,
    ChapterResponse,
    ChapterTreeResponse,
    ChapterUpdateRequest,
)
from web408.schemas.common import ApiResponse
from web408.modules.catalog.chapter_service import ChapterService


router = APIRouter()


@router.post(
    "/subject/{subject_id}",
    response_model=ApiResponse[list[ChapterTreeResponse]],
    summary="查询启用章节树",
    description="根据科目 ID 查询启用的章节树形结构",
)
async def get_chapter_tree(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[list[ChapterTreeResponse]]:
    """查询启用章节树。"""
    chapters = await ChapterService(session).get_chapter_tree(subject_id, enabled_only=True)
    return ApiResponse(data=chapters)


@router.post(
    "/subject/{subject_id}/all",
    response_model=ApiResponse[list[ChapterTreeResponse]],
    summary="查询所有章节树",
    description="根据科目 ID 查询所有章节，仅管理员可访问",
)
async def get_all_chapter_tree(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[list[ChapterTreeResponse]]:
    """查询所有章节树。"""
    chapters = await ChapterService(session).get_chapter_tree(subject_id, enabled_only=False)
    return ApiResponse(data=chapters)


@router.post(
    "/{chapter_id}/detail",
    response_model=ApiResponse[ChapterResponse],
    summary="查询章节详情",
    description="根据 ID 查询章节详细信息",
)
async def get_chapter_by_id(
    session: SessionDep,
    chapter_id: int = Path(..., ge=1, description="章节 ID"),
) -> ApiResponse[ChapterResponse]:
    """按 ID 查询章节。"""
    chapter = await ChapterService(session).get_by_id(chapter_id)
    return ApiResponse(data=chapter)


@router.post(
    "",
    response_model=ApiResponse[ChapterResponse],
    status_code=status.HTTP_200_OK,
    summary="创建章节",
    description="创建新章节，仅管理员可访问",
)
async def create_chapter(
    request: ChapterCreateRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[ChapterResponse]:
    """创建章节。"""
    chapter = await ChapterService(session).create(request)
    return ApiResponse(data=chapter, message="创建成功")


@router.post(
    "/{chapter_id}",
    response_model=ApiResponse[ChapterResponse],
    status_code=status.HTTP_200_OK,
    summary="更新章节",
    description="更新指定章节的信息，仅管理员可访问",
)
async def update_chapter(
    request: ChapterUpdateRequest,
    session: SessionDep,
    chapter_id: int = Path(..., ge=1, description="章节 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[ChapterResponse]:
    """更新章节。"""
    chapter = await ChapterService(session).update(chapter_id, request)
    return ApiResponse(data=chapter, message="更新成功")


@router.post(
    "/{chapter_id}/delete",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="删除章节",
    description="删除指定章节及其子章节，仅管理员可访问",
)
async def delete_chapter(
    session: SessionDep,
    chapter_id: int = Path(..., ge=1, description="章节 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[None]:
    """删除章节。"""
    await ChapterService(session).delete(chapter_id)
    return ApiResponse(message="删除成功")
