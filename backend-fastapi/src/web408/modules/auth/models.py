"""认证模块持久化模型。"""
from typing import List

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship

from web408.models.base import BaseModel
from web408.models.enums import UserRoleEnum


class User(BaseModel, table=True):
    """用户模型。"""
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            "role IN ('ADMIN', 'USER', 'GUEST')",
            name="ck_user_role",
        ),
    )

    username: str = Field(unique=True, index=True, description="用户名")
    password: str = Field(description="Argon2 加密密码")
    email: str | None = Field(default=None, description="邮箱")
    role: str = Field(default=UserRoleEnum.USER.value, description="角色")
    enabled: bool = Field(default=True, description="账户启用状态")

    # 关系
    exam_questions: List["ExamQuestion"] = Relationship(
        back_populates="author",
        passive_deletes=True,
    )
    mock_questions: List["MockQuestion"] = Relationship(
        back_populates="author",
        passive_deletes=True,
    )
