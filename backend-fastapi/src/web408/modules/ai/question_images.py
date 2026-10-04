"""题目图片数据的受控读取：只映射本站上传目录，不抓取外链、不接收浏览器路径。

本模块只处理业务层解析出的图片引用，不访问数据库与模型；读取范围限定在
配置的上传目录内，任何外部地址都只按文件名规则拒绝，不发起网络请求。
"""
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit

from web408.integrations.local_file_storage import LocalFileStorage
from web408.modules.ai.session_schemas import (
    AiOmittedQuestionImage,
    AiQuestionImage,
    AiQuestionImageRef,
    ImageOmissionReason,
)


# 图片白名单与上传接口 UploadService.ALLOWED_EXTENSIONS 保持一致，改一处必须同步另一处。
UPLOAD_PATH_PREFIX: Final = "/uploads/images/"
LOCAL_HOSTS: Final = frozenset({"localhost", "127.0.0.1", "::1"})
MEDIA_TYPES: Final[dict[str, str]] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}
EXTERNAL_REASON: Final[ImageOmissionReason] = "external"
INLINE_REASON: Final[ImageOmissionReason] = "inline"
MISSING_REASON: Final[ImageOmissionReason] = "missing"
OVERSIZE_REASON: Final[ImageOmissionReason] = "oversize"
BUDGET_REASON: Final[ImageOmissionReason] = "budget"
SVG_REASON: Final[ImageOmissionReason] = "svg_budget"
# 原因码到中文说明的唯一定义处；会话说明与快照占位符共用同一套文案。
OMIT_TEXTS: Final[dict[str, str]] = {
    EXTERNAL_REASON: "图片来源不是本站上传图片",
    INLINE_REASON: "内联图形未转换为图像",
    MISSING_REASON: "图片文件不存在",
    OVERSIZE_REASON: "图片超过大小上限",
    BUDGET_REASON: "超出本次图片数量或体积上限",
    SVG_REASON: "SVG 源码超过长度上限",
}


@dataclass(slots=True)
class QuestionImages:
    """一次题目图片读取的结果：可发送图片数据与未附带登记。"""

    images: list[AiQuestionImage]
    omitted: list[AiOmittedQuestionImage]


def resolve_local_image(url: str) -> tuple[str, str] | None:
    """解析图片地址为本站上传目录内的文件名与媒体类型；外链与非法地址返回 None。

    历史数据里的旧域名端口只用于取出路径，host 不是本机时一律视为外链，不按文件名猜测。
    """
    parts = urlsplit(url.strip())
    if parts.scheme and parts.scheme not in {"http", "https"}:
        return None
    host = (parts.hostname or "").lower()
    if host and host not in LOCAL_HOSTS:
        return None
    if not parts.path.startswith(UPLOAD_PATH_PREFIX):
        return None
    filename = parts.path[len(UPLOAD_PATH_PREFIX):]
    if not filename or "/" in filename or "\\" in filename or ".." in filename:
        return None
    media_type = MEDIA_TYPES.get(Path(filename).suffix.lower().lstrip("."))
    if media_type is None:
        return None
    return filename, media_type


def _read_local_image(
    storage: LocalFileStorage,
    filename: str,
    max_image_bytes: int,
) -> tuple[ImageOmissionReason | None, bytes]:
    """同步校验并读取受控文件；返回跳过原因或图片字节，由线程池调用。"""
    try:
        path = storage.safe_file_path(filename)
    except ValueError:
        # 引用来自题目文本而不是浏览器，都被拒绝说明文件名不符合受控目录规则。
        return EXTERNAL_REASON, b""
    if path.is_symlink() or not path.is_file():
        return MISSING_REASON, b""
    size = path.stat().st_size
    if size == 0:
        return MISSING_REASON, b""
    if size > max_image_bytes:
        return OVERSIZE_REASON, b""
    return None, path.read_bytes()


async def load_question_images(
    refs: Sequence[AiQuestionImageRef],
    upload_dir: str | Path,
    *,
    max_count: int,
    max_image_bytes: int,
    max_total_bytes: int,
) -> QuestionImages:
    """按引用顺序读取图片字节；缺失、超限与超出张数的引用只登记原因，不中断咨询。"""
    images: list[AiQuestionImage] = []
    omitted: list[AiOmittedQuestionImage] = []
    if not refs:
        return QuestionImages(images=images, omitted=omitted)
    storage = LocalFileStorage(upload_dir)
    total_bytes = 0
    for ref in refs:
        if len(images) >= max_count:
            omitted.append(AiOmittedQuestionImage(index=ref.index, reason=BUDGET_REASON))
            continue
        reason, data = await asyncio.to_thread(_read_local_image, storage, ref.filename, max_image_bytes)
        if reason is not None:
            omitted.append(AiOmittedQuestionImage(index=ref.index, reason=reason))
            continue
        if total_bytes + len(data) > max_total_bytes:
            omitted.append(AiOmittedQuestionImage(index=ref.index, reason=BUDGET_REASON))
            continue
        total_bytes += len(data)
        images.append(AiQuestionImage(index=ref.index, media_type=ref.media_type, data=data))
    return QuestionImages(images=images, omitted=omitted)
