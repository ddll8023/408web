"""SQLModel 基类和公共时间字段。"""

from datetime import datetime, timezone

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """返回不带时区信息的 UTC 时间，兼容当前 SQLite 存储格式。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BaseModel(SQLModel):
    """所有数据表共用的主键和生命周期字段。"""

    id: int | None = Field(default=None, primary_key=True)
    create_time: datetime = Field(default_factory=utc_now, description="创建时间")
    update_time: datetime = Field(
        default_factory=utc_now,
        description="更新时间",
        sa_column_kwargs={"onupdate": utc_now},
    )

    model_config = ConfigDict(from_attributes=True)
