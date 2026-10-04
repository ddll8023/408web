"""题目咨询的公开契约，凭据只允许进入业务层的进程内调用。"""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from web408.modules.ai.schemas import AiInputMode, AiModelView


# 三类题目共用同一套咨询会话，题目归属由后端按认证账号重新读取。
QuestionKind = Literal["exam", "mock", "adaptation"]
# 图片未附带的固定原因码，与 question_images 的 OMIT_TEXTS 一一对应。
ImageOmissionReason = Literal["external", "inline", "missing", "oversize", "budget", "svg_budget"]
# 单轮提问上限；题目资料不受此限制。
MAX_MESSAGE_CHARS = 2000


class AiSessionCreateRequest(BaseModel):
    """浏览器只指定题目，不提交题面、账号或系统提示词。"""

    model_config = ConfigDict(extra="forbid")
    question_kind: QuestionKind
    question_id: int = Field(ge=1, strict=True)


class AiMessageRequest(BaseModel):
    """一个明确发送意图使用一个 UUID；提问只接受主动发送的纯文本，题目图片随创建时的会话固定上下文发送。"""

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


class AiQuestionImageRef(BaseModel):
    """题目文本中的一处图片引用；只带图号、受控文件名与媒体类型，不含路径与原始地址。"""

    model_config = ConfigDict(extra="forbid", frozen=True)
    index: int = Field(ge=1, le=65536)
    filename: str = Field(min_length=1, max_length=255)
    media_type: str = Field(min_length=1, max_length=100)


class AiQuestionImage(BaseModel):
    """已读取到内存的题目图片数据，只在业务层与运行模块之间传递，不下发浏览器。"""

    model_config = ConfigDict(extra="forbid", frozen=True)
    index: int = Field(ge=1, le=65536)
    media_type: str = Field(min_length=1, max_length=100)
    data: bytes = Field(min_length=1, max_length=20971520)


class AiOmittedQuestionImage(BaseModel):
    """一张未附带的题目图片及其固定原因码，用于向模型与用户说明缺口。"""

    model_config = ConfigDict(extra="forbid", frozen=True)
    index: int = Field(ge=1, le=65536)
    reason: ImageOmissionReason


class AiQuestionSnapshot(BaseModel):
    """只有可信题目文本、可发送的本地图片引用与未附带登记，不含作者、路径或原始地址。"""

    model_config = ConfigDict(extra="forbid", frozen=True)
    question_kind: QuestionKind
    question_id: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=65536)
    images: tuple[AiQuestionImageRef, ...] = ()
    omitted: tuple[AiOmittedQuestionImage, ...] = ()


class AiSessionView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID
    question_kind: QuestionKind
    question_id: int = Field(ge=1)
    model: AiModelView
    input_mode: AiInputMode
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
    input_mode: AiInputMode


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
