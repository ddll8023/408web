"""
分类管理模块请求与响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator


class ExamCategoryCreateRequest(BaseModel):
    """分类创建请求"""
    subject_id: int = Field(
        ...,
        description="所属科目ID",
        examples=[1]
    )
    parent_id: Optional[int] = Field(
        default=None,
        description="父分类ID（NULL表示顶级分类）",
        examples=[None]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="分类名称",
        examples=["栈和队列"]
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="分类编码",
        examples=["stack-queue"]
    )
    description: Optional[str] = Field(
        default=None,
        description="分类描述",
        examples=["栈和队列相关题目"]
    )
    order_num: int = Field(
        ...,
        ge=0,
        description="排序序号（升序）",
        examples=[1]
    )
    enabled: bool = Field(
        default=True,
        description="是否启用",
        examples=[True]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "subject_id": 1,
                    "parent_id": None,
                    "name": "栈和队列",
                    "code": "stack-queue",
                    "description": "栈和队列相关题目",
                    "order_num": 1,
                    "enabled": True
                }
            ]
        }
    }


class ExamCategoryUpdateRequest(BaseModel):
    """分类更新请求"""
    subject_id: Optional[int] = Field(
        default=None,
        description="所属科目ID"
    )
    parent_id: Optional[int] = Field(
        default=None,
        description="父分类ID"
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="分类名称"
    )
    code: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="分类编码"
    )
    description: Optional[str] = Field(
        default=None,
        description="分类描述"
    )
    order_num: Optional[int] = Field(
        default=None,
        ge=0,
        description="排序序号"
    )
    enabled: Optional[bool] = Field(
        default=None,
        description="是否启用"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "栈和队列（修订版）",
                    "order_num": 2,
                    "enabled": True
                }
            ]
        }
    }


class ExamCategoryResponse(BaseModel):
    """分类响应（单个节点）"""
    id: int = Field(..., description="分类ID", examples=[1])
    subject_id: int = Field(..., description="所属科目ID", examples=[1])
    subject_name: Optional[str] = Field(default=None, description="科目名称")
    parent_id: Optional[int] = Field(default=None, description="父分类ID")
    parent_name: Optional[str] = Field(default=None, description="父分类名称")
    name: str = Field(..., description="分类名称", examples=["栈和队列"])
    code: str = Field(..., description="分类编码", examples=["stack-queue"])
    description: Optional[str] = Field(default=None, description="分类描述")
    order_num: int = Field(..., description="排序序号", examples=[1])
    enabled: bool = Field(..., description="是否启用", examples=[True])
    question_count: Optional[int] = Field(
        default=None,
        description="题目数量（统计）",
        examples=[10]
    )
    # 驼峰命名别名，供前端使用
    questionCount: Optional[int] = Field(
        default=None,
        description="题目数量（驼峰命名）",
        examples=[10]
    )
    create_time: Optional[str] = Field(default=None, description="创建时间")
    update_time: Optional[str] = Field(default=None, description="更新时间")

    model_config = {
        "from_attributes": True
    }


class ExamCategoryTreeResponse(BaseModel):
    """分类树形响应（带子分类列表和题目统计）"""
    id: int = Field(..., description="分类ID", examples=[1])
    subject_id: int = Field(..., description="所属科目ID", examples=[1])
    subject_name: Optional[str] = Field(default=None, description="科目名称")
    parent_id: Optional[int] = Field(default=None, description="父分类ID")
    parent_name: Optional[str] = Field(default=None, description="父分类名称")
    name: str = Field(..., description="分类名称", examples=["栈和队列"])
    code: str = Field(..., description="分类编码", examples=["stack-queue"])
    description: Optional[str] = Field(default=None, description="分类描述")
    order_num: int = Field(..., description="排序序号", examples=[1])
    enabled: bool = Field(..., description="是否启用", examples=[True])
    question_count: Optional[int] = Field(
        default=None,
        description="题目数量（统计）",
        examples=[10]
    )
    # 驼峰命名别名，供前端使用
    questionCount: Optional[int] = Field(
        default=None,
        description="题目数量（驼峰命名）",
        examples=[10]
    )
    children: List["ExamCategoryTreeResponse"] = Field(
        default_factory=list,
        description="子分类列表"
    )

    model_config = {
        "from_attributes": True
    }

    @model_validator(mode='before')
    @classmethod
    def copy_question_count(cls, data):
        """自动从 question_count 复制到 questionCount"""
        if isinstance(data, dict):
            # 如果 questionCount 为空且 question_count 有值，则复制
            if data.get('questionCount') is None and 'question_count' in data:
                data['questionCount'] = data['question_count']
        return data


class SubjectStatItem(BaseModel):
    """按科目的统计数据项"""
    subject_id: int = Field(..., description="科目ID")
    subject_name: str = Field(..., description="科目名称")
    category_count: int = Field(..., description="分类数量")
    enabled_category_count: int = Field(..., description="启用分类数量")
    question_count: int = Field(..., description="去重后的题目数量")


class ExamCategoryStatResponse(BaseModel):
    """分类统计响应"""
    subject_stats: List[SubjectStatItem] = Field(
        ...,
        description="按科目的统计数据"
    )
    total_question_count: int = Field(
        ...,
        description="去重后的题目总数"
    )
    total_categories: int = Field(
        ...,
        description="分类总数",
        examples=[100]
    )
    enabled_categories: int = Field(
        ...,
        description="启用分类数",
        examples=[80]
    )
    question_type: str = Field(
        ...,
        description="统计的题目类型",
        examples=["exam"]
    )

    model_config = {
        "from_attributes": True
    }


class ExamCategoryUsageResponse(BaseModel):
    """分类引用检查响应"""
    id: int = Field(..., description="分类ID", examples=[1])
    name: str = Field(..., description="分类名称", examples=["栈和队列"])
    has_children: bool = Field(
        ...,
        description="是否有子分类",
        examples=[False]
    )
    question_count: int = Field(
        ...,
        description="被真题引用的次数",
        examples=[5]
    )
    mock_count: int = Field(
        ...,
        description="被模拟题引用的次数",
        examples=[3]
    )
    can_delete: bool = Field(
        ...,
        description="是否可以删除",
        examples=[True]
    )

    model_config = {
        "from_attributes": True
    }


# 更新正向引用
ExamCategoryTreeResponse.model_rebuild()
