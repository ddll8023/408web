"""图片资源请求与响应模型。"""

from pydantic import BaseModel, ConfigDict, Field


class ImageListRequest(BaseModel):
    """图片列表查询请求。"""

    only_unreferenced: bool = Field(default=False, description="是否只查询未引用图片")


class ImageCleanupRequest(BaseModel):
    """未引用图片清理请求。"""

    confirm: bool = Field(default=False, description="是否确认执行不可逆清理")


class ImageDeleteRequest(BaseModel):
    """指定图片删除请求。"""

    filename: str = Field(..., min_length=1, max_length=255, description="文件名")
    confirm: bool = Field(default=False, description="是否确认执行不可逆删除")


class ImageUsageResponse(BaseModel):
    """图片引用题目信息。"""

    id: int = Field(..., ge=1, description="题目 ID")
    year: int | None = Field(default=None, ge=1990, le=2100, description="年份")
    question_number: int | None = Field(default=None, ge=1, description="题号")
    title: str = Field(..., min_length=1, description="标题")

    model_config = ConfigDict(from_attributes=True)


class ImageResourceResponse(BaseModel):
    """图片资源响应对象。"""

    filename: str = Field(..., min_length=1, max_length=255, description="文件名", example="123456.png")
    url: str = Field(..., min_length=1, description="访问 URL", example="/uploads/images/123456.png")
    size: int = Field(..., ge=0, description="文件大小（字节）", example=204800)
    last_modified: int = Field(
        ...,
        ge=0,
        description="最后修改时间（毫秒时间戳）",
        example=1719744000000,
    )
    referenced: bool = Field(default=False, description="是否被题目引用")
    exams: list[ImageUsageResponse] = Field(
        default_factory=list,
        description="引用该图片的题目列表",
    )

    model_config = ConfigDict(from_attributes=True)
