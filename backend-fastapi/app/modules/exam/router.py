"""真题查询、维护和导出 HTTP 路由。"""
from fastapi import APIRouter, Depends, Path
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import SessionDep
from app.modules.auth.dependencies import AuthUser, get_current_admin
from app.modules.exam.command_service import ExamCommandService
from app.modules.exam.query_service import ExamQueryService
from app.modules.exam.schemas import (
    ExamByCategoryRequest,
    ExamCreateRequest,
    ExamDuplicateCheckResponse,
    ExamDuplicateRequest,
    ExamIndexRequest,
    ExamNavItem,
    ExamQueryParams,
    ExamResponse,
    ExamUpdateRequest,
    ExamYearQueryRequest,
    ExamYearStatResponse,
    PaginatedExamResponse,
)
from app.schemas.common import ApiResponse


router = APIRouter()


def _get_command_service(session: AsyncSession) -> ExamCommandService:
    """创建共享查询服务的真题写入用例。"""
    return ExamCommandService(session, ExamQueryService(session))


@router.post(
    "/query",
    response_model=ApiResponse[PaginatedExamResponse],
    summary="分页查询真题",
    description="支持多条件筛选、分页和排序",
)
async def get_exams(
    request: ExamQueryParams,
    session: SessionDep,
) -> ApiResponse[PaginatedExamResponse]:
    """分页查询真题。"""
    result = await ExamQueryService(session).get_paginated(request)
    return ApiResponse(data=result)


@router.post(
    "/year/{year}",
    response_model=ApiResponse[list[ExamResponse]],
    summary="根据年份查询真题",
    description="查询指定年份的所有真题",
)
async def find_by_year(
    request: ExamYearQueryRequest,
    session: SessionDep,
    year: int = Path(..., ge=1990, le=2100, description="年份"),
) -> ApiResponse[list[ExamResponse]]:
    """根据年份查询真题。"""
    exams = await ExamQueryService(session).find_by_year(
        year,
        request.category,
        request.subject_id,
    )
    return ApiResponse(data=exams)


@router.post(
    "/categories/{subject_id}",
    response_model=ApiResponse[list[str]],
    summary="查询科目下的分类",
    description="查询指定科目下实际存在真题的分类列表",
)
async def get_categories_by_subject(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[list[str]]:
    """查询科目下的真题分类。"""
    categories = await ExamQueryService(session).get_categories_by_subject(subject_id)
    return ApiResponse(data=categories)


@router.post(
    "/year-stats",
    response_model=ApiResponse[list[ExamYearStatResponse]],
    summary="查询年份统计",
    description="按年份统计真题数量",
)
async def get_year_stats(
    request: ExamIndexRequest,
    session: SessionDep,
) -> ApiResponse[list[ExamYearStatResponse]]:
    """查询年份统计。"""
    stats = await ExamQueryService(session).get_year_stats(request.category)
    return ApiResponse(data=stats)


@router.post(
    "/index",
    response_model=ApiResponse[list[ExamResponse]],
    summary="查询真题索引",
    description="查询用于年份导航的真题索引数据",
)
async def find_all_for_index(
    request: ExamIndexRequest,
    session: SessionDep,
) -> ApiResponse[list[ExamResponse]]:
    """查询真题索引。"""
    exams = await ExamQueryService(session).find_all_for_index(request.category)
    return ApiResponse(data=exams)


@router.post(
    "/nav-index",
    response_model=ApiResponse[list[ExamNavItem]],
    summary="查询真题导航索引",
    description="查询用于侧边栏年份导航的轻量级索引数据",
)
async def find_for_nav_index(
    request: ExamIndexRequest,
    session: SessionDep,
) -> ApiResponse[list[ExamNavItem]]:
    """查询轻量级真题导航索引。"""
    exams = await ExamQueryService(session).find_for_nav_index(request.category)
    return ApiResponse(data=exams)


@router.post(
    "/by-category",
    response_model=ApiResponse[list[ExamResponse]],
    summary="根据科目和分类查询真题",
    description="查询指定科目和分类的真题列表",
)
async def find_by_subject_and_category(
    request: ExamByCategoryRequest,
    session: SessionDep,
) -> ApiResponse[list[ExamResponse]]:
    """按科目和分类查询真题。"""
    exams = await ExamQueryService(session).find_by_subject_and_category(
        request.subject_id,
        request.category,
    )
    return ApiResponse(data=exams)


@router.post(
    "/{exam_id}/detail",
    response_model=ApiResponse[ExamResponse],
    summary="查询真题详情",
    description="根据 ID 查询真题详细信息",
)
async def get_exam_detail(
    session: SessionDep,
    exam_id: int = Path(..., ge=1, description="真题 ID"),
) -> ApiResponse[ExamResponse]:
    """查询真题详情。"""
    exam = await ExamQueryService(session).get_by_id(exam_id)
    return ApiResponse(data=exam)


@router.post(
    "/check-duplicate",
    response_model=ApiResponse[ExamDuplicateCheckResponse],
    summary="检查真题重复",
    description="检查年份和题号组合是否已存在，仅管理员可访问",
)
async def check_exam_duplicate(
    request: ExamDuplicateRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[ExamDuplicateCheckResponse]:
    """检查真题重复。"""
    existing = await ExamQueryService(session).check_duplicate(
        request.year,
        request.question_number,
        request.exclude_id,
    )
    return ApiResponse(data=existing)


@router.post(
    "",
    response_model=ApiResponse[ExamResponse],
    summary="创建真题",
    description="创建新真题，仅管理员可访问",
)
async def create_exam(
    request: ExamCreateRequest,
    session: SessionDep,
    admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[ExamResponse]:
    """创建真题。"""
    exam = await _get_command_service(session).create(request, admin.user_id)
    return ApiResponse(data=exam, message="创建成功")


@router.post(
    "/{exam_id}",
    response_model=ApiResponse[ExamResponse],
    summary="更新真题",
    description="更新指定真题的信息，仅管理员可访问",
)
async def update_exam(
    request: ExamUpdateRequest,
    session: SessionDep,
    exam_id: int = Path(..., ge=1, description="真题 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[ExamResponse]:
    """更新真题。"""
    exam = await _get_command_service(session).update(exam_id, request)
    return ApiResponse(data=exam, message="更新成功")


@router.post(
    "/{exam_id}/delete",
    response_model=ApiResponse[None],
    summary="删除真题",
    description="删除指定真题，仅管理员可访问",
)
async def delete_exam(
    session: SessionDep,
    exam_id: int = Path(..., ge=1, description="真题 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[None]:
    """删除真题。"""
    await _get_command_service(session).delete(exam_id)
    return ApiResponse(message="删除成功")
