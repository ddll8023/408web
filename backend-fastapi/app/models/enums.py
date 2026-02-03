"""
枚举类型定义模块
用于替代 MySQL ENUM 类型，在 Python 层进行约束
"""
from enum import Enum


class UserRoleEnum(str, Enum):
    """用户角色枚举"""
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"


class QuestionTypeEnum(str, Enum):
    """题型枚举"""
    CHOICE = "CHOICE"  # 选择题
    ESSAY = "ESSAY"    # 主观题


class DifficultyEnum(str, Enum):
    """难度枚举"""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


# 类型别名，方便引用
UserRole = UserRoleEnum
QuestionType = QuestionTypeEnum
Difficulty = DifficultyEnum
