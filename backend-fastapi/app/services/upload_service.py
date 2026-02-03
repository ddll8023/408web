"""
文件上传服务模块
实现图片上传、列表管理、引用检查和清理功能
"""
import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.entities import ExamQuestion, MockQuestion
from app.exception import NotFoundException, ValidationException
from app.schemas.image import ImageResourceResponse, ImageUsageResponse


# 获取服务日志记录器
logger = logging.getLogger(__name__)


class UploadService:
    """文件上传服务类"""

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

    def __init__(self, session: AsyncSession, upload_dir: str = "uploads/images"):
        self.session = session
        self.upload_dir = Path(upload_dir)

    async def upload_image(self, file) -> str:
        """
        上传图片文件

        Args:
            file: 上传的文件对象 (UploadFile)

        Returns:
            图片访问URL

        Raises:
            ValidationException: 文件为空、文件名无效或文件类型不支持
        """
        # 校验文件
        if not file or not file.filename:
            raise ValidationException("文件不能为空")

        # 校验文件名
        filename = file.filename
        if not filename or not filename.strip():
            raise ValidationException("文件名无效")

        # 校验文件类型
        extension = self._get_file_extension(filename).lower()
        if not extension:
            raise ValidationException("无法识别文件类型")
        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValidationException(f"不支持的文件类型: {extension}")

        try:
            # 生成UUID文件名
            unique_filename = f"{uuid.uuid4().hex}.{extension}"

            # 确保目录存在
            self.upload_dir.mkdir(parents=True, exist_ok=True)

            # 文件路径
            file_path = self.upload_dir / unique_filename

            # 异步写入文件
            import aiofiles
            content = await file.read()
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            # 返回相对URL
            return f"/uploads/images/{unique_filename}"

        except Exception as e:
            raise ValidationException(f"文件上传失败: {str(e)}")

    async def list_images(
        self,
        only_unreferenced: bool = False
    ) -> List[ImageResourceResponse]:
        """
        查询已上传图片列表

        Args:
            only_unreferenced: 是否只查询未引用的图片

        Returns:
            图片资源列表
        """
        logger.info("UploadService.list_images started, only_unreferenced: %s", only_unreferenced)

        if not self.upload_dir.exists() or not self.upload_dir.is_dir():
            logger.info("UploadService.list_images completed, upload_dir not exists")
            return []

        images = []
        for file_path in self.upload_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                images.append(ImageResourceResponse(
                    filename=file_path.name,
                    url=f"/uploads/images/{file_path.name}",
                    size=stat.st_size,
                    last_modified=int(stat.st_mtime * 1000),
                    referenced=False,
                    exams=[]
                ))

        # 检查图片引用
        await self._check_image_references(images)

        # 过滤未引用图片
        if only_unreferenced:
            images = [img for img in images if not img.referenced]

        # 按最后修改时间降序排序
        images.sort(key=lambda x: x.last_modified, reverse=True)

        logger.info("UploadService.list_images completed, count: %d", len(images))
        return images

    async def cleanup_unreferenced_images(self) -> int:
        """
        删除所有未被题目引用的图片

        Returns:
            删除的图片数量
        """
        logger.info("UploadService.cleanup_unreferenced_images started")

        images = await self.list_images(only_unreferenced=True)

        delete_count = 0
        for image in images:
            file_path = self.upload_dir / image.filename
            if file_path.exists() and file_path.is_file():
                try:
                    file_path.unlink()
                    delete_count += 1
                    logger.info("UploadService.cleanup_unreferenced_images: deleted %s", image.filename)
                except OSError:
                    logger.warning("UploadService.cleanup_unreferenced_images: failed to delete %s", image.filename)
                    continue

        logger.info("UploadService.cleanup_unreferenced_images completed, deleted: %d", delete_count)
        return delete_count

    async def delete_image(self, filename: str) -> None:
        """
        删除指定图片

        Args:
            filename: 文件名

        Raises:
            ValidationException: 文件名为空或不合法
            NotFoundException: 文件不存在
        """
        logger.info("UploadService.delete_image started, filename: %s", filename)

        # 校验文件名
        if not filename or not filename.strip():
            raise ValidationException("文件名不能为空")

        # 检查文件名安全性
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValidationException("文件名不合法")

        # 验证文件存在
        file_path = self.upload_dir / filename
        if not file_path.exists() or not file_path.is_file():
            logger.warning("UploadService.delete_image: file not found: %s", filename)
            raise NotFoundException("文件不存在")

        # 删除文件
        file_path.unlink()

        logger.info("UploadService.delete_image completed, filename: %s", filename)

    async def _check_image_references(
        self,
        images: List[ImageResourceResponse]
    ) -> None:
        """
        检查图片是否被真题或模拟题引用

        Args:
            images: 图片资源列表
        """
        if not images:
            return

        # 构建文件名集合用于快速查找
        filename_set = {img.filename for img in images}
        if not filename_set:
            return

        # 批量查询真题
        exam_stmt = select(ExamQuestion.id, ExamQuestion.year,
                          ExamQuestion.question_number, ExamQuestion.title,
                          ExamQuestion.content, ExamQuestion.answer, ExamQuestion.options)
        exam_result = await self.session.exec(exam_stmt)
        exams = exam_result.all()

        # 批量查询模拟题
        mock_stmt = select(MockQuestion.id, MockQuestion.question_number,
                          MockQuestion.title, MockQuestion.source,
                          MockQuestion.content, MockQuestion.answer, MockQuestion.options)
        mock_result = await self.session.exec(mock_stmt)
        mocks = mock_result.all()

        # 创建文件名到ImageResourceResponse的映射
        image_map = {img.filename: img for img in images}

        # 检查真题引用
        for exam in exams:
            text_parts = []
            if exam.content:
                text_parts.append(exam.content)
            if exam.answer:
                text_parts.append(exam.answer)
            if exam.options:
                text_parts.append(exam.options)

            text = " ".join(text_parts)
            if not text:
                continue

            for filename in filename_set:
                if filename in text:
                    img = image_map[filename]
                    img.referenced = True
                    img.exams.append(ImageUsageResponse(
                        id=exam.id,
                        year=exam.year,
                        question_number=exam.question_number,
                        title=exam.title or f"真题-{exam.year}年第{exam.question_number or '?'}题"
                    ))

        # 检查模拟题引用
        for mock in mocks:
            text_parts = []
            if mock.content:
                text_parts.append(mock.content)
            if mock.answer:
                text_parts.append(mock.answer)
            if mock.options:
                text_parts.append(mock.options)

            text = " ".join(text_parts)
            if not text:
                continue

            for filename in filename_set:
                if filename in text:
                    img = image_map[filename]
                    img.referenced = True
                    # 避免重复添加
                    if not any(e.id == mock.id for e in img.exams):
                        img.exams.append(ImageUsageResponse(
                            id=mock.id,
                            year=None,
                            question_number=mock.question_number,
                            title=f"[模拟题] {mock.title or mock.source}"
                        ))

    def _get_file_extension(self, filename: str) -> str:
        """
        获取文件扩展名

        Args:
            filename: 文件名

        Returns:
            扩展名（不含点）
        """
        if not filename:
            return ""
        last_dot = filename.rfind(".")
        if last_dot > 0 and last_dot < len(filename) - 1:
            return filename[last_dot + 1:]
        return ""
