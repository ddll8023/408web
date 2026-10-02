"""本地 AI 系统凭据存储，独立于业务数据库；同步文件操作由调用方在线程中执行。"""
import base64
import binascii
import os
import secrets
import stat
import sys
from pathlib import Path
from typing import Callable
from uuid import uuid4

from pydantic import SecretStr


MAX_SECRET_BYTES = 512


class AiLocalSecretError(Exception):
    """仅携带安全消息，不暴露文件内容、路径或底层异常链。"""


def _secret_directory() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    if not base.is_absolute():
        raise AiLocalSecretError("AI 本地凭据目录不可用，请检查系统用户目录")
    return base / "408web" / "ai"


def _check_private_mode(info: os.stat_result) -> None:
    # Windows 继承系统用户目录 ACL；POSIX 同时检查所有者与组 / 其他用户权限。
    if os.name != "nt" and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
        raise AiLocalSecretError("AI 本地凭据权限不安全，请检查系统用户私有目录")


def _prepare_directory(create: bool) -> Path:
    root = _secret_directory()
    for directory in (root.parent, root):
        if create:
            directory.mkdir(mode=0o700, parents=directory == root.parent, exist_ok=True)
        info = directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or directory.is_symlink() or directory.is_junction():
            raise AiLocalSecretError("AI 本地凭据目录类型无效，不允许目录链接")
        _check_private_mode(info)
    return root


def _read_secret(path: Path) -> bytes:
    """只读取有界普通文件，拒绝符号链接、宽松权限及读取期间的文件替换。"""
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_SECRET_BYTES:
        raise AiLocalSecretError("AI 本地凭据文件类型或大小无效，不会自动覆盖")
    _check_private_mode(before)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as source:
        current = os.fstat(source.fileno())
        if not stat.S_ISREG(current.st_mode) or (current.st_dev, current.st_ino) != (before.st_dev, before.st_ino):
            raise AiLocalSecretError("AI 本地凭据文件发生变化，请稍后重试")
        _check_private_mode(current)
        value = source.read(MAX_SECRET_BYTES + 1)
    if len(value) > MAX_SECRET_BYTES:
        raise AiLocalSecretError("AI 本地凭据文件超限，不会自动覆盖")
    return value.strip()


def _publish_secret(path: Path, value: bytes) -> None:
    """写完临时文件再独占发布，两个服务同时初始化时不覆盖获胜者的凭据。"""
    temporary = path.parent / f".{path.name}.{uuid4().hex}.tmp"
    created = False
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        with os.fdopen(descriptor, "wb") as output:
            output.write(value + b"\n")
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            # 另一进程已经发布，后续统一读取并校验磁盘上的获胜值。
            pass
    finally:
        if created:
            temporary.unlink(missing_ok=True)


def _load_secret(
    filename: str,
    validator: Callable[[bytes], bool],
    generator: Callable[[], bytes],
    *,
    create: bool,
) -> SecretStr:
    try:
        path = _prepare_directory(create) / filename
        try:
            value = _read_secret(path)
        except FileNotFoundError:
            if not create:
                raise AiLocalSecretError("AI 加密主密钥缺失，请恢复独立备份") from None
            _publish_secret(path, generator())
            value = _read_secret(path)
        if not validator(value):
            raise AiLocalSecretError("AI 本地凭据文件格式无效，请恢复备份；不会自动覆盖")
        return SecretStr(value.decode("ascii"))
    except OSError:
        raise AiLocalSecretError("AI 本地凭据存储不可用，请检查系统用户目录权限或恢复备份") from None


def _valid_master_key(value: bytes) -> bool:
    if len(value) != 44:
        return False
    try:
        decoded = base64.b64decode(value, altchars=b"-_", validate=True)
    except (ValueError, binascii.Error):
        return False
    return len(decoded) == 32 and base64.urlsafe_b64encode(decoded) == value


def get_master_key(*, create: bool) -> SecretStr:
    """首次明确保存新 Go Key 才允许补建主密钥；解密只读取既有文件。"""
    return _load_secret(
        "master.key",
        _valid_master_key,
        lambda: base64.urlsafe_b64encode(secrets.token_bytes(32)),
        create=create,
    )
