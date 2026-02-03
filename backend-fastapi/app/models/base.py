"""
SQLModel 基类定义
所有数据模型继承此类
"""
from datetime import datetime
from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    """
    基础模型类
    包含所有表共有的通用字段
    """
    id: int | None = Field(default=None, primary_key=True)
    create_time: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    update_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="更新时间",
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )

    class Config:
        from_attributes = True
