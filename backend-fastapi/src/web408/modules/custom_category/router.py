"""自定义分类管理 HTTP 路由。"""
from fastapi import APIRouter, Depends, Path, status

from web408.api.dependencies import SessionDep
from web408.modules.auth.dependencies import AuthUser, get_current_admin
from web408.modules.custom_category.command_service import CustomCategoryCommandService
from web408.modules.custom_category.query_service import CustomCategoryQueryService
from web408.modules.custom_category.schemas import (
    AvailableParentCategoriesRequest,
    CustomCategoryCodeRebuildRequest,
    CustomCategoryCreateRequest,
    CustomCategoryMoveRequest,
    CustomCategoryResponse,
    CustomCategoryStatResponse,
    CustomCategoryTreeRequest,
    CustomCategoryTreeResponse,
    CustomCategoryUpdateRequest,
)
from web408.schemas.common import ApiResponse


router = APIRouter()


def _get_query_service(session: SessionDep) -> CustomCategoryQueryService:
    """创建自定义分类查询用例。"""
    return CustomCategoryQueryService(session)


def _get_command_service(session: SessionDep) -> CustomCategoryCommandService:
    """创建自定义分类写入用例及其查询依赖。"""
    return CustomCategoryCommandService(session, CustomCategoryQueryService(session))


@router.post(
    "/subject/{subject_id}/tree",
    response_model=ApiResponse[list[CustomCategoryTreeResponse]],
    summary="查询自定义分类树",
    description="按科目查询自定义分类树",
)
async def get_category_tree_by_subject(
    session: SessionDep,
    subject_id: int = Path(..., ge=1, description="科目 ID"),
    request: CustomCategoryTreeRequest | None = None,
) -> ApiResponse[list[CustomCategoryTreeResponse]]:
    """查询指定科目的自定义分类树，可按需只返回启用分类。"""
    categories = await _get_query_service(session).get_category_tree(
        subject_id,
        enabled_only=request.enabled_only if request else False,
    )
    return ApiResponse(data=categories)


@router.post(
    "/stats",
    response_model=ApiResponse[CustomCategoryStatResponse],
    summary="获取自定义分类统计",
    description="获取各科目的自定义分类数量统计",
)
async def get_category_stats(
    session: SessionDep,
) -> ApiResponse[CustomCategoryStatResponse]:
    """获取各科目自定义分类数量统计。"""
    stats = await _get_query_service(session).get_subject_stats()
    return ApiResponse(data=stats)


@router.post(
    "/available-parents",
    response_model=ApiResponse[list[CustomCategoryResponse]],
    summary="查询可选父分类",
    description="查询可作为父分类的自定义分类列表，仅管理员可访问",
)
async def get_available_parent_categories(
    request: AvailableParentCategoriesRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[list[CustomCategoryResponse]]:
    """查询可选父分类。"""
    categories = await _get_query_service(session).get_available_parent_categories(
        request.subject_id,
        request.exclude_id,
    )
    return ApiResponse(data=categories)


@router.post(
    "/rebuild-codes",
    response_model=ApiResponse[list[CustomCategoryResponse]],
    summary="重排分类编码",
    description="按当前显示顺序重排同级序号并重建分类编码，仅管理员可访问",
)
async def rebuild_category_codes(
    request: CustomCategoryCodeRebuildRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[list[CustomCategoryResponse]]:
    """重排指定科目或指定分类子树的层级编码。"""
    categories = await _get_command_service(session).rebuild_codes(
        request.subject_id,
        request.category_id,
    )
    return ApiResponse(data=categories, message="编码重排成功")


@router.post(
    "",
    response_model=ApiResponse[CustomCategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="创建自定义分类",
    description="创建自定义分类，仅管理员可访问",
)
async def create_category(
    request: CustomCategoryCreateRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[CustomCategoryResponse]:
    """创建自定义分类。"""
    category = await _get_command_service(session).create(request)
    return ApiResponse(data=category, message="创建成功")


@router.post(
    "/{category_id}",
    response_model=ApiResponse[CustomCategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="更新自定义分类",
    description="更新指定自定义分类的信息，仅管理员可访问",
)
async def update_category(
    request: CustomCategoryUpdateRequest,
    session: SessionDep,
    category_id: int = Path(..., ge=1, description="分类 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[CustomCategoryResponse]:
    """更新自定义分类。"""
    category = await _get_command_service(session).update(category_id, request)
    return ApiResponse(data=category, message="更新成功")


@router.post(
    "/{category_id}/move",
    response_model=ApiResponse[list[CustomCategoryResponse]],
    summary="移动自定义分类并排序",
    description="移动整棵自定义分类子树，返回该科目的最新分类树，仅管理员可访问",
)
async def move_category(
    request: CustomCategoryMoveRequest,
    session: SessionDep,
    category_id: int = Path(..., ge=1, description="分类 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[list[CustomCategoryResponse]]:
    """原子保存父级与受影响的同级顺序。"""
    categories = await _get_command_service(session).move(category_id, request)
    return ApiResponse(data=categories, message="分类移动成功")


@router.post(
    "/{category_id}/delete",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="删除自定义分类",
    description="删除指定自定义分类，仅管理员可访问",
)
async def delete_category(
    session: SessionDep,
    category_id: int = Path(..., ge=1, description="分类 ID"),
    _admin: AuthUser = Depends(get_current_admin),
) -> ApiResponse[None]:
    """删除自定义分类。"""
    await _get_command_service(session).delete(category_id)
    return ApiResponse(message="删除成功")
