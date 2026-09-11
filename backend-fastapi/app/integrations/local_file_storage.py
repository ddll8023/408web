"""本地文件存储基础设施。"""
from dataclasses import dataclass
import asyncio
from pathlib import Path
import uuid

import aiofiles
from fastapi import UploadFile


class FileTooLargeError(Exception):
    """上传文件超过存储边界。"""


@dataclass(frozen=True, slots=True)
class StagedUpload:
    """尚未提交到目标路径的上传文件。"""

    temporary_path: Path
    target_path: Path
    header: bytes
    total_size: int


class LocalFileStorage:
    """提供安全路径、临时文件和原子替换能力。"""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir).expanduser().resolve()

    async def stage_upload(
        self,
        file: UploadFile,
        filename: str,
        max_file_size: int,
    ) -> StagedUpload:
        """将上传内容写入临时文件，等待业务校验后提交。"""
        target_path = self.safe_file_path(filename)
        temporary_path = self.root_dir / f".{uuid.uuid4().hex}.part"
        try:
            await asyncio.to_thread(self.root_dir.mkdir, parents=True, exist_ok=True)
            total_size = 0
            header = b""
            async with aiofiles.open(temporary_path, "wb") as output:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > max_file_size:
                        raise FileTooLargeError
                    if len(header) < 16:
                        header += chunk[: 16 - len(header)]
                    await output.write(chunk)
            return StagedUpload(
                temporary_path=temporary_path,
                target_path=target_path,
                header=header,
                total_size=total_size,
            )
        except Exception:
            await self.discard_upload(temporary_path)
            raise

    async def commit_upload(self, staged: StagedUpload) -> None:
        """以原子替换方式提交临时文件。"""
        await asyncio.to_thread(staged.temporary_path.replace, staged.target_path)

    async def discard_upload(self, staged: StagedUpload | Path) -> None:
        """清理未提交的临时文件。"""
        path = staged.temporary_path if isinstance(staged, StagedUpload) else staged
        try:
            await asyncio.to_thread(path.unlink, missing_ok=True)
        except OSError:
            pass

    async def list_files(self, extensions: set[str]) -> list[Path]:
        """列出根目录下指定扩展名的普通文件。"""
        return await asyncio.to_thread(self._list_files, extensions)

    async def get_file_metadata(self, path: Path) -> tuple[int, float]:
        """读取文件大小和修改时间。"""
        stat = await asyncio.to_thread(path.stat)
        return stat.st_size, stat.st_mtime

    async def is_file(self, filename: str) -> bool:
        """判断安全文件路径是否存在。"""
        return await asyncio.to_thread(self.safe_file_path(filename).is_file)

    async def delete_file(self, filename: str) -> None:
        """删除指定安全文件。"""
        await asyncio.to_thread(self.safe_file_path(filename).unlink)

    def safe_file_path(self, filename: str) -> Path:
        """将文件名限制在存储根目录内。"""
        if not filename or Path(filename).name != filename:
            raise ValueError("文件名不合法")
        if any(part in filename for part in ("..", "/", "\\")):
            raise ValueError("文件名不合法")

        path = self.root_dir / filename
        if path.is_symlink():
            raise ValueError("不允许操作符号链接")
        resolved_path = path.resolve(strict=False)
        if resolved_path.parent != self.root_dir:
            raise ValueError("文件路径不合法")
        return path

    def _list_files(self, extensions: set[str]) -> list[Path]:
        """同步列出安全文件，由线程池调用。"""
        if not self.root_dir.is_dir():
            return []
        return sorted(
            (
                path
                for path in self.root_dir.iterdir()
                if path.is_file()
                and not path.is_symlink()
                and path.suffix.lower().lstrip(".") in extensions
            ),
            key=lambda path: path.name,
        )
