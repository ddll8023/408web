"""题目内容的纯业务校验。"""
from typing import Optional

from web408.core.exceptions import ValidationException
from web408.models.enums import QuestionTypeEnum
from web408.modules.question_content.schemas import QuestionOptions, validate_question_payload


def validate_question_values(
    question_type: QuestionTypeEnum | str,
    content: Optional[str],
    options: Optional[QuestionOptions],
) -> None:
    """将纯数据校验错误转换为项目业务异常。"""
    try:
        validate_question_payload(question_type, content, options)
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc
