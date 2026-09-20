"""改编题查询、维护、来源解析与覆盖统计 HTTP 路由。"""
from fastapi import APIRouter, Depends, Path
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.api.dependencies import SessionDep
from web408.modules.adaptation.command_service import AdaptationCommandService
from web408.modules.adaptation.query_service import AdaptationQueryService
from web408.modules.adaptation.schemas import (
    AdaptationBySourceItem,
    AdaptationBySourceRequest,
    AdaptationCoverageItem,
    AdaptationCoverageRequest,
    AdaptationCreateRequest,
    AdaptationDuplicateCheckResponse,
    AdaptationDuplicateRequest,
    AdaptationQueryParams,
    AdaptationResponse,
    AdaptationSourceLookupItem,
    AdaptationSourceLookupRequest,
    AdaptationSubjectStatItem,
    AdaptationUpdateRequest,
    PaginatedAdaptationResponse,
)
from web408.modules.auth.dependencies import AuthUser, get_current_admin
from web408.schemas.common import ApiResponse


router = APIRouter()


def _get_command_service(session: AsyncSession) -> AdaptationCommandService:
    """创建共享查询服务的改编题写入用例。"""
    return AdaptationCommandService(session, AdaptationQueryService(session))


@router.post(
    "/query",
    response_model=ApiResponse[PaginatedAdaptationResponse],
    summary="分页查询改编题",
    description="支持科目、分类、题型、来源和关键词筛选，以及分页和排序",
)
async def get_adaptations(
    request: AdaptationQueryParams,
    session: SessionDep,
) -> ApiResponse[PaginatedAdaptationResponse]:
    """分页查询改编题。"""
    result = await AdaptationQueryService(session).get_paginated(request)
    return ApiResponse(data=result)


@router.post(
    "/subject-stats",
    response_model=ApiResponse[list[AdaptationSubjectStatItem]],
    summary="按科目统计改编题",
    description="返回各科目的改编题数量，包含零题目科目",
)
async def get_subject_stats(
    session: SessionDep,
) -> ApiResponse[list[AdaptationSubjectStatItem]]:
    """按科目统计改编题数量。"""
    stats = await AdaptationQueryService(session).count_by_subject()
    return ApiResponse(data=stats)


@router.post(
    "/categories/{subject_id}",
    response_model=ApiResponse[list[str]],
    summary="查询科目下的改编题分类",
    description="返回科目下改编题实际使用的分类名称",
)
async def get_categories_by_subject(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[list[str]]:
    """查询科目下的改编题分类。"""
    categories = await AdaptationQueryService(session).find_categories_by_subject(subject_id)
    return ApiResponse(data=categories)


@router.post(
    "/check-duplicate",
    response_model=ApiResponse[AdaptationDuplicateCheckResponse],
    summary="检查改编题重复",
    description="检查标题与题号组合是否已存在，并提示已被引用的来源，仅管理员可访问",
)
async def check_adaptation_duplicate(
    request: AdaptationDuplicateRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[AdaptationDuplicateCheckResponse]:
    """检查改编题重复与同源引用。"""
    result = await AdaptationQueryService(session).check_duplicate(
        request.title,
        request.question_number,
        request.sources,
        request.exclude_id,
    )
    return ApiResponse(data=result)


@router.post(
    "/source-lookup",
    response_model=ApiResponse[list[AdaptationSourceLookupItem]],
    summary="批量解析改编来源",
    description="按年份与题号批量查询真题库，返回是否存在及原题摘要",
)
async def lookup_adaptation_sources(
    request: AdaptationSourceLookupRequest,
    session: SessionDep,
) -> ApiResponse[list[AdaptationSourceLookupItem]]:
    """批量解析改编来源。"""
    items = await AdaptationQueryService(session).lookup_sources(request.sources)
    return ApiResponse(data=items)


@router.post(
    "/by-source",
    response_model=ApiResponse[list[AdaptationBySourceItem]],
    summary="按真题来源反查改编题",
    description="查询引用指定年份与题号的改编题列表",
)
async def find_adaptations_by_source(
    request: AdaptationBySourceRequest,
    session: SessionDep,
) -> ApiResponse[list[AdaptationBySourceItem]]:
    """按真题来源反查改编题。"""
    items = await AdaptationQueryService(session).find_by_source(request)
    return ApiResponse(data=items)


@router.post(
    "/source-coverage",
    response_model=ApiResponse[list[AdaptationCoverageItem]],
    summary="统计真题改编覆盖",
    description="按年份统计真题总题数、已改编题数、未改编题号与悬空来源数",
)
async def get_adaptation_coverage(
    request: AdaptationCoverageRequest,
    session: SessionDep,
) -> ApiResponse[list[AdaptationCoverageItem]]:
    """统计真题改编覆盖情况。"""
    items = await AdaptationQueryService(session).get_coverage(request)
    return ApiResponse(data=items)


@router.post(
    "",
    response_model=ApiResponse[AdaptationResponse],
    summary="创建改编题",
    description="创建改编题及其来源引用，仅管理员可访问",
)
async def create_adaptation(
    request: AdaptationCreateRequest,
    session: SessionDep,
    admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[AdaptationResponse]:
    """创建改编题。"""
    adaptation = await _get_command_service(session).create(request, admin.user_id)
    return ApiResponse(data=adaptation, message="创建成功")


@router.post(
    "/{adaptation_id}/detail",
    response_model=ApiResponse[AdaptationResponse],
    summary="查询改编题详情",
    description="根据 ID 查询改编题详情及来源引用",
)
async def get_adaptation_detail(
    session: SessionDep,
    adaptation_id: int = Path(..., ge=1, description="改编题 ID"),
) -> ApiResponse[AdaptationResponse]:
    """查询改编题详情。"""
    adaptation = await AdaptationQueryService(session).get_by_id(adaptation_id)
    return ApiResponse(data=adaptation)


@router.post(
    "/{adaptation_id}",
    response_model=ApiResponse[AdaptationResponse],
    summary="更新改编题",
    description="更新指定改编题及其来源引用，仅管理员可访问",
)
async def update_adaptation(
    request: AdaptationUpdateRequest,
    session: SessionDep,
    adaptation_id: int = Path(..., ge=1, description="改编题 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[AdaptationResponse]:
    """更新改编题。"""
    adaptation = await _get_command_service(session).update(adaptation_id, request)
    return ApiResponse(data=adaptation, message="更新成功")


@router.post(
    "/{adaptation_id}/delete",
    response_model=ApiResponse[None],
    summary="删除改编题",
    description="删除指定改编题及其来源引用，仅管理员可访问",
)
async def delete_adaptation(
    session: SessionDep,
    adaptation_id: int = Path(..., ge=1, description="改编题 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[None]:
    """删除改编题。"""
    await _get_command_service(session).delete(adaptation_id)
    return ApiResponse(message="删除成功")
