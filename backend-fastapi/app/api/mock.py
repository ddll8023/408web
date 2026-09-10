"""模拟题查询和维护 HTTP 路由。"""
from fastapi import APIRouter, Depends, Path

from app.api.dependencies import SessionDep
from app.modules.auth.dependencies import AuthUser, get_current_admin
from app.schemas.common import ApiResponse
from app.schemas.mock import (
    MockCategoryFilterRequest,
    MockCategoryStatsResponse,
    MockCreateRequest,
    MockDuplicateCheckResponse,
    MockDuplicateRequest,
    MockQueryParams,
    MockResponse,
    MockSourceQueryRequest,
    MockSourceStatResponse,
    MockSourcesResponse,
    MockSubjectStatItem,
    MockUpdateRequest,
    PaginatedMockResponse,
)
from app.services.mock_service import MockService


router = APIRouter()


@router.post(
    "/query",
    response_model=ApiResponse[PaginatedMockResponse],
    summary="分页查询模拟题",
    description="支持多条件筛选、分页和排序",
)
async def get_mock_questions(
    request: MockQueryParams,
    session: SessionDep,
) -> ApiResponse[PaginatedMockResponse]:
    """分页查询模拟题。"""
    result = await MockService(session).get_paginated(request)
    return ApiResponse(data=result)


@router.post(
    "/source/{source}",
    response_model=ApiResponse[list[MockResponse]],
    summary="根据来源查询模拟题",
    description="查询指定来源机构的所有模拟题",
)
async def find_by_source(
    request: MockSourceQueryRequest,
    session: SessionDep,
    source: str = Path(..., min_length=1, max_length=100, description="来源机构"),
) -> ApiResponse[list[MockResponse]]:
    """根据来源查询模拟题。"""
    mocks = await MockService(session).find_by_source(
        source,
        request.category,
        request.subject_id,
    )
    return ApiResponse(data=mocks)


@router.post(
    "/source-stats",
    response_model=ApiResponse[list[MockSourceStatResponse]],
    summary="查询来源统计",
    description="按来源机构统计模拟题数量",
)
async def get_source_stats(
    request: MockCategoryFilterRequest,
    session: SessionDep,
) -> ApiResponse[list[MockSourceStatResponse]]:
    """查询模拟题来源统计。"""
    stats = await MockService(session).get_source_stats(request.category)
    return ApiResponse(data=stats)


@router.post(
    "/sources",
    response_model=ApiResponse[MockSourcesResponse],
    summary="查询所有来源机构",
    description="获取所有不重复的来源机构列表",
)
async def get_all_sources(session: SessionDep) -> ApiResponse[MockSourcesResponse]:
    """查询来源机构列表。"""
    sources = await MockService(session).get_sources()
    return ApiResponse(data=sources)


@router.post(
    "/categories/{subject_id}",
    response_model=ApiResponse[list[str]],
    summary="查询科目下的分类",
    description="查询指定科目下实际存在模拟题的分类列表",
)
async def find_categories_by_subject(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[list[str]]:
    """查询模拟题分类列表。"""
    categories = await MockService(session).find_categories_by_subject(subject_id)
    return ApiResponse(data=categories)


@router.post(
    "/category-stats/{subject_id}",
    response_model=ApiResponse[MockCategoryStatsResponse],
    summary="查询科目下的分类统计",
    description="查询指定科目下模拟题分类及题目数量",
)
async def find_category_stats_by_subject(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[MockCategoryStatsResponse]:
    """查询模拟题分类统计。"""
    stats = await MockService(session).get_category_stats(subject_id)
    return ApiResponse(data=stats)


@router.post(
    "/subject-stats",
    response_model=ApiResponse[list[MockSubjectStatItem]],
    summary="按科目统计数量",
    description="按科目分组统计模拟题数量",
)
async def count_by_subject(session: SessionDep) -> ApiResponse[list[MockSubjectStatItem]]:
    """按科目统计模拟题数量。"""
    stats = await MockService(session).count_by_subject()
    return ApiResponse(data=stats)


@router.post(
    "/titles/{source}",
    response_model=ApiResponse[list[str]],
    summary="根据来源查询标题列表",
    description="获取指定来源下所有不重复的标题列表",
)
async def get_titles_by_source(
    session: SessionDep,
    source: str = Path(..., min_length=1, max_length=100, description="来源机构"),
) -> ApiResponse[list[str]]:
    """根据来源查询标题列表。"""
    titles = await MockService(session).get_titles_by_source(source)
    return ApiResponse(data=titles)


@router.post(
    "/{mock_id}/detail",
    response_model=ApiResponse[MockResponse],
    summary="查询模拟题详情",
    description="根据 ID 查询模拟题详细信息",
)
async def get_mock_detail(
    session: SessionDep,
    mock_id: int = Path(..., ge=1, description="模拟题 ID"),
) -> ApiResponse[MockResponse]:
    """查询模拟题详情。"""
    mock = await MockService(session).get_by_id(mock_id)
    return ApiResponse(data=mock)


@router.post(
    "/check-duplicate",
    response_model=ApiResponse[MockDuplicateCheckResponse],
    summary="检查模拟题重复",
    description="检查来源、标题和题号组合是否已存在，仅管理员可访问",
)
async def check_mock_duplicate(
    request: MockDuplicateRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[MockDuplicateCheckResponse]:
    """检查模拟题重复。"""
    existing = await MockService(session).check_duplicate(
        request.source,
        request.title,
        request.question_number,
        request.exclude_id,
    )
    return ApiResponse(data=existing)


@router.post(
    "",
    response_model=ApiResponse[MockResponse],
    summary="创建模拟题",
    description="创建新模拟题，仅管理员可访问",
)
async def create_mock(
    request: MockCreateRequest,
    session: SessionDep,
    admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[MockResponse]:
    """创建模拟题。"""
    mock = await MockService(session).create(request, admin.user_id)
    return ApiResponse(data=mock, message="创建成功")


@router.post(
    "/{mock_id}",
    response_model=ApiResponse[MockResponse],
    summary="更新模拟题",
    description="更新指定模拟题的信息，仅管理员可访问",
)
async def update_mock(
    request: MockUpdateRequest,
    session: SessionDep,
    mock_id: int = Path(..., ge=1, description="模拟题 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[MockResponse]:
    """更新模拟题。"""
    mock = await MockService(session).update(mock_id, request)
    return ApiResponse(data=mock, message="更新成功")


@router.post(
    "/{mock_id}/delete",
    response_model=ApiResponse[None],
    summary="删除模拟题",
    description="删除指定模拟题，仅管理员可访问",
)
async def delete_mock(
    session: SessionDep,
    mock_id: int = Path(..., ge=1, description="模拟题 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[None]:
    """删除模拟题。"""
    await MockService(session).delete(mock_id)
    return ApiResponse(message="删除成功")
