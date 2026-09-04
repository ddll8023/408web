"""真题和模拟题共用的题目字段及结构校验。"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import DifficultyEnum, QuestionTypeEnum


class QuestionOptions(BaseModel):
    """选择题 A-D 选项。"""

    model_config = ConfigDict(extra="forbid")

    A: str = Field(..., min_length=1, description="选项 A")
    B: str = Field(..., min_length=1, description="选项 B")
    C: str = Field(..., min_length=1, description="选项 C")
    D: str = Field(..., min_length=1, description="选项 D")


class QuestionCreateFields(BaseModel):
    """题目创建时的共用字段。"""

    question_type: QuestionTypeEnum = Field(
        default=QuestionTypeEnum.ESSAY,
        description="题型",
    )
    title: Optional[str] = Field(default=None, max_length=200, description="题目标题")
    content: str = Field(..., min_length=1, description="Markdown 格式题目内容")
    options: Optional[QuestionOptions] = Field(default=None, description="选择题选项")
    answer: Optional[str] = Field(default=None, description="答案解析")
    category: Optional[list[str]] = Field(default=None, description="分类名称列表")
    subject_id: Optional[int] = Field(default=None, ge=1, description="科目 ID")
    difficulty: Optional[DifficultyEnum] = Field(default=None, description="难度")

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("题目内容不能为空")
        return value

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        normalized = [item.strip() for item in value]
        if any(not item for item in normalized):
            raise ValueError("分类名称不能为空")
        return normalized

    @model_validator(mode="after")
    def validate_structure(self) -> "QuestionCreateFields":
        validate_question_payload(self.question_type, self.content, self.options)
        return self


class QuestionUpdateFields(BaseModel):
    """题目更新时的共用字段。"""

    question_type: Optional[QuestionTypeEnum] = Field(default=None, description="题型")
    title: Optional[str] = Field(default=None, max_length=200, description="题目标题")
    content: Optional[str] = Field(default=None, min_length=1, description="Markdown 格式题目内容")
    options: Optional[QuestionOptions] = Field(default=None, description="选择题选项")
    answer: Optional[str] = Field(default=None, description="答案解析")
    category: Optional[list[str]] = Field(default=None, description="分类名称列表")
    subject_id: Optional[int] = Field(default=None, ge=1, description="科目 ID")
    difficulty: Optional[DifficultyEnum] = Field(default=None, description="难度")

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("题目内容不能为空")
        return value

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None
        normalized = [item.strip() for item in value]
        if any(not item for item in normalized):
            raise ValueError("分类名称不能为空")
        return normalized


def validate_question_payload(
    question_type: QuestionTypeEnum | str,
    content: Optional[str],
    options: Optional[QuestionOptions],
) -> None:
    """校验题型、题干和选项之间的纯数据约束。"""
    type_value = question_type.value if isinstance(question_type, QuestionTypeEnum) else question_type

    if not content or not content.strip():
        raise ValueError("题目内容不能为空")
    if type_value == QuestionTypeEnum.CHOICE.value and options is None:
        raise ValueError("选择题必须提供 A-D 四个选项")
    if type_value == QuestionTypeEnum.ESSAY.value and options is not None:
        raise ValueError("主观题不能包含选择题选项")
    if type_value not in {item.value for item in QuestionTypeEnum}:
        raise ValueError("题型必须为 CHOICE 或 ESSAY")
