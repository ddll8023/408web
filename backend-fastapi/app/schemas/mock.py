"""
模拟题管理模块请求与响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class MockQueryParams(BaseModel):
    """模拟题分页查询参数"""
    page: int = Field(default=1, ge=1, description="页码", examples=[1])
    page_size: int = Field(default=10, ge=1, le=100, description="每页大小", examples=[10])
    source: Optional[str] = Field(default=None, description="来源机构筛选", examples=["王道"])
    category: Optional[str] = Field(default=None, description="分类筛选（JSON数组包含）", examples=["栈"])
    subject_id: Optional[int] = Field(default=None, description="科目ID筛选", examples=[1])
    no_category: Optional[bool] = Field(default=None, description="是否筛选无分类的题目", examples=[False])
    keyword: Optional[str] = Field(default=None, description="关键词搜索（匹配title或content）", examples=["链表"])
    sort_field: str = Field(default="update_time", description="排序字段：source/update_time/question_number")
    sort_order: str = Field(default="desc", description="排序方向：asc/desc")

    model_config = {
        "json_schema_extra": {
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
                    "sort_order": "desc"
                }
            ]
        }
    }

    @field_validator("sort_field")
    @classmethod
    def validate_sort_field(cls, v: str) -> str:
        allowed_fields = {"source", "update_time", "question_number", "create_time"}
        if v not in allowed_fields:
            raise ValueError(f"排序字段必须为以下之一: {', '.join(allowed_fields)}")
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        if v not in {"asc", "desc"}:
            raise ValueError("排序方向必须为 asc 或 desc")
        return v


class MockCreateRequest(BaseModel):
    """模拟题创建请求"""
    source: str = Field(..., min_length=1, max_length=100, description="来源机构名称", examples=["王道"])
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
                    "source": "王道",
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


class MockUpdateRequest(BaseModel):
    """模拟题更新请求"""
    source: Optional[str] = Field(default=None, min_length=1, max_length=100, description="来源机构名称")
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
                    "source": "天勤",
                    "question_number": 2,
                    "title": "栈的操作（修订版）"
                }
            ]
        }
    }


class MockResponse(BaseModel):
    """模拟题响应"""
    id: int = Field(..., description="主键ID", examples=[1])
    source: str = Field(..., description="来源机构", examples=["王道"])
    question_number: Optional[int] = Field(default=None, description="题号", examples=[1])
    question_type: str = Field(..., description="题型", examples=["ESSAY"])
    title: Optional[str] = Field(default=None, description="题目标题", examples=["栈的操作"])
    content: str = Field(..., description="题目内容", examples=["请实现一个栈..."])
    options: Optional[str] = Field(default=None, description="选择题选项")
    answer: Optional[str] = Field(default=None, description="答案")
    category: Optional[str] = Field(default=None, description="分类（JSON数组）")
    subject_id: Optional[int] = Field(default=None, description="科目ID")
    subject_name: Optional[str] = Field(default=None, description="科目名称")
    difficulty: Optional[str] = Field(default=None, description="难度")
    author_id: int = Field(..., description="作者ID")
    author_name: Optional[str] = Field(default=None, description="作者名称")
    create_time: Optional[str] = Field(default=None, description="创建时间")
    update_time: Optional[str] = Field(default=None, description="更新时间")

    model_config = {
        "from_attributes": True
    }


class MockSourceStatResponse(BaseModel):
    """模拟题来源统计响应"""
    source: str = Field(..., description="来源机构", examples=["王道"])
    count: int = Field(..., description="题目数量", examples=[50])

    model_config = {
        "from_attributes": True
    }


class MockSourceItem(BaseModel):
    """模拟题来源列表项"""
    source: str = Field(..., description="来源机构", examples=["王道"])
    question_count: int = Field(..., description="题目数量", examples=[50])

    model_config = {
        "from_attributes": True
    }


class MockSourcesResponse(BaseModel):
    """模拟题来源列表响应"""
    sources: List[MockSourceItem] = Field(default_factory=list, description="来源列表")

    model_config = {
        "from_attributes": True
    }


class MockCategoryStatItem(BaseModel):
    """模拟题分类统计项"""
    category: str = Field(..., description="分类名称", examples=["栈"])
    count: int = Field(..., description="题目数量", examples=[10])

    model_config = {
        "from_attributes": True
    }


class MockCategoryStatsResponse(BaseModel):
    """模拟题分类统计响应"""
    subject_id: int = Field(..., description="科目ID")
    subject_name: Optional[str] = Field(default=None, description="科目名称")
    stats: List[MockCategoryStatItem] = Field(default_factory=list, description="分类统计列表")
    total_count: int = Field(default=0, description="该科目下的题目总数（去重后）")

    model_config = {
        "from_attributes": True
    }


class MockDuplicateCheckResponse(BaseModel):
    """模拟题查重响应"""
    is_duplicate: bool = Field(..., description="是否重复", examples=[False])
    existing_question: Optional[MockResponse] = Field(default=None, description="已存在的题目")

    model_config = {
        "from_attributes": True
    }


class PaginatedMockResponse(BaseModel):
    """模拟题分页响应"""
    data: List[MockResponse] = Field(default_factory=list, description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")

    model_config = {
        "from_attributes": True
    }
