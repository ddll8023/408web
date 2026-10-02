"""文本咨询的公开契约，凭据只允许进入业务层的进程内调用。"""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from web408.modules.ai.schemas import AiModelView


QuestionKind = Literal["exam", "mock", "adaptation"]
MAX_MESSAGE_CHARS = 2000


class AiSessionCreateRequest(BaseModel):
    """浏览器只指定题目，不提交题面、账号或系统提示词。"""

    model_config = ConfigDict(extra="forbid")
    question_kind: QuestionKind
    question_id: int = Field(ge=1, strict=True)


class AiMessageRequest(BaseModel):
    """一个明确发送意图使用一个 UUID；本阶段只接受主动选择的纯文本。"""

    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    input_mode: Literal["text"]
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)

    @model_validator(mode="after")
    def validate_message(self) -> "AiMessageRequest":
        """拒绝纯空白和无效 Unicode，保留正常多行提问原文。"""
        if not self.message.strip():
            raise ValueError("提问不能为空白")
        if any(0xD800 <= ord(char) <= 0xDFFF for char in self.message):
            raise ValueError("提问包含无效 Unicode 字符")
        return self


class AiAbortRequest(BaseModel):
    """停止一个发送意图，不隐式停止别的请求。"""

    model_config = ConfigDict(extra="forbid")
    request_id: UUID


class AiCloseRequest(BaseModel):
    """显式关闭只使用路径中的会话标识。"""

    model_config = ConfigDict(extra="forbid")


class AiQuestionSnapshot(BaseModel):
    """只有可信题目文本和未提供图片数量，不包含作者、路径或图片原文。"""

    model_config = ConfigDict(extra="forbid", frozen=True)
    question_kind: QuestionKind
    question_id: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=65536)
    omitted_images: int = Field(ge=0, le=65536)


class AiSessionView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID
    question_kind: QuestionKind
    question_id: int = Field(ge=1)
    model: AiModelView
    input_mode: Literal["text"]
    context_note: str = Field(max_length=300)


class AiSessionActionView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stopped: bool
    closed: bool


class AiMetaEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID
    request_id: UUID
    model: AiModelView
    input_mode: Literal["text"]


class AiDeltaEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    text: str = Field(max_length=65536)


class AiStreamError(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Literal[409, 422, 429, 502, 503]
    message: str = Field(min_length=1, max_length=300)


class AiDoneEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    status: Literal["completed", "cancelled", "failed"]
    answer: str | None = Field(default=None, max_length=65536)
    error: AiStreamError | None = None

    @model_validator(mode="after")
    def validate_terminal(self) -> "AiDoneEvent":
        """成功必须提供完整回答；取消和失败不得携带可被误认成成功的回答。"""
        if self.status == "completed":
            if self.answer is None or not self.answer.strip() or self.error is not None:
                raise ValueError("成功终态必须包含完整回答且没有错误")
        elif self.answer is not None:
            raise ValueError("未完成终态不允许提供成功回答")
        return self
