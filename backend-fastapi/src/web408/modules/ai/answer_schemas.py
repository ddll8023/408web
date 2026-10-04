"""答案生成契约：只接受已有题目或管理员编辑草稿，不接受模型指令，也不回写题库。"""
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from web408.modules.ai.session_schemas import AiSessionCreateRequest, AiSessionView
from web408.modules.question_content.schemas import QuestionOptions


class AiAnswerDraft(BaseModel):
    """生成所需的题面草稿；原答案不进入模型上下文。"""

    model_config = ConfigDict(extra="forbid")
    question_type: Literal["CHOICE", "ESSAY"]
    subject_id: int | None = Field(default=None, ge=1, strict=True)
    content: str = Field(min_length=1, max_length=65536)
    options: QuestionOptions | None = None

    @model_validator(mode="after")
    def validate_question(self) -> Self:
        """拒绝不完整题面、题型与选项冲突及无效 Unicode。"""
        if not self.content.strip():
            raise ValueError("题干不能为空白")
        if (self.question_type == "CHOICE") != (self.options is not None):
            raise ValueError("选择题必须提供选项，主观题不能提供选项")
        texts = [self.content]
        if self.options is not None:
            texts.extend(self.options.model_dump().values())
        if any(not text.strip() or len(text) > 65536 for text in texts):
            raise ValueError("题干或选项为空或超过长度上限")
        if any(0xD800 <= ord(char) <= 0xDFFF for text in texts for char in text):
            raise ValueError("题面包含无效 Unicode 字符")
        return self


class AiAnswerSource(AiAnswerDraft):
    """浏览器对比基线；answer 仅供用户对比，不发送给模型。"""

    answer: str | None = None


class AiAnswerSessionCreateRequest(AiSessionCreateRequest):
    """无草稿时读取最新已保存题面；有草稿时仍核实题目存在。"""

    draft: AiAnswerDraft | None = None


class AiAnswerSessionView(AiSessionView):
    """携带实际生成来源，防止阅读页旧列表成为错误的对比基线。"""

    answer_source: AiAnswerSource
