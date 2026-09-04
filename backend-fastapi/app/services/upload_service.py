"""图片上传、引用扫描和清理服务。"""
import asyncio
import uuid
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import UploadFile
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exception import (
    ConflictException,
    InfrastructureException,
    NotFoundException,
    ValidationException,
)
from app.models.entities import ExamQuestion, MockQuestion
from app.schemas.image import ImageResourceResponse, ImageUsageResponse
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


class UploadService:
    """图片文件服务。"""

    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
    CONTENT_TYPES = {
        "jpg": {"image/jpeg", "image/jpg"},
        "jpeg": {"image/jpeg", "image/jpg"},
        "png": {"image/png"},
        "gif": {"image/gif"},
        "webp": {"image/webp"},
    }

    def __init__(
        self,
        session: AsyncSession,
        upload_dir: str = "uploads/images",
        max_file_size: int = 10 * 1024 * 1024,
    ) -> None:
        self.session = session
        self.upload_dir = Path(upload_dir).expanduser().resolve()
        self.max_file_size = max_file_size

    async def upload_image(self, file: UploadFile) -> str:
        """校验并保存图片，返回公开访问 URL。"""
        if not file.filename or not file.filename.strip():
            raise ValidationException("文件不能为空")

        extension = self._get_file_extension(file.filename)
        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValidationException(f"不支持的文件类型: {extension or 'unknown'}")
        if file.content_type not in self.CONTENT_TYPES[extension]:
            raise ValidationException("文件类型与内容类型不匹配")

        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        target_path = self.upload_dir / unique_filename
        temporary_path = self.upload_dir / f".{uuid.uuid4().hex}.part"

        try:
            await asyncio.to_thread(self.upload_dir.mkdir, parents=True, exist_ok=True)
            total_size = 0
            header = b""
            async with aiofiles.open(temporary_path, "wb") as output:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > self.max_file_size:
                        raise ValidationException(
                            f"文件大小不能超过 {self.max_file_size} 字节"
                        )
                    if len(header) < 16:
                        header += chunk[: 16 - len(header)]
                    await output.write(chunk)

            if total_size == 0:
                raise ValidationException("文件不能为空")
            if not self._matches_signature(extension, header):
                raise ValidationException("文件内容不是有效的图片")

            await asyncio.to_thread(temporary_path.replace, target_path)
            return f"/uploads/images/{unique_filename}"
        except ValidationException:
            await self._remove_if_exists(temporary_path)
            raise
        except OSError as exc:
            await self._remove_if_exists(temporary_path)
            logger.error("图片文件写入失败", exc_info=True)
            raise InfrastructureException("文件上传失败") from exc
        except Exception as exc:
            await self._remove_if_exists(temporary_path)
            logger.error("图片上传出现未处理异常", exc_info=True)
            raise InfrastructureException("文件上传失败") from exc

    async def list_images(self, only_unreferenced: bool = False) -> list[ImageResourceResponse]:
        """查询图片元数据及引用状态。"""
        logger.info(
            "UploadService.list_images started, only_unreferenced: %s",
            only_unreferenced,
        )
        if not await asyncio.to_thread(self.upload_dir.is_dir):
            return []

        file_paths = await asyncio.to_thread(self._list_image_paths)
        images: list[ImageResourceResponse] = []
        for file_path in file_paths:
            stat = await asyncio.to_thread(file_path.stat)
            images.append(
                ImageResourceResponse(
                    filename=file_path.name,
                    url=f"/uploads/images/{file_path.name}",
                    size=stat.st_size,
                    last_modified=int(stat.st_mtime * 1000),
                    referenced=False,
                    exams=[],
                )
            )

        await self._check_image_references(images)
        if only_unreferenced:
            images = [image for image in images if not image.referenced]
        images.sort(key=lambda image: image.last_modified, reverse=True)
        return images

    async def cleanup_unreferenced_images(self, *, confirm: bool) -> int:
        """重新确认引用后清理未引用图片。"""
        if not confirm:
            raise ValidationException("未确认图片清理操作")

        images = await self.list_images(only_unreferenced=True)
        delete_count = 0
        for image in images:
            # 列表扫描和实际删除之间可能发生题目保存，因此逐文件复核。
            if await self._is_image_referenced(image.filename):
                continue
            try:
                file_path = self._safe_file_path(image.filename)
                if await asyncio.to_thread(file_path.is_file):
                    await asyncio.to_thread(file_path.unlink)
                    delete_count += 1
            except OSError:
                logger.warning(
                    "未引用图片删除失败: filename=%s",
                    image.filename,
                    exc_info=True,
                )

        logger.info(
            "UploadService.cleanup_unreferenced_images completed, deleted: %d",
            delete_count,
        )
        return delete_count

    async def delete_image(self, filename: str, *, confirm: bool) -> None:
        """删除未被题目引用的指定图片。"""
        if not confirm:
            raise ValidationException("未确认图片删除操作")

        file_path = self._safe_file_path(filename)
        if not await asyncio.to_thread(file_path.is_file):
            raise NotFoundException("文件")
        if await self._is_image_referenced(filename):
            raise ConflictException("图片仍被题目引用，无法删除")

        try:
            await asyncio.to_thread(file_path.unlink)
        except OSError as exc:
            logger.error("图片文件删除失败: filename=%s", filename, exc_info=True)
            raise InfrastructureException("文件删除失败") from exc

    def _list_image_paths(self) -> list[Path]:
        """同步列出安全的图片文件，由线程池调用。"""
        return sorted(
            (
                path
                for path in self.upload_dir.iterdir()
                if path.is_file()
                and not path.is_symlink()
                and path.suffix.lower().lstrip(".") in self.ALLOWED_EXTENSIONS
            ),
            key=lambda path: path.name,
        )

    def _safe_file_path(self, filename: str) -> Path:
        """将文件名限制在上传根目录内。"""
        if not filename or Path(filename).name != filename:
            raise ValidationException("文件名不合法")
        if any(part in filename for part in ("..", "/", "\\")):
            raise ValidationException("文件名不合法")

        path = self.upload_dir / filename
        if path.is_symlink():
            raise ValidationException("不允许操作符号链接")
        resolved_root = self.upload_dir.resolve()
        resolved_path = path.resolve(strict=False)
        if resolved_path.parent != resolved_root:
            raise ValidationException("文件路径不合法")
        return path

    async def _is_image_referenced(self, filename: str) -> bool:
        """扫描全部题目，确认单张图片是否仍被引用。"""
        image = ImageResourceResponse(
            filename=filename,
            url=f"/uploads/images/{filename}",
            size=0,
            last_modified=0,
            referenced=False,
            exams=[],
        )
        await self._check_image_references([image])
        return image.referenced

    async def _check_image_references(
        self,
        images: list[ImageResourceResponse],
    ) -> None:
        """扫描真题和模拟题的题干、选项及答案引用。"""
        if not images:
            return

        filename_set = {image.filename for image in images}
        image_map = {image.filename: image for image in images}

        exam_result = await self.session.exec(
            select(
                ExamQuestion.id,
                ExamQuestion.year,
                ExamQuestion.question_number,
                ExamQuestion.title,
                ExamQuestion.content,
                ExamQuestion.answer,
                ExamQuestion.options,
            )
        )
        mock_result = await self.session.exec(
            select(
                MockQuestion.id,
                MockQuestion.question_number,
                MockQuestion.title,
                MockQuestion.source,
                MockQuestion.content,
                MockQuestion.answer,
                MockQuestion.options,
            )
        )

        for exam in exam_result.all():
            text = " ".join(
                part for part in (exam.content, exam.answer, exam.options) if part
            )
            for filename in filename_set:
                if filename in text:
                    image = image_map[filename]
                    image.referenced = True
                    image.exams.append(
                        ImageUsageResponse(
                            id=exam.id,
                            year=exam.year,
                            question_number=exam.question_number,
                            title=exam.title
                            or f"真题-{exam.year}年第{exam.question_number or '?'}题",
                        )
                    )

        for mock in mock_result.all():
            text = " ".join(
                part for part in (mock.content, mock.answer, mock.options) if part
            )
            for filename in filename_set:
                if filename in text:
                    image = image_map[filename]
                    image.referenced = True
                    if not any(item.id == mock.id for item in image.exams):
                        image.exams.append(
                            ImageUsageResponse(
                                id=mock.id,
                                year=None,
                                question_number=mock.question_number,
                                title=f"[模拟题] {mock.title or mock.source}",
                            )
                        )

    async def _remove_if_exists(self, path: Path) -> None:
        """清理上传失败留下的临时文件。"""
        try:
            await asyncio.to_thread(path.unlink, missing_ok=True)
        except OSError:
            logger.warning("临时图片文件清理失败", exc_info=True)

    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """获取标准化文件扩展名。"""
        return Path(filename).suffix.lower().lstrip(".")

    @staticmethod
    def _matches_signature(extension: str, header: bytes) -> bool:
        """检查常见图片文件头。"""
        signatures = {
            "jpg": header.startswith(b"\xff\xd8\xff"),
            "jpeg": header.startswith(b"\xff\xd8\xff"),
            "png": header.startswith(b"\x89PNG\r\n\x1a\n"),
            "gif": header.startswith((b"GIF87a", b"GIF89a")),
            "webp": header.startswith(b"RIFF") and header[8:12] == b"WEBP",
        }
        return signatures.get(extension, False)
