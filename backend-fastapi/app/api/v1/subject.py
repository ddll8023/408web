"""
科目管理模块路由
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.connection import get_async_session
from app.services.subject_service import SubjectService
from app.schemas.subject import (
    SubjectCreateRequest,
    SubjectUpdateRequest,
    SubjectResponse
)
from app.schemas.common import Response
from app.middleware.auth import get_current_user, get_current_admin, AuthUser

router = APIRouter()


@router.get(
    "",
    response_model=Response[List[SubjectResponse]],
    summary="查询启用科目列表",
    description="查询所有启用状态的科目（带题目统计）"
)
async def get_subjects(
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[SubjectResponse]]:
    """
    查询启用科目列表

    Returns:
        启用科目列表（带题目统计）
    """
    service = SubjectService(session)
    subjects = await service.get_enabled_subjects()
    return Response(data=subjects)


@router.get(
    "/all",
    response_model=Response[List[SubjectResponse]],
    summary="查询所有科目",
    description="查询所有科目（包含禁用状态），仅管理员可访问"
)
async def get_all_subjects(
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[SubjectResponse]]:
    """
    查询所有科目

    Returns:
        所有科目列表
    """
    service = SubjectService(session)
    subjects = await service.get_all_subjects()
    return Response(data=subjects)


@router.get(
    "/{subject_id}",
    response_model=Response[SubjectResponse],
    summary="查询科目详情",
    description="根据ID查询科目详细信息"
)
async def get_subject_by_id(
    subject_id: int,
    session: AsyncSession = Depends(get_async_session)
) -> Response[SubjectResponse]:
    """
    按ID查询科目

    Args:
        subject_id: 科目ID

    Returns:
        科目详情
    """
    service = SubjectService(session)
    subject = await service.get_by_id(subject_id)
    return Response(data=subject)


@router.get(
    "/code/{code}",
    response_model=Response[SubjectResponse],
    summary="根据编码查询科目",
    description="根据科目编码查询科目信息"
)
async def get_subject_by_code(
    code: str,
    session: AsyncSession = Depends(get_async_session)
) -> Response[SubjectResponse]:
    """
    按编码查询科目

    Args:
        code: 科目编码

    Returns:
        科目详情
    """
    service = SubjectService(session)
    subject = await service.get_by_code(code)
    return Response(data=subject)


@router.post(
    "",
    response_model=Response[SubjectResponse],
    status_code=status.HTTP_200_OK,
    summary="创建科目",
    description="创建新科目，仅管理员可访问"
)
async def create_subject(
    request: SubjectCreateRequest,
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[SubjectResponse]:
    """
    创建科目

    Args:
        request: 科目信息
        current_user: 当前管理员

    Returns:
        创建的科目
    """
    service = SubjectService(session)
    subject = await service.create(request)
    return Response(data=subject, message="创建成功")


@router.post(
    "/{subject_id}",
    response_model=Response[SubjectResponse],
    status_code=status.HTTP_200_OK,
    summary="更新科目",
    description="更新指定科目的信息，仅管理员可访问"
)
async def update_subject(
    subject_id: int,
    request: SubjectUpdateRequest,
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[SubjectResponse]:
    """
    更新科目

    Args:
        subject_id: 科目ID
        request: 科目信息
        current_user: 当前管理员

    Returns:
        更新后的科目
    """
    service = SubjectService(session)
    subject = await service.update(subject_id, request)
    return Response(data=subject, message="更新成功")


@router.post(
    "/{subject_id}/delete",
    response_model=Response[None],
    status_code=status.HTTP_200_OK,
    summary="删除科目",
    description="删除指定科目，仅管理员可访问"
)
async def delete_subject(
    subject_id: int,
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[None]:
    """
    删除科目

    Args:
        subject_id: 科目ID
        current_user: 当前管理员
    """
    service = SubjectService(session)
    await service.delete(subject_id)
    return Response(message="删除成功")
