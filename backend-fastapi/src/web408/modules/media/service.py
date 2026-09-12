"""图片上传、引用扫描和清理服务。"""
import logging
from pathlib import Path
import uuid

from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from web408.core.exceptions import (
    ConflictException,
    InfrastructureException,
    NotFoundException,
    ValidationException,
)
from web408.integrations.local_file_storage import (
    FileTooLargeError,
    LocalFileStorage,
    StagedUpload,
)
from web408.modules.media.reference_reader import MediaReferenceReader
from web408.modules.media.schemas import ImageResourceResponse


logger = logging.getLogger(__name__)


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
        self.storage = LocalFileStorage(upload_dir)
        self.reference_reader = MediaReferenceReader(session)
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
        staged: StagedUpload | None = None
        try:
            staged = await self.storage.stage_upload(
                file,
                unique_filename,
                self.max_file_size,
            )
            if staged.total_size == 0:
                raise ValidationException("文件不能为空")
            if not self._matches_signature(extension, staged.header):
                raise ValidationException("文件内容不是有效的图片")

            await self.storage.commit_upload(staged)
            return f"/uploads/images/{unique_filename}"
        except FileTooLargeError as exc:
            raise ValidationException(
                f"文件大小不能超过 {self.max_file_size} 字节"
            ) from exc
        except ValidationException:
            if staged is not None:
                await self.storage.discard_upload(staged)
            raise
        except OSError as exc:
            if staged is not None:
                await self.storage.discard_upload(staged)
            logger.error("图片文件写入失败", exc_info=True)
            raise InfrastructureException("文件上传失败") from exc
        except Exception as exc:
            if staged is not None:
                await self.storage.discard_upload(staged)
            logger.error("图片上传出现未处理异常", exc_info=True)
            raise InfrastructureException("文件上传失败") from exc

    async def list_images(self, only_unreferenced: bool = False) -> list[ImageResourceResponse]:
        """查询图片元数据及引用状态。"""
        logger.info(
            "UploadService.list_images started, only_unreferenced: %s",
            only_unreferenced,
        )
        file_paths = await self.storage.list_files(self.ALLOWED_EXTENSIONS)
        images: list[ImageResourceResponse] = []
        for file_path in file_paths:
            size, modified_time = await self.storage.get_file_metadata(file_path)
            images.append(
                ImageResourceResponse(
                    filename=file_path.name,
                    url=f"/uploads/images/{file_path.name}",
                    size=size,
                    last_modified=int(modified_time * 1000),
                    referenced=False,
                    exams=[],
                )
            )

        await self.reference_reader.mark_references(images)
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
                if await self.storage.is_file(image.filename):
                    await self.storage.delete_file(image.filename)
                    delete_count += 1
            except (OSError, ValueError):
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

        try:
            self.storage.safe_file_path(filename)
        except ValueError as exc:
            raise ValidationException(str(exc)) from exc
        if not await self.storage.is_file(filename):
            raise NotFoundException("文件")
        if await self._is_image_referenced(filename):
            raise ConflictException("图片仍被题目引用，无法删除")

        try:
            await self.storage.delete_file(filename)
        except OSError as exc:
            logger.error("图片文件删除失败: filename=%s", filename, exc_info=True)
            raise InfrastructureException("文件删除失败") from exc

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
        await self.reference_reader.mark_references([image])
        return image.referenced

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
