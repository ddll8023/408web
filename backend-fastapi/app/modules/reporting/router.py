"""统计与导出 HTTP 路由。"""
from urllib.parse import quote

from fastapi import APIRouter, Depends, Response as FastAPIResponse

from app.api.dependencies import SessionDep
from app.modules.auth.dependencies import AuthUser, get_current_admin
from app.modules.reporting.schemas import (
    ExamCategoryStatsExportRequest,
    ExamCategoryStatsRequest,
    ExamCategoryStatsResponse,
    ExamExportRequest,
)
from app.modules.reporting.service import ReportingService
from app.schemas.common import ApiResponse


router = APIRouter()


@router.post(
    "/category-stats",
    summary="查询分类统计",
    description="按分类统计真题数量",
)
async def get_exam_category_stats(
    request: ExamCategoryStatsRequest,
    session: SessionDep,
) -> ApiResponse[ExamCategoryStatsResponse]:
    """查询真题分类统计。"""
    stats = await ReportingService(session).get_category_stats(request.subject_id)
    return ApiResponse(data=stats)


@router.post(
    "/export-category-stats",
    summary="导出真题分类统计",
    description="管理员按科目导出真题分类统计 Markdown 或 Excel 文件",
)
async def export_exam_category_stats(
    request: ExamCategoryStatsExportRequest,
    session: SessionDep,
    _admin: AuthUser = Depends(get_current_admin),
) -> FastAPIResponse:
    """导出真题分类统计。"""
    export_result = await ReportingService(session).export_category_stats(
        request.subject_id,
        request.format,
    )
    encoded_filename = quote(export_result.filename)
    extension = export_result.filename.rsplit(".", 1)[-1]
    return FastAPIResponse(
        content=export_result.file_bytes,
        media_type=export_result.content_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="category-stats.{extension}"; '
                f"filename*=UTF-8''{encoded_filename}"
            ),
            "Cache-Control": "no-store",
        },
    )


@router.post(
    "/export",
    summary="导出真题",
    description="按科目导出 Markdown 真题文件",
)
async def export_exam_by_subject(
    request: ExamExportRequest,
    session: SessionDep,
) -> FastAPIResponse:
    """按科目导出真题。"""
    export_result = await ReportingService(session).export_by_subject(request)
    encoded_filename = quote(export_result.filename)
    return FastAPIResponse(
        content=export_result.file_bytes,
        media_type=export_result.content_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="exam.md"; '
                f"filename*=UTF-8''{encoded_filename}"
            ),
        },
    )
