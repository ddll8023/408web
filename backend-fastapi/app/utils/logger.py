"""
日志配置模块
提供统一的日志配置功能，支持时间轮转
"""
import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Optional


def get_base_dir():
    """获取程序基础目录（兼容打包后）

    Returns:
        str: 程序基础目录路径
            - 打包后：程序所在目录
            - 开发时：项目根目录
    """
    if getattr(sys, 'frozen', False):
        # 打包后：程序所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发时：项目根目录
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# 日志目录
BASE_DIR = get_base_dir()
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 默认日志级别
DEFAULT_LOG_LEVEL = logging.INFO

# 日志轮转配置
LOG_ROTATION_WHEN = 'midnight'  # 轮转周期：midnight 表示每天午夜
LOG_ROTATION_INTERVAL = 1       # 轮转间隔：1天
LOG_BACKUP_COUNT = 7            # 保留的历史日志文件数量

# 日志格式：时间 [文件名:行号] [日志名] [级别] 消息
LOG_FORMAT = "[%(asctime)s] [%(filename)s:%(lineno)d] [%(name)s] [%(levelname)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: Optional[str] = None,
    level: int | str = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    console: bool = True,
    backup_count: int = LOG_BACKUP_COUNT,
    rotation_when: str = LOG_ROTATION_WHEN,
    rotation_interval: int = LOG_ROTATION_INTERVAL
) -> logging.Logger:
    """
    配置并返回日志记录器

    Args:
        name: 日志器名称，None则返回根日志器
        level: 日志级别
        log_file: 日志文件名，默认自动命名
        console: 是否输出到控制台
        backup_count: 保留的历史日志文件数量
        rotation_when: 日志轮转单位 (midnight, D, H, M, S)
        rotation_interval: 日志轮转间隔

    Returns:
        配置好的 logging.Logger 实例
    """
    # 创建日志目录
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 格式化器
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件处理器 - 使用时间轮转
    if log_file is None:
        log_file = datetime.now().strftime("%Y-%m-%d") + ".log"
    file_path = os.path.join(LOG_DIR, log_file)
    file_handler = TimedRotatingFileHandler(
        filename=file_path,
        when=rotation_when,
        interval=rotation_interval,
        backupCount=backup_count,
        encoding="utf-8",
        atTime=datetime.strptime("00:00:00", "%H:%M:%S")
    )
    # 轮转后的文件后缀格式
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
