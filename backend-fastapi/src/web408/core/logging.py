"""应用级日志配置。"""
import logging
import shutil
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


_configured = False


class WindowsCompatibleTimedRotatingFileHandler(TimedRotatingFileHandler):
    """在 Windows 文件占用场景下使用复制和清空完成日志轮转。"""

    def rotate(self, source: str, dest: str) -> None:
        self.close()
        try:
            shutil.copy2(source, dest)
            Path(source).write_text("", encoding=self.encoding or "utf-8")
        except OSError:
            super().rotate(source, dest)


def configure_logging(
    *,
    log_dir: str,
    log_file: str,
    level: str,
    backup_count: int,
    console: bool = True,
) -> None:
    """集中配置根日志器；业务模块只获取命名日志器。"""
    global _configured
    if _configured:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    directory = Path(log_dir).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(filename)s:%(lineno)d] "
        "[%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    file_handler = WindowsCompatibleTimedRotatingFileHandler(
        filename=directory / log_file,
        when="midnight",
        interval=1,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    _configured = True
