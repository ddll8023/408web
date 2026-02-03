"""
真题管理模块请求与响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ExamQueryParams(BaseModel):
    """真题分页查询参数"""
    page: int = Field(default=1, ge=1, description="页码", examples=[1])
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小", examples=[10])
    year: Optional[int] = Field(default=None, description="年份筛选", examples=[2023])
    category: Optional[str] = Field(default=None, description="分类筛选（JSON数组包含）", examples=["栈"])
    subject_id: Optional[int] = Field(default=None, description="科目ID筛选", examples=[1])
    no_category: Optional[bool] = Field(default=None, description="是否筛选无分类的题目", examples=[False])
    keyword: Optional[str] = Field(default=None, description="关键词搜索（匹配title或content）", examples=["链表"])
    sort_field: str = Field(default="update_time", description="排序字段：year/update_time/question_number", examples=["update_time"])
    sort_order: str = Field(default="desc", description="排序方向：asc/desc", examples=["desc"])

    model_config = {
        "json_schema_extra": {
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
                    "sort_order": "desc"
                }
            ]
        }
    }

    @field_validator("sort_field")
    @classmethod
    def validate_sort_field(cls, v: str) -> str:
        allowed_fields = {"year", "update_time", "question_number"}
        if v not in allowed_fields:
            raise ValueError(f"排序字段必须为以下之一: {', '.join(allowed_fields)}")
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        if v not in {"asc", "desc"}:
            raise ValueError("排序方向必须为 asc 或 desc")
        return v


class ExamCreateRequest(BaseModel):
    """真题创建请求"""
    year: int = Field(..., ge=1990, le=2100, description="年份", examples=[2023])
    question_number: Optional[int] = Field(default=None, ge=1, le=1000, description="题号", examples=[1])
    question_type: str = Field(default="ESSAY", description="题型：CHOICE=选择题，ESSAY=主观题", examples=["ESSAY"])
    title: Optional[str] = Field(default=None, max_length=200, description="题目标题", examples=["栈的操作"])
    content: str = Field(..., description="Markdown格式题目内容", examples=["请实现一个栈..."])
    options: Optional[str] = Field(default=None, description="选择题选项（JSON格式，如{\"A\":\"选项A\",\"B\":\"选项B\"}）")
    answer: Optional[str] = Field(default=None, description="答案")
    category: Optional[str] = Field(default=None, description="分类（JSON数组，如[\"数据结构\",\"栈\"]）")
    subject_id: Optional[int] = Field(default=None, description="科目ID", examples=[1])
    difficulty: Optional[str] = Field(default=None, description="难度：EASY/MEDIUM/HARD", examples=["MEDIUM"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "year": 2023,
                    "question_number": 1,
                    "question_type": "ESSAY",
                    "title": "栈的操作",
                    "content": "请实现一个栈，包含push和pop操作...",
                    "answer": "实现代码见解析...",
                    "category": "[\"数据结构\", \"栈\"]",
                    "subject_id": 1,
                    "difficulty": "MEDIUM"
                }
            ]
        }
    }


class ExamUpdateRequest(BaseModel):
    """真题更新请求"""
    year: Optional[int] = Field(default=None, ge=1990, le=2100, description="年份")
    question_number: Optional[int] = Field(default=None, ge=1, le=1000, description="题号")
    question_type: Optional[str] = Field(default=None, description="题型：CHOICE=选择题，ESSAY=主观题")
    title: Optional[str] = Field(default=None, max_length=200, description="题目标题")
    content: Optional[str] = Field(default=None, description="Markdown格式题目内容")
    options: Optional[str] = Field(default=None, description="选择题选项（JSON格式）")
    answer: Optional[str] = Field(default=None, description="答案")
    category: Optional[str] = Field(default=None, description="分类（JSON数组）")
    subject_id: Optional[int] = Field(default=None, description="科目ID")
    difficulty: Optional[str] = Field(default=None, description="难度：EASY/MEDIUM/HARD")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "year": 2023,
                    "question_number": 2,
                    "title": "栈的操作（修订版）"
                }
            ]
        }
    }


class ExamResponse(BaseModel):
    """真题响应"""
    id: int = Field(..., description="主键ID", examples=[1])
    year: int = Field(..., description="年份", examples=[2023])
    question_number: Optional[int] = Field(
        default=None,
        alias="questionNumber",
        description="题号", examples=[1]
    )
    question_type: str = Field(
        ...,
        alias="questionType",
        description="题型", examples=["ESSAY"]
    )
    title: Optional[str] = Field(default=None, description="题目标题", examples=["栈的操作"])
    content: str = Field(..., description="题目内容", examples=["请实现一个栈..."])
    options: Optional[str] = Field(default=None, description="选择题选项", examples=[{"A": "选项A"}])
    answer: Optional[str] = Field(default=None, description="答案", examples=["实现代码..."])
    category: Optional[List[str]] = Field(default=None, description="分类列表", examples=[["数据结构", "栈"]])
    subject_id: Optional[int] = Field(
        default=None,
        alias="subjectId",
        description="科目ID", examples=[1]
    )
    subject_name: Optional[str] = Field(
        default=None,
        alias="subjectName",
        description="科目名称", examples=["数据结构"]
    )
    difficulty: Optional[str] = Field(default=None, description="难度", examples=["MEDIUM"])
    author_id: int = Field(
        ...,
        alias="authorId",
        description="作者ID", examples=[1]
    )
    author_name: Optional[str] = Field(
        default=None,
        alias="authorName",
        description="作者名称", examples=["admin"]
    )
    create_time: Optional[str] = Field(
        default=None,
        alias="createTime",
        description="创建时间", examples=["2024-01-01T10:00:00"]
    )
    update_time: Optional[str] = Field(
        default=None,
        alias="updateTime",
        description="更新时间", examples=["2024-01-02T10:00:00"]
    )

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }


class ExamYearStatResponse(BaseModel):
    """真题年份统计响应"""
    year: int = Field(..., description="年份", examples=[2023])
    count: int = Field(..., description="题目数量", examples=[15])
    choice_count: int = Field(default=0, description="选择题数量", examples=[5])
    subjective_count: int = Field(default=0, description="主观题数量", examples=[10])

    model_config = {
        "from_attributes": True
    }


class ExamCategoryStatItem(BaseModel):
    """真题分类统计项"""
    category: str = Field(..., description="分类名称", examples=["栈"])
    count: int = Field(..., description="题目数量", examples=[10])
    choice_count: int = Field(default=0, description="选择题数量")
    subjective_count: int = Field(default=0, description="主观题数量")

    model_config = {
        "from_attributes": True
    }


class ExamCategoryStatsResponse(BaseModel):
    """真题分类统计响应"""
    subject_id: Optional[int] = Field(default=None, description="科目ID", examples=[1])
    subject_name: Optional[str] = Field(default=None, description="科目名称", examples=["数据结构"])
    stats: List[ExamCategoryStatItem] = Field(default_factory=list, description="分类统计列表")

    model_config = {
        "from_attributes": True
    }


class ExamDuplicateCheckResponse(BaseModel):
    """真题查重响应"""
    is_duplicate: bool = Field(..., description="是否重复", examples=[False])
    existing_question: Optional[ExamResponse] = Field(default=None, description="已存在的题目")

    model_config = {
        "from_attributes": True
    }


class ExamIndexItem(BaseModel):
    """真题索引项（年份-题号组合）"""
    year: int = Field(..., description="年份")
    question_number: Optional[int] = Field(default=None, description="题号")
    id: int = Field(..., description="题目ID")

    model_config = {
        "from_attributes": True
    }


class ExamIndexResponse(BaseModel):
    """真题索引数据响应"""
    subject_id: Optional[int] = Field(default=None, description="科目ID")
    subject_name: Optional[str] = Field(default=None, description="科目名称")
    index_data: List[ExamIndexItem] = Field(default_factory=list, description="索引数据列表")

    model_config = {
        "from_attributes": True
    }


class PaginatedExamResponse(BaseModel):
    """真题分页响应"""
    data: List[ExamResponse] = Field(default_factory=list, description="数据列表")
    total: int = Field(..., description="总记录数", examples=[100])
    page: int = Field(..., description="当前页码", examples=[1])
    page_size: int = Field(..., description="每页大小", examples=[10])

    model_config = {
        "from_attributes": True
    }


class ExportResultResponse(BaseModel):
    """真题导出响应"""
    filename: str = Field(..., description="文件名")
    content_type: str = Field(..., description="内容类型")
    file_bytes: bytes = Field(..., description="文件字节流")
