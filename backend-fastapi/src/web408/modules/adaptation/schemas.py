"""改编题查询、来源引用、维护和响应模型。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from web408.models.enums import DifficultyEnum, QuestionTypeEnum
from web408.modules.question_content.schemas import (
    QuestionCreateFields,
    QuestionOptions,
    QuestionUpdateFields,
)
from web408.schemas.common import PaginatedResponse


AdaptationSortField = Literal["id", "title", "update_time", "create_time"]
SortOrder = Literal["asc", "desc"]
SourceState = Literal["all", "with_source", "without_source"]

# 单题一次最多维护/解析的来源条数，避免误传超大列表拖慢请求。
MAX_SOURCE_REFS = 20
# 408 真题每年固定为 47 道题，来源题号统一按该范围校验。
MAX_SOURCE_QUESTION_NUMBER = 47


class AdaptationSourceRefInput(BaseModel):
    """改编来源引用输入。"""

    source_year: int = Field(..., ge=1990, le=2100, description="来源真题年份")
    source_question_number: int = Field(
        ..., ge=1, le=MAX_SOURCE_QUESTION_NUMBER, description="来源真题题号"
    )


class AdaptationQueryParams(BaseModel):
    """改编题分页查询参数。"""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小")
    subject_id: int | None = Field(default=None, ge=1, description="科目 ID 筛选")
    category: str | None = Field(default=None, description="分类筛选")
    no_category: bool | None = Field(default=None, description="是否筛选无分类")
    question_type: QuestionTypeEnum | None = Field(default=None, description="题型筛选")
    keyword: str | None = Field(default=None, max_length=200, description="关键词搜索")
    source_year: int | None = Field(default=None, ge=1990, le=2100, description="来源年份筛选")
    source_question_number: int | None = Field(
        default=None,
        ge=1,
        le=MAX_SOURCE_QUESTION_NUMBER,
        description="来源题号筛选",
    )
    source_state: SourceState = Field(default="all", description="来源标注状态筛选")
    sort_field: AdaptationSortField = Field(default="update_time", description="排序字段")
    sort_order: SortOrder = Field(default="desc", description="排序方向")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "page": 1,
                    "page_size": 10,
                    "subject_id": 1,
                    "category": "栈",
                    "question_type": "CHOICE",
                    "keyword": "链表",
                    "source_year": 2021,
                    "source_state": "with_source",
                    "sort_field": "update_time",
                    "sort_order": "desc",
                }
            ]
        }
    )


class AdaptationSourceUsageRequest(BaseModel):
    """改编题来源占用检查请求。"""

    exclude_id: int | None = Field(default=None, ge=1, description="排除的题目 ID")
    sources: list[AdaptationSourceRefInput] = Field(
        default_factory=list,
        max_length=MAX_SOURCE_REFS,
        description="当前表单中的来源引用，用于提示同源改编",
    )


class AdaptationSourceLookupRequest(BaseModel):
    """来源批量解析请求。"""

    sources: list[AdaptationSourceRefInput] = Field(
        ...,
        min_length=1,
        max_length=MAX_SOURCE_REFS,
        description="待解析的来源引用",
    )


class AdaptationSourceLookupItem(BaseModel):
    """来源解析结果项。"""

    source_year: int = Field(..., ge=1990, le=2100)
    source_question_number: int = Field(
        ..., ge=1, le=MAX_SOURCE_QUESTION_NUMBER
    )
    exists: bool = Field(..., description="真题库中是否存在该题")
    exam_question_id: int | None = Field(default=None, ge=1)
    exam_title: str | None = Field(default=None, description="命中的真题标题")
    exam_question_type: QuestionTypeEnum | None = Field(default=None, description="命中的真题题型")

    model_config = ConfigDict(from_attributes=True)


class AdaptationBySourceRequest(BaseModel):
    """按真题来源反查改编题的请求。"""

    source_year: int = Field(..., ge=1990, le=2100, description="来源真题年份")
    source_question_number: int = Field(
        ..., ge=1, le=MAX_SOURCE_QUESTION_NUMBER, description="来源真题题号"
    )
    subject_id: int | None = Field(default=None, ge=1, description="科目 ID 筛选")


class AdaptationBySourceItem(BaseModel):
    """反查结果项。"""

    id: int = Field(..., ge=1)
    title: str | None = Field(default=None)
    question_type: QuestionTypeEnum
    subject_id: int | None = Field(default=None, ge=1)
    subject_name: str | None = Field(default=None)
    update_time: str | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class AdaptationCoverageRequest(BaseModel):
    """改编覆盖统计请求。"""

    subject_id: int | None = Field(default=None, ge=1, description="科目 ID 筛选")
    years: list[int] | None = Field(
        default=None,
        max_length=50,
        description="年份列表，不传表示统计真题库中全部年份",
    )

    @field_validator("years")
    @classmethod
    def validate_years(cls, value: list[int] | None) -> list[int] | None:
        """约束覆盖统计的年份范围，避免非法年份进入统计查询。"""
        if value is not None and any(year < 1990 or year > 2100 for year in value):
            raise ValueError("年份必须在 1990 到 2100 之间")
        return value


class AdaptationCoverageCountItem(BaseModel):
    """覆盖统计中单题的改编次数。"""

    question_number: int = Field(
        ..., ge=1, le=MAX_SOURCE_QUESTION_NUMBER
    )
    adaptation_count: int = Field(..., ge=0)


class AdaptationCoverageItem(BaseModel):
    """按年份的改编覆盖统计项。"""

    year: int = Field(..., ge=1990, le=2100)
    total: int = Field(..., ge=0, description="该年真题总题数")
    adapted: int = Field(..., ge=0, description="被引用的真题题目数")
    missing_numbers: list[int] = Field(
        default_factory=list,
        description="尚未被改编的真题题号",
    )
    dangling_sources: int = Field(
        default=0,
        ge=0,
        description="来源中无法对应真题库的引用条数",
    )
    counts: list[AdaptationCoverageCountItem] = Field(
        default_factory=list,
        description="题号及其被引用次数",
    )

    model_config = ConfigDict(from_attributes=True)


class AdaptationSourceUsageItem(BaseModel):
    """同源改编提示项。"""

    source_year: int = Field(..., ge=1990, le=2100)
    source_question_number: int = Field(
        ..., ge=1, le=MAX_SOURCE_QUESTION_NUMBER
    )
    adaptation_id: int = Field(..., ge=1)
    title: str | None = Field(default=None)


class AdaptationSourceRefResponse(BaseModel):
    """来源引用响应。"""

    id: int | None = Field(default=None, ge=1, description="来源行 ID")
    source_year: int = Field(..., ge=1990, le=2100)
    source_question_number: int = Field(
        ..., ge=1, le=MAX_SOURCE_QUESTION_NUMBER
    )
    exam_question_id: int | None = Field(default=None, ge=1, description="命中的真题 ID")
    source_exists: bool = Field(default=False, description="真题库中是否存在该题")
    exam_title: str | None = Field(default=None, description="命中的真题标题")

    model_config = ConfigDict(from_attributes=True)


class AdaptationResponse(BaseModel):
    """改编题响应。"""

    id: int = Field(..., ge=1)
    title: str | None = Field(default=None)
    question_type: QuestionTypeEnum
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
    sources: list[AdaptationSourceRefResponse] = Field(
        default_factory=list,
        description="来源引用列表",
    )
    source_summary: str = Field(default="", description="来源展示摘要")

    model_config = ConfigDict(from_attributes=True)


class AdaptationCreateRequest(QuestionCreateFields):
    """改编题创建请求。"""

    sources: list[AdaptationSourceRefInput] = Field(
        default_factory=list,
        max_length=MAX_SOURCE_REFS,
        description="来源引用列表，允许暂未标注",
    )


class AdaptationUpdateRequest(QuestionUpdateFields):
    """改编题更新请求。"""

    sources: list[AdaptationSourceRefInput] | None = Field(
        default=None,
        max_length=MAX_SOURCE_REFS,
        description="来源引用列表，缺省表示不修改，空数组表示清空",
    )


class AdaptationSourceUsageCheckResponse(BaseModel):
    """改编题来源占用检查响应。"""

    reused_sources: list[AdaptationSourceUsageItem] = Field(
        default_factory=list,
        description="已被其他改编题引用的来源",
    )

    model_config = ConfigDict(from_attributes=True)


class PaginatedAdaptationResponse(PaginatedResponse[AdaptationResponse]):
    """改编题分页响应。"""
