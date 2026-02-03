"""
分类管理模块路由
提供分类标签管理的RESTful API接口
遵循Spring Boot旧项目接口规范
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.connection import get_async_session
from app.services.category_service import ExamCategoryService
from app.schemas.category import (
    ExamCategoryCreateRequest,
    ExamCategoryUpdateRequest,
    ExamCategoryResponse,
    ExamCategoryTreeResponse,
    ExamCategoryStatResponse,
    ExamCategoryUsageResponse
)
from app.schemas.common import Response
from app.middleware.auth import get_current_user, get_current_admin, AuthUser

router = APIRouter()


@router.get(
    "",
    response_model=Response[List[ExamCategoryResponse]],
    summary="查询所有分类",
    description="查询所有分类（包含引用统计），可按题目类型筛选"
)
async def get_all_categories(
    question_type: str = Query(default="exam", description="题目类型：exam=真题, mock=模拟题, exercise=课后习题"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[ExamCategoryResponse]]:
    """
    查询所有分类

    - 权限：公开
    - 支持按题目类型筛选（exam/mock/exercise）
    """
    service = ExamCategoryService(session)
    categories = await service.get_all_categories(question_type)
    return Response(data=categories)


@router.get(
    "/subject/{subject_id}",
    response_model=Response[List[ExamCategoryResponse]],
    summary="按科目查询分类",
    description="按科目查询所有分类（包含引用统计），可按题目类型筛选"
)
async def get_categories_by_subject(
    subject_id: int = Path(..., description="科目ID"),
    question_type: str = Query(default="exam", description="题目类型：exam=真题, mock=模拟题, exercise=课后习题"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[ExamCategoryResponse]]:
    """
    按科目查询分类

    - 权限：公开
    - 路径参数 subject_id：科目ID
    - 查询参数 question_type：题目类型
    """
    service = ExamCategoryService(session)
    categories = await service.get_categories_by_subject(subject_id, question_type)
    return Response(data=categories)


@router.get(
    "/subject/{subject_id}/enabled",
    response_model=Response[List[ExamCategoryResponse]],
    summary="查询启用分类",
    description="按科目查询启用的分类（用于前端选择器）"
)
async def get_enabled_categories_by_subject(
    subject_id: int = Path(..., description="科目ID"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[ExamCategoryResponse]]:
    """
    查询启用的分类

    - 权限：公开
    - 仅返回启用状态的分类
    """
    service = ExamCategoryService(session)
    categories = await service.get_enabled_categories_by_subject(subject_id)
    return Response(data=categories)


@router.get(
    "/subject/{subject_id}/tree",
    response_model=Response[List[ExamCategoryTreeResponse]],
    summary="查询分类树",
    description="按科目查询分类树形结构"
)
async def get_category_tree_by_subject(
    subject_id: int = Path(..., description="科目ID"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[ExamCategoryTreeResponse]]:
    """
    查询分类树形结构

    - 权限：公开
    - 返回任意层级深度的树形结构
    """
    service = ExamCategoryService(session)
    categories = await service.get_category_tree(subject_id, enabled_only=False)
    return Response(data=categories)


@router.get(
    "/subject/{subject_id}/tree/enabled",
    response_model=Response[List[ExamCategoryTreeResponse]],
    summary="查询启用分类树",
    description="按科目查询启用的分类树形结构（用于前端侧边栏）"
)
async def get_enabled_category_tree_by_subject(
    subject_id: int = Path(..., description="科目ID"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[ExamCategoryTreeResponse]]:
    """
    查询启用的分类树

    - 权限：公开
    - 仅返回启用状态的分类
    """
    service = ExamCategoryService(session)
    categories = await service.get_category_tree(subject_id, enabled_only=True)
    return Response(data=categories)


@router.get(
    "/subject/{subject_id}/tree/enabled/{question_type}",
    response_model=Response[List[ExamCategoryTreeResponse]],
    summary="查询启用分类树（带题型统计）",
    description="按科目和题型查询启用的分类树形结构，questionCount为指定题型的数量"
)
async def get_enabled_category_tree_with_stats(
    subject_id: int = Path(..., description="科目ID"),
    question_type: str = Path(..., description="题目类型：exam=真题, mock=模拟题, exercise=课后习题"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[ExamCategoryTreeResponse]]:
    """
    查询启用分类树（带题型统计）

    - 权限：公开
    - 用于模拟题和课后习题侧边栏
    - questionCount为指定题型的数量
    """
    service = ExamCategoryService(session)
    categories = await service.get_enabled_category_tree_with_stats(subject_id, question_type)
    return Response(data=categories)


@router.get(
    "/available-parents",
    response_model=Response[List[ExamCategoryResponse]],
    summary="查询可选父分类",
    description="查询可作为父分类的列表（顶级分类，排除自身及其子孙）"
)
async def get_available_parent_categories(
    subject_id: int = Query(..., description="科目ID"),
    exclude_id: Optional[int] = Query(None, description="排除的分类ID"),
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[List[ExamCategoryResponse]]:
    """
    查询可选父分类

    - 权限：ADMIN
    - 返回可作为父分类的列表（顶级分类）
    - 排除自身及其子孙分类
    """
    service = ExamCategoryService(session)
    categories = await service.get_available_parent_categories(subject_id, exclude_id)
    return Response(data=categories)


@router.get(
    "/stats",
    response_model=Response[ExamCategoryStatResponse],
    summary="获取分类统计",
    description="获取各科目去重后的题目数统计，解决多标签重复计数问题"
)
async def get_category_stats(
    question_type: str = Query(default="exam", description="题目类型：exam=真题, mock=模拟题, exercise=课后习题"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[ExamCategoryStatResponse]:
    """
    获取分类统计信息

    - 权限：公开
    - 用于解决一道题目有多个标签时的重复计数问题
    """
    service = ExamCategoryService(session)
    stats = await service.get_category_stats(question_type=question_type)
    return Response(data=stats)


@router.get(
    "/{category_id}/usage",
    response_model=Response[int],
    summary="检查分类引用",
    description="检查分类是否被引用，返回引用数量"
)
async def check_category_usage(
    category_id: int = Path(..., description="分类ID"),
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[int]:
    """
    检查分类引用

    - 权限：ADMIN
    - 返回分类被引用的次数（真题+模拟题）
    """
    service = ExamCategoryService(session)
    usage = await service.check_category_usage(category_id)
    return Response(data=usage)


@router.get(
    "/{category_id}",
    response_model=Response[ExamCategoryResponse],
    summary="查询分类详情",
    description="根据ID查询分类详细信息"
)
async def get_category_by_id(
    category_id: int = Path(..., description="分类ID"),
    session: AsyncSession = Depends(get_async_session)
) -> Response[ExamCategoryResponse]:
    """
    按ID查询分类

    - 权限：公开
    """
    service = ExamCategoryService(session)
    category = await service.get_by_id(category_id)
    return Response(data=category)


@router.post(
    "",
    response_model=Response[ExamCategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="创建分类",
    description="创建新分类，仅管理员可访问"
)
async def create_category(
    request: ExamCategoryCreateRequest,
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[ExamCategoryResponse]:
    """
    创建分类

    - 权限：ADMIN
    """
    service = ExamCategoryService(session)
    category = await service.create(request)
    return Response(data=category, message="创建成功")


@router.post(
    "/{category_id}",
    response_model=Response[ExamCategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="更新分类",
    description="更新指定分类的信息，仅管理员可访问"
)
async def update_category(
    category_id: int = Path(..., description="分类ID"),
    request: ExamCategoryUpdateRequest = None,
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[ExamCategoryResponse]:
    """
    更新分类

    - 权限：ADMIN
    """
    service = ExamCategoryService(session)
    category = await service.update(category_id, request)
    return Response(data=category, message="更新成功")


@router.post(
    "/{category_id}/delete",
    response_model=Response[None],
    status_code=status.HTTP_200_OK,
    summary="删除分类",
    description="删除指定分类，仅管理员可访问"
)
async def delete_category(
    category_id: int = Path(..., description="分类ID"),
    current_user: AuthUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_async_session)
) -> Response[None]:
    """
    删除分类

    - 权限：ADMIN
    - 需确保无子分类和题目引用
    """
    service = ExamCategoryService(session)
    await service.delete(category_id)
    return Response(message="删除成功")
