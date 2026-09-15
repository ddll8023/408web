"""真题过程图片的上传、展示和维护业务。"""
import logging
from pathlib import Path

from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.config import settings
from web408.core.exceptions import (
    InfrastructureException,
    NotFoundException,
    ValidationException,
)
from web408.modules.exam.models import ExamProcessImage
from web408.modules.exam.process_image_repository import ExamProcessImageRepository
from web408.modules.exam.schemas import (
    ExamProcessImageResponse,
    ExamProcessImageReorderRequest,
)
from web408.modules.media.service import UploadService


logger = logging.getLogger(__name__)


class ExamProcessImageService:
    """编排真题过程图片的文件上传和关联记录事务。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ExamProcessImageRepository(session)
        self.upload_service = UploadService(
            session,
            settings.upload.upload_dir,
            settings.upload.max_file_size,
        )

    async def list_images(self, exam_id: int) -> list[ExamProcessImageResponse]:
        """查询指定真题的过程图片。"""
        await self._require_exam(exam_id)
        return [
            self._to_response(image)
            for image in await self.repository.list_by_exam_id(exam_id)
        ]

    async def upload_image(
        self,
        exam_id: int,
        file: UploadFile,
        admin_id: int,
    ) -> ExamProcessImageResponse:
        """上传一张过程图片并创建其真题关联记录。"""
        await self._require_exam(exam_id)

        uploaded_filename: str | None = None
        try:
            file_url = await self.upload_service.upload_image(file)
            uploaded_filename = self._extract_filename(file_url)
            image = ExamProcessImage(
                exam_id=exam_id,
                filename=uploaded_filename,
                sort_order=await self.repository.get_next_sort_order(exam_id),
                created_by=admin_id,
            )
            self.session.add(image)
            await self.session.flush()
            await self.session.refresh(image)
            response = self._to_response(image)
            await self.session.commit()
            return response
        except Exception:
            await self.session.rollback()
            if uploaded_filename is not None:
                await self._discard_uploaded_file(uploaded_filename)
            raise

    async def delete_image(self, exam_id: int, image_id: int) -> None:
        """删除过程图片关联，文件交由现有未引用清理机制处理。"""
        await self._require_exam(exam_id)
        image = await self.repository.get_by_exam_and_id(exam_id, image_id)
        if image is None:
            raise NotFoundException("过程图片")

        await self.session.delete(image)
        await self.session.commit()

    async def reorder_images(
        self,
        exam_id: int,
        request: ExamProcessImageReorderRequest,
    ) -> list[ExamProcessImageResponse]:
        """保存指定真题的过程图片顺序。"""
        await self._require_exam(exam_id)
        images = await self.repository.list_by_exam_id(exam_id)
        current_ids = [image.id for image in images if image.id is not None]
        requested_ids = request.image_ids

        if (
            len(requested_ids) != len(set(requested_ids))
            or set(requested_ids) != set(current_ids)
        ):
            raise ValidationException("过程图片顺序与当前图片不一致")

        image_map = {image.id: image for image in images if image.id is not None}
        for sort_order, image_id in enumerate(requested_ids):
            image_map[image_id].sort_order = sort_order

        await self.session.commit()
        return await self.list_images(exam_id)

    async def _require_exam(self, exam_id: int) -> None:
        """确认过程图片所属真题存在。"""
        if await self.repository.get_exam(exam_id) is None:
            raise NotFoundException("真题")

    def _to_response(self, image: ExamProcessImage) -> ExamProcessImageResponse:
        """将过程图片实体转换为公开响应。"""
        if image.id is None:
            raise InfrastructureException("过程图片保存失败")

        return ExamProcessImageResponse(
            id=image.id,
            exam_id=image.exam_id,
            filename=image.filename,
            url=f"/uploads/images/{image.filename}",
            sort_order=image.sort_order,
            create_time=image.create_time.isoformat() if image.create_time else None,
            update_time=image.update_time.isoformat() if image.update_time else None,
        )

    def _extract_filename(self, file_url: str) -> str:
        """从上传服务返回的 URL 中提取并校验文件名。"""
        filename = Path(file_url).name
        try:
            self.upload_service.storage.safe_file_path(filename)
        except ValueError as exc:
            raise InfrastructureException("文件上传失败") from exc
        return filename

    async def _discard_uploaded_file(self, filename: str) -> None:
        """数据库关联失败时清理已提交的图片文件。"""
        try:
            if await self.upload_service.storage.is_file(filename):
                await self.upload_service.storage.delete_file(filename)
        except (OSError, ValueError):
            logger.warning(
                "过程图片关联失败后的文件清理失败: filename=%s",
                filename,
                exc_info=True,
            )
