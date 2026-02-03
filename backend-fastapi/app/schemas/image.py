"""
图片资源Schema定义模块
对应 Java 的 ImageResourceVO 和 ImageUsageExamVO
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ImageUsageResponse(BaseModel):
    """
    图片引用真题信息
    对应 Java 的 ImageUsageExamVO
    """
    id: int = Field(..., description="真题ID")
    year: Optional[int] = Field(None, description="年份")
    question_number: Optional[int] = Field(None, description="题号")
    title: str = Field(..., description="标题")


class ImageResourceResponse(BaseModel):
    """
    图片资源响应对象
    对应 Java 的 ImageResourceVO
    """
    filename: str = Field(..., description="文件名", example="123456.png")
    url: str = Field(..., description="访问URL", example="/uploads/images/123456.png")
    size: int = Field(..., description="文件大小（字节）", example=204800)
    last_modified: int = Field(..., description="最后修改时间（毫秒时间戳）", example=1719744000000)
    referenced: bool = Field(default=False, description="是否被题目引用")
    exams: List[ImageUsageResponse] = Field(default_factory=list, description="引用该图片的题目列表")
