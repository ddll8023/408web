"""真题和模拟题共用的业务校验。"""
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.enums import QuestionTypeEnum
from app.repositories.question_scope_repository import QuestionScopeRepository
from app.schemas.question import QuestionOptions, validate_question_payload


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
    repository = QuestionScopeRepository(session)
    if subject_id is not None:
        if not await repository.subject_exists(subject_id):
            raise NotFoundException("科目")

    if not categories:
        return
    if subject_id is None:
        raise ValidationException("选择分类时必须指定科目")

    valid_names = await repository.category_names(subject_id)
    invalid_names = [name for name in categories if name not in valid_names]

    legacy_unchanged = (
        existing_subject_id == subject_id and existing_categories == categories
    )
    if invalid_names and not legacy_unchanged:
        raise ValidationException(
            f"分类不属于指定科目或不存在: {', '.join(invalid_names)}"
        )
