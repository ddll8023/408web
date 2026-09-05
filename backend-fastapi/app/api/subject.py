"""科目管理 HTTP 路由。"""
from fastapi import APIRouter, Depends, Path, status

from app.api.dependencies import AuthUser, SessionDep, get_current_admin
from app.schemas.common import ApiResponse
from app.schemas.subject import (
    SubjectCodeRequest,
    SubjectCreateRequest,
    SubjectResponse,
    SubjectUpdateRequest,
)
from app.services.subject_service import SubjectService


router = APIRouter()


@router.post(
    "/query",
    response_model=ApiResponse[list[SubjectResponse]],
    summary="查询启用科目列表",
    description="查询所有启用状态的科目（带题目统计）",
)
async def get_subjects(session: SessionDep) -> ApiResponse[list[SubjectResponse]]:
    """查询启用科目列表。"""
    subjects = await SubjectService(session).get_enabled_subjects()
    return ApiResponse(data=subjects)


@router.post(
    "/query-all",
    response_model=ApiResponse[list[SubjectResponse]],
    summary="查询所有科目",
    description="查询所有科目（包含禁用状态），仅管理员可访问",
)
async def get_all_subjects(
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[list[SubjectResponse]]:
    """查询所有科目。"""
    subjects = await SubjectService(session).get_all_subjects()
    return ApiResponse(data=subjects)


@router.post(
    "/{subject_id}/detail",
    response_model=ApiResponse[SubjectResponse],
    summary="查询科目详情",
    description="根据 ID 查询科目详细信息",
)
async def get_subject_by_id(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[SubjectResponse]:
    """按 ID 查询科目。"""
    subject = await SubjectService(session).get_by_id(subject_id)
    return ApiResponse(data=subject)


@router.post(
    "/query-by-code",
    response_model=ApiResponse[SubjectResponse],
    summary="根据编码查询科目",
    description="根据科目编码查询科目信息",
)
async def get_subject_by_code(
    request: SubjectCodeRequest,
    session: SessionDep,
) -> ApiResponse[SubjectResponse]:
    """按编码查询科目。"""
    subject = await SubjectService(session).get_by_code(request.code)
    return ApiResponse(data=subject)


@router.post(
    "",
    response_model=ApiResponse[SubjectResponse],
    status_code=status.HTTP_200_OK,
    summary="创建科目",
    description="创建新科目，仅管理员可访问",
)
async def create_subject(
    request: SubjectCreateRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[SubjectResponse]:
    """创建科目。"""
    subject = await SubjectService(session).create(request)
    return ApiResponse(data=subject, message="创建成功")


@router.post(
    "/{subject_id}",
    response_model=ApiResponse[SubjectResponse],
    status_code=status.HTTP_200_OK,
    summary="更新科目",
    description="更新指定科目的信息，仅管理员可访问",
)
async def update_subject(
    request: SubjectUpdateRequest,
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[SubjectResponse]:
    """更新科目。"""
    subject = await SubjectService(session).update(subject_id, request)
    return ApiResponse(data=subject, message="更新成功")


@router.post(
    "/{subject_id}/delete",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="删除科目",
    description="删除指定科目，仅管理员可访问",
)
async def delete_subject(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[None]:
    """删除科目。"""
    await SubjectService(session).delete(subject_id)
    return ApiResponse(message="删除成功")
