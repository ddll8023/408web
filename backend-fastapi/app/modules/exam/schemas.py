"""真题查询、维护和响应模型。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DifficultyEnum, QuestionTypeEnum
from app.modules.question_content.schemas import (
    QuestionCreateFields,
    QuestionOptions,
    QuestionUpdateFields,
)
from app.schemas.common import PaginatedResponse


ExamSortField = Literal["year", "update_time", "question_number"]
SortOrder = Literal["asc", "desc"]


class ExamQueryParams(BaseModel):
    """真题分页查询参数。"""

    page: int = Field(default=1, ge=1, description="页码", examples=[1])
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小", examples=[10])
    year: int | None = Field(default=None, ge=1990, le=2100, description="年份筛选")
    category: str | None = Field(default=None, description="分类筛选")
    subject_id: int | None = Field(default=None, ge=1, description="科目 ID 筛选")
    no_category: bool | None = Field(default=None, description="是否筛选无分类")
    keyword: str | None = Field(default=None, max_length=200, description="关键词搜索")
    sort_field: ExamSortField = Field(default="update_time", description="排序字段")
    sort_order: SortOrder = Field(default="desc", description="排序方向")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "page": 1,
                    "page_size": 10,
                    "year": 2023,
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

class ExamYearQueryRequest(BaseModel):
    """按年份查询真题的请求。"""

    category: str | None = Field(default=None, description="分类筛选")
    subject_id: int | None = Field(default=None, ge=1, description="科目 ID 筛选")


class ExamIndexRequest(BaseModel):
    """真题索引查询请求。"""

    category: str | None = Field(default=None, description="分类筛选")


class ExamByCategoryRequest(BaseModel):
    """按科目和分类查询真题的请求。"""

    subject_id: int | None = Field(default=None, ge=1, description="科目 ID")
    category: str = Field(..., min_length=1, max_length=100, description="分类名称")


class ExamDuplicateRequest(BaseModel):
    """真题查重请求。"""

    year: int = Field(..., ge=1990, le=2100, description="年份")
    question_number: int | None = Field(default=None, ge=1, le=1000, description="题号")
    exclude_id: int | None = Field(default=None, ge=1, description="排除的题目 ID")


class ExamCreateRequest(QuestionCreateFields):
    """真题创建请求。"""

    question_number: int | None = Field(default=None, ge=1, le=1000, description="题号")
    year: int = Field(..., ge=1990, le=2100, description="年份", examples=[2023])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "year": 2023,
                    "question_number": 1,
                    "question_type": "ESSAY",
                    "title": "栈的操作",
                    "content": "请实现一个栈，包含 push 和 pop 操作。",
                    "answer": "实现代码见解析。",
                    "category": ["数据结构", "栈"],
                    "subject_id": 1,
                    "difficulty": "MEDIUM",
                }
            ]
        }
    )


class ExamUpdateRequest(QuestionUpdateFields):
    """真题更新请求。"""

    year: int | None = Field(default=None, ge=1990, le=2100, description="年份")
    question_number: int | None = Field(default=None, ge=1, le=1000, description="题号")


class ExamResponse(BaseModel):
    """真题响应。"""

    id: int = Field(..., description="主键 ID")
    year: int = Field(..., description="年份")
    question_number: int | None = Field(default=None, ge=1, description="题号")
    question_type: QuestionTypeEnum = Field(..., description="题型")
    title: str | None = Field(default=None, description="题目标题")
    content: str = Field(..., description="题目内容")
    options: QuestionOptions | None = Field(default=None, description="选择题选项")
    answer: str | None = Field(default=None, description="答案")
    category: list[str] | None = Field(default=None, description="分类列表")
    subject_id: int | None = Field(default=None, ge=1, description="科目 ID")
    subject_name: str | None = Field(default=None, description="科目名称")
    difficulty: DifficultyEnum | None = Field(default=None, description="难度")
    author_id: int = Field(..., ge=1, description="作者 ID")
    author_name: str | None = Field(default=None, description="作者名称")
    create_time: str | None = Field(default=None, description="创建时间")
    update_time: str | None = Field(default=None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class ExamYearStatResponse(BaseModel):
    """真题年份统计响应。"""

    year: int = Field(..., ge=1990, le=2100)
    count: int = Field(..., ge=0)
    choice_count: int = Field(default=0, ge=0)
    subjective_count: int = Field(default=0, ge=0)

    model_config = ConfigDict(from_attributes=True)


class ExamDuplicateCheckResponse(BaseModel):
    """真题查重响应。"""

    is_duplicate: bool
    existing_question: ExamResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ExamIndexItem(BaseModel):
    """真题索引项。"""

    year: int = Field(..., ge=1990, le=2100)
    question_number: int | None = Field(default=None, ge=1)
    id: int = Field(..., ge=1)

    model_config = ConfigDict(from_attributes=True)


class ExamIndexResponse(BaseModel):
    """真题索引响应。"""

    subject_id: int | None = Field(default=None, ge=1)
    subject_name: str | None = None
    index_data: list[ExamIndexItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ExamNavItem(BaseModel):
    """真题导航索引项。"""

    id: int = Field(..., ge=1)
    year: int = Field(..., ge=1990, le=2100)
    question_number: int | None = Field(default=None, ge=1)
    title: str | None = None
    category: list[str] | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedExamResponse(PaginatedResponse[ExamResponse]):
    """真题分页响应。"""
