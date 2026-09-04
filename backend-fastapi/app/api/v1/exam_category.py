"""分类管理路由。"""
from fastapi import APIRouter, Depends, Path, status

from app.database.connection import SessionDep
from app.middleware.auth import AuthUser, get_current_admin
from app.schemas.category import (
    AvailableParentCategoriesRequest,
    CategoryBySubjectQueryRequest,
    CategoryQueryRequest,
    CategoryStatsRequest,
    ExamCategoryCreateRequest,
    ExamCategoryResponse,
    ExamCategoryStatResponse,
    ExamCategoryTreeResponse,
    ExamCategoryUpdateRequest,
)
from app.schemas.common import ApiResponse
from app.services.category_service import ExamCategoryService


router = APIRouter()


@router.post(
    "/query",
    response_model=ApiResponse[list[ExamCategoryResponse]],
    summary="查询所有分类",
    description="查询所有分类（包含引用统计）",
)
async def get_all_categories(
    request: CategoryQueryRequest,
    session: SessionDep,
) -> ApiResponse[list[ExamCategoryResponse]]:
    """查询所有分类。"""
    categories = await ExamCategoryService(session).get_all_categories(request.question_type)
    return ApiResponse(data=categories)


@router.post(
    "/subject/{subject_id}/query",
    response_model=ApiResponse[list[ExamCategoryResponse]],
    summary="按科目查询分类",
    description="按科目查询分类及引用统计",
)
async def get_categories_by_subject(
    request: CategoryBySubjectQueryRequest,
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[list[ExamCategoryResponse]]:
    """按科目查询分类。"""
    categories = await ExamCategoryService(session).get_categories_by_subject(
        subject_id,
        question_type=request.question_type,
    )
    return ApiResponse(data=categories)


@router.post(
    "/subject/{subject_id}/enabled",
    response_model=ApiResponse[list[ExamCategoryResponse]],
    summary="查询启用分类",
    description="按科目查询启用的分类",
)
async def get_enabled_categories_by_subject(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[list[ExamCategoryResponse]]:
    """查询启用分类。"""
    categories = await ExamCategoryService(session).get_enabled_categories_by_subject(subject_id)
    return ApiResponse(data=categories)


@router.post(
    "/subject/{subject_id}/tree",
    response_model=ApiResponse[list[ExamCategoryTreeResponse]],
    summary="查询分类树",
    description="按科目查询分类树",
)
async def get_category_tree_by_subject(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[list[ExamCategoryTreeResponse]]:
    """查询分类树。"""
    categories = await ExamCategoryService(session).get_category_tree(subject_id, enabled_only=False)
    return ApiResponse(data=categories)


@router.post(
    "/subject/{subject_id}/tree/enabled",
    response_model=ApiResponse[list[ExamCategoryTreeResponse]],
    summary="查询启用分类树",
    description="按科目查询启用的分类树",
)
async def get_enabled_category_tree_by_subject(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[list[ExamCategoryTreeResponse]]:
    """查询启用分类树。"""
    categories = await ExamCategoryService(session).get_category_tree(subject_id, enabled_only=True)
    return ApiResponse(data=categories)


@router.post(
    "/subject/{subject_id}/tree/enabled-with-stats",
    response_model=ApiResponse[list[ExamCategoryTreeResponse]],
    summary="查询启用分类树及题型统计",
    description="按科目和题目类型查询启用分类树",
)
async def get_enabled_category_tree_with_stats(
    request: CategoryQueryRequest,
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
) -> ApiResponse[list[ExamCategoryTreeResponse]]:
    """查询启用分类树及题型统计。"""
    categories = await ExamCategoryService(session).get_enabled_category_tree_with_stats(
        subject_id,
        request.question_type,
    )
    return ApiResponse(data=categories)


@router.post(
    "/available-parents",
    response_model=ApiResponse[list[ExamCategoryResponse]],
    summary="查询可选父分类",
    description="查询可作为父分类的列表",
)
async def get_available_parent_categories(
    request: AvailableParentCategoriesRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[list[ExamCategoryResponse]]:
    """查询可选父分类。"""
    categories = await ExamCategoryService(session).get_available_parent_categories(
        request.subject_id,
        request.exclude_id,
    )
    return ApiResponse(data=categories)


@router.post(
    "/stats",
    response_model=ApiResponse[ExamCategoryStatResponse],
    summary="获取分类统计",
    description="获取各科目去重后的题目数统计",
)
async def get_category_stats(
    request: CategoryStatsRequest,
    session: SessionDep,
) -> ApiResponse[ExamCategoryStatResponse]:
    """获取分类统计。"""
    stats = await ExamCategoryService(session).get_category_stats(request.question_type)
    return ApiResponse(data=stats)


@router.post(
    "/{category_id}/usage",
    response_model=ApiResponse[int],
    summary="检查分类引用",
    description="检查分类是否被引用",
)
async def check_category_usage(
    session: SessionDep,
    category_id: int = Path(..., ge=1, description="分类 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[int]:
    """检查分类引用数量。"""
    usage = await ExamCategoryService(session).check_category_usage(category_id)
    return ApiResponse(data=usage)


@router.post(
    "/{category_id}/detail",
    response_model=ApiResponse[ExamCategoryResponse],
    summary="查询分类详情",
    description="根据 ID 查询分类详情",
)
async def get_category_by_id(
    session: SessionDep,
    category_id: int = Path(..., ge=1, description="分类 ID"),
) -> ApiResponse[ExamCategoryResponse]:
    """查询分类详情。"""
    category = await ExamCategoryService(session).get_by_id(category_id)
    return ApiResponse(data=category)


@router.post(
    "",
    response_model=ApiResponse[ExamCategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="创建分类",
    description="创建新分类，仅管理员可访问",
)
async def create_category(
    request: ExamCategoryCreateRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[ExamCategoryResponse]:
    """创建分类。"""
    category = await ExamCategoryService(session).create(request)
    return ApiResponse(data=category, message="创建成功")


@router.post(
    "/{category_id}",
    response_model=ApiResponse[ExamCategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="更新分类",
    description="更新指定分类的信息，仅管理员可访问",
)
async def update_category(
    request: ExamCategoryUpdateRequest,
    session: SessionDep,
    category_id: int = Path(..., ge=1, description="分类 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[ExamCategoryResponse]:
    """更新分类。"""
    category = await ExamCategoryService(session).update(category_id, request)
    return ApiResponse(data=category, message="更新成功")


@router.post(
    "/{category_id}/delete",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="删除分类",
    description="删除指定分类，仅管理员可访问",
)
async def delete_category(
    session: SessionDep,
    category_id: int = Path(..., ge=1, description="分类 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[None]:
    """删除分类。"""
    await ExamCategoryService(session).delete(category_id)
    return ApiResponse(message="删除成功")
