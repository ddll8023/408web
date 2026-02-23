"""
真题管理模块路由
提供真题管理的RESTful API接口
遵循Spring Boot旧项目接口规范
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, Response as FastAPIResponse
from app.database.connection import SessionDep
from app.services.exam_service import ExamService
from app.schemas.exam import (
    ExamQueryParams,
    ExamCreateRequest,
    ExamUpdateRequest,
    ExamResponse,
    ExamYearStatResponse,
    ExamCategoryStatsResponse,
    ExamDuplicateCheckResponse,
    ExamIndexResponse,
    ExamNavItem,
    PaginatedExamResponse,
    ExportResultResponse
)
from app.schemas.common import Response
from app.middleware.auth import get_current_user, get_current_admin, AuthUser

router = APIRouter()


@router.get(
    "",
    response_model=Response[PaginatedExamResponse],
    summary="分页查询真题",
    description="支持多条件筛选、分页、排序"
)
async def get_exams(
    session: SessionDep,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页大小"),
    year: Optional[int] = Query(default=None, description="年份筛选"),
    category: Optional[str] = Query(default=None, description="分类筛选"),
    subject_id: Optional[int] = Query(default=None, description="科目ID筛选"),
    no_category: Optional[bool] = Query(default=None, description="是否筛选无分类"),
    keyword: Optional[str] = Query(default=None, description="关键词搜索"),
    sort_field: str = Query(default="update_time", description="排序字段"),
    sort_order: str = Query(default="desc", description="排序方向")
) -> Response[PaginatedExamResponse]:
    """
    分页查询真题

    支持按年份、分类、科目、关键词等条件筛选，支持分页和排序。
    """
    params = ExamQueryParams(
        page=page,
        page_size=page_size,
        year=year,
        category=category,
        subject_id=subject_id,
        no_category=no_category,
        keyword=keyword,
        sort_field=sort_field,
        sort_order=sort_order
    )
    service = ExamService(session)
    result = await service.get_paginated(params)
    return Response(data=result)


@router.get(
    "/year/{year}",
    response_model=Response[List[ExamResponse]],
    summary="根据年份查询真题",
    description="查询指定年份的所有真题"
)
async def find_by_year(
    session: SessionDep,
    year: int = Path(..., description="年份"),
    category: Optional[str] = Query(default=None, description="分类"),
    subject_id: Optional[int] = Query(default=None, description="科目ID")
) -> Response[List[ExamResponse]]:
    """
    根据年份查询真题

    - 权限：公开
    - 返回指定年份的所有真题列表
    """
    service = ExamService(session)
    exams = await service.find_by_year(year, category, subject_id)
    return Response(data=exams)


@router.get(
    "/categories/{subject_id}",
    response_model=Response[List[str]],
    summary="查询科目下的分类",
    description="查询指定科目下实际存在真题的分类列表"
)
async def get_categories_by_subject(
    session: SessionDep,
    subject_id: int = Path(..., description="科目ID")
) -> Response[List[str]]:
    """
    查询科目下的分类列表

    - 权限：公开
    - 返回指定科目下实际存在真题的分类名列表（去重）
    """
    service = ExamService(session)
    categories = await service.get_categories_by_subject(subject_id)
    return Response(data=categories)


@router.get(
    "/year-stats",
    response_model=Response[List[ExamYearStatResponse]],
    summary="查询年份统计",
    description="按年份统计真题数量"
)
async def get_year_stats(
    session: SessionDep,
    category: Optional[str] = Query(default=None, description="分类筛选")
) -> Response[List[ExamYearStatResponse]]:
    """
    获取年份统计

    - 权限：公开
    - 返回各年份的真题数量统计，区分选择题和主观题
    """
    service = ExamService(session)
    stats = await service.get_year_stats(category)
    return Response(data=stats)


@router.get(
    "/index",
    response_model=Response[List[ExamResponse]],
    summary="查询真题索引",
    description="查询用于年份导航的真题索引数据"
)
async def find_all_for_index(
    session: SessionDep,
    category: Optional[str] = Query(default=None, description="分类筛选")
) -> Response[List[ExamResponse]]:
    """
    获取真题索引数据

    - 权限：公开
    - 返回(year, question_number, id)列表，用于前端构建索引导航
    """
    service = ExamService(session)
    exams = await service.find_all_for_index(category)
    return Response(data=exams)


@router.get(
    "/nav-index",
    response_model=Response[List[ExamNavItem]],
    summary="查询真题导航索引（轻量级）",
    description="查询用于侧边栏年份导航的轻量级真题索引数据"
)
async def find_for_nav_index(
    session: SessionDep,
    category: Optional[str] = Query(default=None, description="分类筛选")
) -> Response[List[ExamNavItem]]:
    """
    获取轻量级真题导航索引数据

    - 权限：公开
    - 只返回导航所需字段(id, year, questionNumber, title, category)
    - 数据量比 /index 小很多，用于侧边栏快速加载
    """
    service = ExamService(session)
    exams = await service.find_for_nav_index(category)
    return Response(data=exams)


@router.get(
    "/category-stats",
    response_model=Response[List[ExamCategoryStatsResponse]],
    summary="查询分类统计",
    description="按分类统计真题数量"
)
async def get_category_stats(
    session: SessionDep,
    subject_id: Optional[int] = Query(default=None, description="科目ID筛选")
) -> Response[List[ExamCategoryStatsResponse]]:
    """
    获取分类统计

    - 权限：公开
    - 从JSON数组中展开分类，统计各分类的题目数量
    """
    service = ExamService(session)
    stats = await service.get_category_stats(subject_id)
    return Response(data=stats)


@router.get(
    "/by-category",
    response_model=Response[List[ExamResponse]],
    summary="根据科目和分类查询真题",
    description="查询指定科目和分类的真题列表"
)
async def find_by_subject_and_category(
    session: SessionDep,
    subject_id: Optional[int] = Query(default=None, description="科目ID"),
    category: str = Query(..., description="分类名称")
) -> Response[List[ExamResponse]]:
    """
    根据科目和分类查询真题

    - 权限：公开
    - 返回指定科目和分类的真题列表
    """
    service = ExamService(session)
    exams = await service.find_by_subject_and_category(subject_id, category)
    return Response(data=exams)


@router.get(
    "/export",
    summary="导出真题",
    description="按科目导出真题（支持Markdown格式）"
)
async def export_by_subject(
    session: SessionDep,
    subject_id: int = Query(..., description="科目ID"),
    format: str = Query(..., description="导出格式")
) -> FastAPIResponse:
    """
    按科目导出真题

    - 权限：公开
    - 返回指定格式的导出文件
    """
    service = ExamService(session)
    export_result = await service.export_by_subject(subject_id, format)

    return FastAPIResponse(
        content=export_result.file_bytes,
        media_type=export_result.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={export_result.filename}"
        }
    )


@router.get(
    "/{exam_id}",
    response_model=Response[ExamResponse],
    summary="查询真题详情",
    description="根据ID查询真题详细信息"
)
async def get_exam_detail(
    session: SessionDep,
    exam_id: int = Path(..., description="真题ID")
) -> Response[ExamResponse]:
    """
    按ID查询真题详情

    - 权限：公开
    """
    service = ExamService(session)
    exam = await service.get_by_id(exam_id)
    return Response(data=exam)


@router.get(
    "/check-duplicate",
    response_model=Response[ExamResponse],
    summary="检查真题重复",
    description="检查(year, question_number)组合是否已存在，仅管理员可访问"
)
async def check_exam_duplicate(
    session: SessionDep,
    year: int = Query(..., description="年份"),
    question_number: int = Query(..., description="题号"),
    current_user: AuthUser = Depends(get_current_admin)
) -> Response[ExamResponse]:
    """
    检查真题是否重复

    - 权限：ADMIN
    - 校验(year + question_number)组合是否已存在
    """
    service = ExamService(session)
    existing = await service.check_duplicate(year, question_number)
    return Response(data=existing)


@router.post(
    "",
    response_model=Response[ExamResponse],
    summary="创建真题",
    description="创建新真题，仅管理员可访问"
)
async def create_exam(
    session: SessionDep,
    request: ExamCreateRequest,
    current_user: AuthUser = Depends(get_current_admin)
) -> Response[ExamResponse]:
    """
    创建真题

    - 权限：ADMIN
    - 创建时自动关联当前管理员为作者，并校验唯一性约束
    """
    service = ExamService(session)
    exam = await service.create(request, current_user.user_id)
    return Response(data=exam, message="创建成功")


@router.post(
    "/{exam_id}",
    response_model=Response[ExamResponse],
    summary="更新真题",
    description="更新指定真题的信息，仅管理员可访问"
)
async def update_exam(
    session: SessionDep,
    exam_id: int = Path(..., description="真题ID"),
    request: ExamUpdateRequest = None,
    current_user: AuthUser = Depends(get_current_admin)
) -> Response[ExamResponse]:
    """
    更新真题

    - 权限：ADMIN
    - 支持部分字段更新，更新时校验唯一性约束
    """
    service = ExamService(session)
    exam = await service.update(exam_id, request)
    return Response(data=exam, message="更新成功")


@router.post(
    "/{exam_id}/delete",
    response_model=Response[None],
    summary="删除真题",
    description="删除指定真题，仅管理员可访问"
)
async def delete_exam(
    session: SessionDep,
    exam_id: int = Path(..., description="真题ID"),
    current_user: AuthUser = Depends(get_current_admin)
) -> Response[None]:
    """
    删除真题

    - 权限：ADMIN
    - 物理删除真题记录，无法撤销
    """
    service = ExamService(session)
    await service.delete(exam_id)
    return Response(message="删除成功")
