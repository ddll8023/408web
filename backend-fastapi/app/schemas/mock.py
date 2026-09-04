"""模拟题查询、维护和响应模型。"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import PaginatedResponse
from app.schemas.question import QuestionCreateFields, QuestionOptions, QuestionUpdateFields


class MockQueryParams(BaseModel):
    """模拟题分页查询参数。"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小")
    source: Optional[str] = Field(default=None, max_length=100, description="来源机构筛选")
    category: Optional[str] = Field(default=None, description="分类筛选")
    subject_id: Optional[int] = Field(default=None, ge=1, description="科目 ID 筛选")
    no_category: Optional[bool] = Field(default=None, description="是否筛选无分类")
    keyword: Optional[str] = Field(default=None, max_length=200, description="关键词搜索")
    sort_field: str = Field(default="update_time", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "page": 1,
                    "page_size": 10,
                    "source": "王道",
                    "category": "栈",
                    "subject_id": 1,
                    "no_category": False,
                    "keyword": "链表",
                    "sort_field": "update_time",
                    "sort_order": "desc",
                }
            ]
        }
    )

    @field_validator("sort_field")
    @classmethod
    def validate_sort_field(cls, value: str) -> str:
        allowed_fields = {"source", "update_time", "question_number", "create_time"}
        if value not in allowed_fields:
            raise ValueError(f"排序字段必须为以下之一: {', '.join(sorted(allowed_fields))}")
        return value

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, value: str) -> str:
        if value not in {"asc", "desc"}:
            raise ValueError("排序方向必须为 asc 或 desc")
        return value


class MockSourceQueryRequest(BaseModel):
    """按来源查询模拟题的请求。"""

    category: Optional[str] = Field(default=None, description="分类筛选")
    subject_id: Optional[int] = Field(default=None, ge=1, description="科目 ID 筛选")


class MockCategoryFilterRequest(BaseModel):
    """模拟题来源统计筛选请求。"""

    category: Optional[str] = Field(default=None, description="分类筛选")


class MockDuplicateRequest(BaseModel):
    """模拟题查重请求。"""

    source: str = Field(..., min_length=1, max_length=100, description="来源机构")
    title: Optional[str] = Field(default=None, max_length=200, description="题目标题")
    question_number: Optional[int] = Field(default=None, ge=1, le=1000, description="题号")
    exclude_id: Optional[int] = Field(default=None, ge=1, description="排除的题目 ID")


class MockCreateRequest(QuestionCreateFields):
    """模拟题创建请求。"""

    source: str = Field(..., min_length=1, max_length=100, description="来源机构名称")


class MockUpdateRequest(QuestionUpdateFields):
    """模拟题更新请求。"""

    source: Optional[str] = Field(default=None, min_length=1, max_length=100, description="来源机构名称")
    question_number: Optional[int] = Field(default=None, ge=1, le=1000, description="题号")


class MockResponse(BaseModel):
    """模拟题响应。"""

    id: int
    source: str
    question_number: Optional[int] = None
    question_type: str
    title: Optional[str] = None
    content: str
    options: Optional[QuestionOptions] = None
    answer: Optional[str] = None
    category: Optional[list[str]] = None
    subject_id: Optional[int] = None
    subject_name: Optional[str] = None
    difficulty: Optional[str] = None
    author_id: int
    author_name: Optional[str] = None
    create_time: Optional[str] = None
    update_time: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MockSourceStatResponse(BaseModel):
    """模拟题来源统计响应。"""

    source: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class MockSourceItem(BaseModel):
    """模拟题来源列表项。"""

    source: str
    question_count: int

    model_config = ConfigDict(from_attributes=True)


class MockSourcesResponse(BaseModel):
    """模拟题来源列表响应。"""

    sources: list[MockSourceItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MockSubjectStatItem(BaseModel):
    """按科目统计项。"""

    subject_id: int
    subject_name: str
    count: int


class MockCategoryStatItem(BaseModel):
    """模拟题分类统计项。"""

    category: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class MockCategoryStatsResponse(BaseModel):
    """模拟题分类统计响应。"""

    subject_id: int
    subject_name: Optional[str] = None
    stats: list[MockCategoryStatItem] = Field(default_factory=list)
    total_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class MockDuplicateCheckResponse(BaseModel):
    """模拟题查重响应。"""

    is_duplicate: bool
    existing_question: Optional[MockResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedMockResponse(PaginatedResponse[MockResponse]):
    """模拟题分页响应。"""
