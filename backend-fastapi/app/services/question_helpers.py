"""真题和模拟题共用的数据转换及业务校验。"""
import json
from json import JSONDecodeError
from typing import Optional

from pydantic import ValidationError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exception import NotFoundException, ValidationException
from app.models.entities import ExamCategory, Subject
from app.models.enums import QuestionTypeEnum
from app.schemas.question import QuestionOptions, validate_question_payload


def serialize_options(options: Optional[QuestionOptions]) -> Optional[str]:
    """将选择题选项序列化为数据库 JSON 文本。"""
    if options is None:
        return None
    return json.dumps(options.model_dump(), ensure_ascii=False)


def serialize_categories(categories: Optional[list[str]]) -> Optional[str]:
    """将分类名称列表序列化为数据库 JSON 文本。"""
    if not categories:
        return None
    return json.dumps(categories, ensure_ascii=False)


def parse_options(value: Optional[str]) -> Optional[QuestionOptions]:
    """将数据库中的选项 JSON 转换为响应模型。"""
    if not value:
        return None
    try:
        return QuestionOptions.model_validate(json.loads(value))
    except (JSONDecodeError, TypeError, ValidationError):
        return None


def parse_categories(value: Optional[str]) -> Optional[list[str]]:
    """将数据库中的分类 JSON 转换为列表。"""
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except (JSONDecodeError, TypeError):
        return None
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        return None
    return parsed


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


async def validate_question_scope(
    session: AsyncSession,
    subject_id: Optional[int],
    categories: Optional[list[str]],
    *,
    existing_subject_id: Optional[int] = None,
    existing_categories: Optional[list[str]] = None,
) -> None:
    """校验科目存在性及分类归属，允许原有历史分类原样保留。"""
    if subject_id is not None:
        subject_result = await session.exec(select(Subject.id).where(Subject.id == subject_id))
        if subject_result.first() is None:
            raise NotFoundException("科目")

    if not categories:
        return
    if subject_id is None:
        raise ValidationException("选择分类时必须指定科目")

    category_result = await session.exec(
        select(ExamCategory.name).where(ExamCategory.subject_id == subject_id)
    )
    valid_names = set(category_result.all())
    invalid_names = [name for name in categories if name not in valid_names]

    # 历史记录可能引用已删除分类；编辑未改变分类时保留原值。
    legacy_unchanged = (
        existing_subject_id == subject_id and existing_categories == categories
    )
    if invalid_names and not legacy_unchanged:
        raise ValidationException(
            f"分类不属于指定科目或不存在: {', '.join(invalid_names)}"
        )
