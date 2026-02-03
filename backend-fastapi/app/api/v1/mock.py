"""
模拟题管理模块路由
提供模拟题管理的RESTful API接口
遵循Spring Boot旧项目接口规范
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.connection import get_async_session
from app.services.mock_service import MockService
from app.schemas.mock import (
    MockQueryParams,
    MockCreateRequest,
    MockUpdateRequest,
    MockResponse,
    MockSourceStatResponse,
    MockSourcesResponse,
    MockCategoryStatsResponse,
    PaginatedMockResponse
)
from app.schemas.common import Response
from app.middleware.auth import get_current_user, get_current_admin, AuthUser

router = APIRouter()


@router.get(
    "",
    response_model=Response[PaginatedMockResponse],
    summary="分页查询模拟题",
    description="支持多条件筛选、分页、排序"
)
async def get_mock_questions(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页大小"),
    source: Optional[str] = Query(default=None, description="来源机构筛选"),
    category: Optional[str] = Query(default=None, description="分类筛选"),
    subject_id: Optional[int] = Query(default=None, description="科目ID筛选"),
    no_category: Optional[bool] = Query(default=None, description="是否筛选无分类"),
    keyword: Optional[str] = Query(default=None, description="关键词搜索"),
    sort_field: str = Query(default="update_time", description="排序字段"),
    sort_order: str = Query(default="desc", description="排序方向"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[PaginatedMockResponse]:
    """
    分页查询模拟题

    支持按来源、分类、科目、关键词等条件筛选，支持分页和排序。
    """
    params = MockQueryParams(
        page=page,
        page_size=page_size,
        source=source,
        category=category,
        subject_id=subject_id,
        no_category=no_category,
        keyword=keyword,
        sort_field=sort_field,
        sort_order=sort_order
    )
    service = MockService(session)
    result = await service.get_paginated(params)
    return Response(data=result)


@router.get(
    "/source/{source}",
    response_model=Response[List[MockResponse]],
    summary="根据来源查询模拟题",
    description="查询指定来源机构的所有模拟题"
)
async def find_by_source(
    source: str = Path(..., description="来源机构"),
    category: Optional[str] = Query(default=None, description="分类"),
    subject_id: Optional[int] = Query(default=None, description="科目ID"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[MockResponse]]:
    """
    根据来源查询模拟题

    - 权限：公开
    - 返回指定来源机构的所有模拟题列表
    """
    service = MockService(session)
    mocks = await service.find_by_source(source, category, subject_id)
    return Response(data=mocks)


@router.get(
    "/source-stats",
    response_model=Response[List[MockSourceStatResponse]],
    summary="查询来源统计",
    description="按来源机构统计模拟题数量"
)
async def get_source_stats(
    category: Optional[str] = Query(default=None, description="分类筛选"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[MockSourceStatResponse]]:
    """
    获取来源统计

    - 权限：公开
    - 返回各来源机构的模拟题数量统计
    """
    service = MockService(session)
    stats = await service.get_source_stats(category)
    return Response(data=stats)


@router.get(
    "/sources",
    response_model=Response[MockSourcesResponse],
    summary="查询所有来源机构",
    description="获取所有不重复的来源机构列表"
)
async def get_all_sources(
    session: AsyncSession = Depends(get_async_session)
) -> Response[MockSourcesResponse]:
    """
    获取来源列表

    - 权限：公开
    - 返回所有来源机构及其对应的模拟题数量
    """
    service = MockService(session)
    sources = await service.get_sources()
    return Response(data=sources)


@router.get(
    "/categories/{subject_id}",
    response_model=Response[List[str]],
    summary="查询科目下的分类",
    description="查询指定科目下实际存在模拟题的分类列表"
)
async def find_categories_by_subject(
    subject_id: int = Path(..., description="科目ID"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[str]]:
    """
    查询科目下的分类列表

    - 权限：公开
    - 返回指定科目下实际存在模拟题的分类名列表（去重）
    """
    service = MockService(session)
    categories = await service.find_categories_by_subject(subject_id)
    return Response(data=categories)


@router.get(
    "/category-stats/{subject_id}",
    response_model=Response[MockCategoryStatsResponse],
    summary="查询科目下的分类（带统计）",
    description="查询指定科目下实际存在模拟题的分类列表，包含每个分类的题目数量"
)
async def find_category_stats_by_subject(
    subject_id: int = Path(..., description="科目ID"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[MockCategoryStatsResponse]:
    """
    获取分类统计

    - 权限：公开
    - 按科目获取模拟题的分类统计（从JSON数组展开）
    """
    service = MockService(session)
    stats = await service.get_category_stats(subject_id)
    return Response(data=stats)


@router.get(
    "/subject-stats",
    response_model=Response[List[dict]],
    summary="按科目统计数量",
    description="按科目分组统计模拟题数量"
)
async def count_by_subject(
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[dict]]:
    """
    按科目统计模拟题数量

    - 权限：公开
    - 返回各科目的模拟题数量统计
    """
    service = MockService(session)
    stats = await service.count_by_subject()
    return Response(data=stats)


@router.get(
    "/titles/{source}",
    response_model=Response[List[str]],
    summary="根据来源查询标题列表",
    description="获取指定来源下所有不重复的标题列表"
)
async def get_titles_by_source(
    source: str = Path(..., description="来源机构"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[str]]:
    """
    根据来源查询标题列表

    - 权限：公开
    - 获取指定来源下所有不重复的标题列表
    - 用途：编辑模拟题时，根据选择的来源动态加载标题下拉选项
    """
    service = MockService(session)
    titles = await service.get_titles_by_source(source)
    return Response(data=titles)


@router.get(
    "/{mock_id}",
    response_model=Response[MockResponse],
    summary="查询模拟题详情",
    description="根据ID查询模拟题详细信息"
)
async def get_mock_detail(
    mock_id: int = Path(..., description="模拟题ID"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[MockResponse]:
    """
    按ID查询模拟题详情

    - 权限：公开
    """
    service = MockService(session)
    mock = await service.get_by_id(mock_id)
    return Response(data=mock)


@router.post(
    "",
    response_model=Response[MockResponse],
    summary="创建模拟题",
    description="创建新模拟题，仅管理员可访问"
)
async def create_mock(
    request: MockCreateRequest,
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[MockResponse]:
    """
    创建模拟题

    - 权限：ADMIN
    - 创建时自动关联当前管理员为作者，并校验唯一性约束
    """
    service = MockService(session)
    mock = await service.create(request, current_user.user_id)
    return Response(data=mock, message="创建成功")


@router.post(
    "/{mock_id}",
    response_model=Response[MockResponse],
    summary="更新模拟题",
    description="更新指定模拟题的信息，仅管理员可访问"
)
async def update_mock(
    mock_id: int = Path(..., description="模拟题ID"),
    request: MockUpdateRequest = None,
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[MockResponse]:
    """
    更新模拟题

    - 权限：ADMIN
    - 支持部分字段更新，更新时校验唯一性约束
    """
    service = MockService(session)
    mock = await service.update(mock_id, request)
    return Response(data=mock, message="更新成功")


@router.post(
    "/{mock_id}/delete",
    response_model=Response[None],
    summary="删除模拟题",
    description="删除指定模拟题，仅管理员可访问"
)
async def delete_mock(
    mock_id: int = Path(..., description="模拟题ID"),
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[None]:
    """
    删除模拟题

    - 权限：ADMIN
    - 物理删除模拟题记录，无法撤销
    """
    service = MockService(session)
    await service.delete(mock_id)
    return Response(message="删除成功")
