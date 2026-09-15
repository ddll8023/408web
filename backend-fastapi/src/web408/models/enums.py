"""数据库枚举值。"""

from enum import Enum


class UserRoleEnum(str, Enum):
    """用户角色枚举。"""
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"


class QuestionTypeEnum(str, Enum):
    """题型枚举。"""
    CHOICE = "CHOICE"  # 选择题
    ESSAY = "ESSAY"    # 主观题


class DifficultyEnum(str, Enum):
    """难度枚举。"""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
