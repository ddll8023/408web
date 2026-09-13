"""模拟题查询、维护和响应模型。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from web408.models.enums import DifficultyEnum, QuestionTypeEnum
from web408.modules.question_content.schemas import (
    QuestionCreateFields,
    QuestionOptions,
    QuestionUpdateFields,
)
from web408.schemas.common import PaginatedResponse


MockSortField = Literal["source", "update_time", "question_number", "create_time"]
SortOrder = Literal["asc", "desc"]


class MockQueryParams(BaseModel):
    """模拟题分页查询参数。"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小")
    source: str | None = Field(default=None, max_length=100, description="来源机构筛选")
    category: str | None = Field(default=None, description="分类筛选")
    subject_id: int | None = Field(default=None, ge=1, description="科目 ID 筛选")
    no_category: bool | None = Field(default=None, description="是否筛选无分类")
    keyword: str | None = Field(default=None, max_length=200, description="关键词搜索")
    sort_field: MockSortField = Field(default="update_time", description="排序字段")
    sort_order: SortOrder = Field(default="desc", description="排序方向")

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

class MockSourceQueryRequest(BaseModel):
    """按来源查询模拟题的请求。"""

    category: str | None = Field(default=None, description="分类筛选")
    subject_id: int | None = Field(default=None, ge=1, description="科目 ID 筛选")


class MockCategoryFilterRequest(BaseModel):
    """模拟题来源统计筛选请求。"""

    category: str | None = Field(default=None, description="分类筛选")


class MockDuplicateRequest(BaseModel):
    """模拟题查重请求。"""

    source: str = Field(..., min_length=1, max_length=100, description="来源机构")
    title: str | None = Field(default=None, max_length=200, description="题目标题")
    question_number: int | None = Field(default=None, ge=1, le=1000, description="题号")
    exclude_id: int | None = Field(default=None, ge=1, description="排除的题目 ID")


class MockCreateRequest(QuestionCreateFields):
    """模拟题创建请求。"""

    question_number: int | None = Field(default=None, ge=1, le=1000, description="题号")
    source: str = Field(..., min_length=1, max_length=100, description="来源机构名称")


class MockUpdateRequest(QuestionUpdateFields):
    """模拟题更新请求。"""

    source: str | None = Field(default=None, min_length=1, max_length=100, description="来源机构名称")
    question_number: int | None = Field(default=None, ge=1, le=1000, description="题号")


class MockResponse(BaseModel):
    """模拟题响应。"""

    id: int = Field(..., ge=1)
    source: str
    question_number: int | None = Field(default=None, ge=1)
    question_type: QuestionTypeEnum
    title: str | None = None
    content: str
    options: QuestionOptions | None = None
    answer: str | None = None
    category: list[str] | None = None
    subject_id: int | None = Field(default=None, ge=1)
    subject_name: str | None = None
    difficulty: DifficultyEnum | None = None
    author_id: int = Field(..., ge=1)
    author_name: str | None = None
    create_time: str | None = None
    update_time: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MockSourceStatResponse(BaseModel):
    """模拟题来源统计响应。"""

    source: str
    count: int = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True)


class MockSourceItem(BaseModel):
    """模拟题来源列表项。"""

    source: str
    question_count: int = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True)


class MockSourcesResponse(BaseModel):
    """模拟题来源列表响应。"""

    sources: list[MockSourceItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MockSubjectStatItem(BaseModel):
    """按科目统计项。"""

    subject_id: int = Field(..., ge=1)
    subject_name: str
    count: int = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True)


class MockCategoryStatItem(BaseModel):
    """模拟题分类统计项。"""

    category_name: str
    count: int = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True)


class MockCategoryStatsResponse(BaseModel):
    """模拟题分类统计响应。"""

    subject_id: int = Field(..., ge=1)
    subject_name: str | None = None
    stats: list[MockCategoryStatItem] = Field(default_factory=list)
    total_count: int = Field(default=0, ge=0)

    model_config = ConfigDict(from_attributes=True)


class MockDuplicateCheckResponse(BaseModel):
    """模拟题查重响应。"""

    is_duplicate: bool
    existing_question: MockResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedMockResponse(PaginatedResponse[MockResponse]):
    """模拟题分页响应。"""
