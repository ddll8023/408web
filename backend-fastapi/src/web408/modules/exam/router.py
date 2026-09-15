"""真题查询、维护和导出 HTTP 路由。"""
from fastapi import APIRouter, Depends, File, Path, UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.api.dependencies import SessionDep
from web408.modules.auth.dependencies import AuthUser, get_current_admin
from web408.modules.exam.command_service import ExamCommandService
from web408.modules.exam.process_image_service import ExamProcessImageService
from web408.modules.exam.query_service import ExamQueryService
from web408.modules.exam.schemas import (
    ExamByCategoryRequest,
    ExamCreateRequest,
    ExamDuplicateCheckResponse,
    ExamDuplicateRequest,
    ExamIndexRequest,
    ExamNavItem,
    ExamProcessImageResponse,
    ExamProcessImageReorderRequest,
    ExamQueryParams,
    ExamResponse,
    ExamUpdateRequest,
    ExamYearQueryRequest,
    ExamYearStatResponse,
    PaginatedExamResponse,
)
from web408.schemas.common import ApiResponse


router = APIRouter()


def _get_command_service(session: AsyncSession) -> ExamCommandService:
    """创建共享查询服务的真题写入用例。"""
    return ExamCommandService(session, ExamQueryService(session))


def _get_process_image_service(session: AsyncSession) -> ExamProcessImageService:
    """创建真题过程图片业务服务。"""
    return ExamProcessImageService(session)


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
    "/{exam_id}/process-images",
    response_model=ApiResponse[list[ExamProcessImageResponse]],
    summary="查询真题过程图片",
    description="查询指定真题的讲解过程图片",
)
async def list_exam_process_images(
    session: SessionDep,
    exam_id: int = Path(..., ge=1, description="真题 ID"),
) -> ApiResponse[list[ExamProcessImageResponse]]:
    """查询真题过程图片。"""
    images = await _get_process_image_service(session).list_images(exam_id)
    return ApiResponse(data=images)


@router.post(
    "/{exam_id}/process-images/upload",
    response_model=ApiResponse[ExamProcessImageResponse],
    summary="上传真题过程图片",
    description="上传并关联一张真题讲解过程图片，仅管理员可访问",
)
async def upload_exam_process_image(
    session: SessionDep,
    file: UploadFile = File(..., description="过程图片文件"),
    admin: AuthUser = Depends(get_current_admin),
    exam_id: int = Path(..., ge=1, description="真题 ID"),
) -> ApiResponse[ExamProcessImageResponse]:
    """上传并关联真题过程图片。"""
    image = await _get_process_image_service(session).upload_image(
        exam_id,
        file,
        admin.user_id,
    )
    return ApiResponse(data=image, message="过程图片上传成功")


@router.post(
    "/{exam_id}/process-images/{image_id}/delete",
    response_model=ApiResponse[None],
    summary="删除真题过程图片",
    description="删除指定真题的过程图片关联，仅管理员可访问",
)
async def delete_exam_process_image(
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
    exam_id: int = Path(..., ge=1, description="真题 ID"),
    image_id: int = Path(..., ge=1, description="过程图片 ID"),
) -> ApiResponse[None]:
    """删除真题过程图片关联。"""
    await _get_process_image_service(session).delete_image(exam_id, image_id)
    return ApiResponse(message="过程图片删除成功")


@router.post(
    "/{exam_id}/process-images/reorder",
    response_model=ApiResponse[list[ExamProcessImageResponse]],
    summary="调整真题过程图片顺序",
    description="保存指定真题的过程图片展示顺序，仅管理员可访问",
)
async def reorder_exam_process_images(
    request: ExamProcessImageReorderRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
    exam_id: int = Path(..., ge=1, description="真题 ID"),
) -> ApiResponse[list[ExamProcessImageResponse]]:
    """调整真题过程图片顺序。"""
    images = await _get_process_image_service(session).reorder_images(
        exam_id,
        request,
    )
    return ApiResponse(data=images, message="过程图片顺序已保存")


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
