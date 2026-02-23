"""
章节管理模块路由
"""
from typing import List
from fastapi import APIRouter, Depends, status
from app.database.connection import SessionDep
from app.services.chapter_service import ChapterService
from app.schemas.chapter import (
    ChapterCreateRequest,
    ChapterUpdateRequest,
    ChapterResponse,
    ChapterTreeResponse
)
from app.schemas.common import Response
from app.middleware.auth import get_current_user, get_current_admin, AuthUser

router = APIRouter()


@router.get(
    "/subject/{subject_id}",
    response_model=Response[List[ChapterTreeResponse]],
    summary="查询启用章节树",
    description="根据科目ID查询启用的章节树形结构"
)
async def get_chapter_tree(
    subject_id: int,
    session: SessionDep
) -> Response[List[ChapterTreeResponse]]:
    """
    查询启用章节树

    根据科目ID查询所有启用的章节，并以树形结构返回。

    Args:
        subject_id: 科目ID

    Returns:
        章节树形结构列表
    """
    service = ChapterService(session)
    chapters = await service.get_chapter_tree(subject_id, enabled_only=True)
    return Response(data=chapters)


@router.get(
    "/subject/{subject_id}/all",
    response_model=Response[List[ChapterTreeResponse]],
    summary="查询所有章节树",
    description="根据科目ID查询所有章节（包含禁用状态），仅管理员可访问"
)
async def get_all_chapter_tree(
    session: SessionDep,
    subject_id: int,
    current_user: AuthUser = Depends(get_current_admin)
) -> Response[List[ChapterTreeResponse]]:
    """
    查询所有章节树

    根据科目ID查询所有章节（包含禁用状态），以树形结构返回。

    Args:
        subject_id: 科目ID
        current_user: 当前管理员

    Returns:
        章节树形结构列表
    """
    service = ChapterService(session)
    chapters = await service.get_chapter_tree(subject_id, enabled_only=False)
    return Response(data=chapters)


@router.get(
    "/{chapter_id}",
    response_model=Response[ChapterResponse],
    summary="查询章节详情",
    description="根据ID查询章节详细信息"
)
async def get_chapter_by_id(
    chapter_id: int,
    session: SessionDep
) -> Response[ChapterResponse]:
    """
    按ID查询章节

    Args:
        chapter_id: 章节ID

    Returns:
        章节详情
    """
    service = ChapterService(session)
    chapter = await service.get_by_id(chapter_id)
    return Response(data=chapter)


@router.post(
    "",
    response_model=Response[ChapterResponse],
    status_code=status.HTTP_200_OK,
    summary="创建章节",
    description="创建新章节，仅管理员可访问"
)
async def create_chapter(
    session: SessionDep,
    request: ChapterCreateRequest,
    current_user: AuthUser = Depends(get_current_admin)
) -> Response[ChapterResponse]:
    """
    创建章节

    Args:
        request: 章节信息
        current_user: 当前管理员

    Returns:
        创建的章节
    """
    service = ChapterService(session)
    chapter = await service.create(request)
    return Response(data=chapter, message="创建成功")


@router.post(
    "/{chapter_id}",
    response_model=Response[ChapterResponse],
    status_code=status.HTTP_200_OK,
    summary="更新章节",
    description="更新指定章节的信息，仅管理员可访问"
)
async def update_chapter(
    session: SessionDep,
    chapter_id: int,
    request: ChapterUpdateRequest,
    current_user: AuthUser = Depends(get_current_admin)
) -> Response[ChapterResponse]:
    """
    更新章节

    Args:
        chapter_id: 章节ID
        request: 章节信息
        current_user: 当前管理员

    Returns:
        更新后的章节
    """
    service = ChapterService(session)
    chapter = await service.update(chapter_id, request)
    return Response(data=chapter, message="更新成功")


@router.post(
    "/{chapter_id}/delete",
    response_model=Response[None],
    status_code=status.HTTP_200_OK,
    summary="删除章节",
    description="删除指定章节及其子章节，仅管理员可访问"
)
async def delete_chapter(
    session: SessionDep,
    chapter_id: int,
    current_user: AuthUser = Depends(get_current_admin)
) -> Response[None]:
    """
    删除章节

    删除章节及其所有子章节（由数据库外键约束级联删除）。

    Args:
        chapter_id: 章节ID
        current_user: 当前管理员
    """
    service = ChapterService(session)
    await service.delete(chapter_id)
    return Response(message="删除成功")
